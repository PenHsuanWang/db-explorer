"""Job CRUD endpoints with Celery dispatch and SSE streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from src.application.job_service import JobService
from src.config import get_settings
from src.core.domain.models import JobCreate, JobResponse
from src.dependencies import get_current_user, get_job_service
from src.infrastructure.database import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


def _dispatch_celery_task(job_id: str, user_id: str, body: JobCreate) -> bool:
    """Dispatch a Celery task for the given job. Returns True if dispatched."""
    try:
        from src.infrastructure.tasks import deep_search_job, reindex_metadata_job

        if body.job_type == "deep_search":
            connection_ids = body.payload.get("connection_ids", [])
            query = body.payload.get("query", "")
            deep_search_job.delay(job_id, user_id, query, connection_ids)
            return True
        elif body.job_type == "reindex_metadata":
            connection_id = body.payload.get("connection_id", "")
            reindex_metadata_job.delay(job_id, user_id, connection_id)
            return True
    except Exception:
        logger.warning(
            "Celery dispatch failed for job %s; job remains PENDING",
            job_id,
            exc_info=True,
        )
    return False


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=JobResponse,
    responses={202: {"model": JobResponse}},
)
async def create_job(
    body: JobCreate,
    service: Annotated[JobService, Depends(get_job_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
):
    job_id = await service.create_job(
        session, current_user["id"], body.job_type, body.payload
    )
    job = await service.get_job(session, current_user["id"], job_id)

    dispatched = _dispatch_celery_task(job_id, current_user["id"], body)
    response_status = status.HTTP_202_ACCEPTED if dispatched else status.HTTP_201_CREATED

    from fastapi.responses import JSONResponse

    return JSONResponse(
        content=JobResponse.model_validate(job).model_dump(),  # type: ignore[arg-type]
        status_code=response_status,
    )


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    service: Annotated[JobService, Depends(get_job_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    return await service.list_jobs(session, current_user["id"])


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    service: Annotated[JobService, Depends(get_job_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    job = await service.get_job(session, current_user["id"], job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job


@router.get("/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    service: Annotated[JobService, Depends(get_job_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> EventSourceResponse:
    """SSE endpoint that streams real-time job progress."""
    job = await service.get_job(session, current_user["id"], job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # If job is already terminal, return final event immediately
    if job["status"] in ("SUCCESS", "FAILURE"):
        async def _done_generator():
            yield {
                "event": "complete",
                "data": json.dumps(
                    {"event": "complete", "status": job["status"]}
                ),
            }

        return EventSourceResponse(_done_generator())

    async def event_generator():
        import redis

        settings = get_settings()
        try:
            r = redis.from_url(settings.REDIS_URL)
            pubsub = r.pubsub()
            pubsub.subscribe(f"job_progress:{job_id}")
        except Exception:
            logger.warning(
                "Redis unavailable for SSE stream on job %s", job_id
            )
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": "Real-time streaming unavailable"}
                ),
            }
            return

        try:
            while True:
                message = pubsub.get_message(timeout=0.5)
                if message and message["type"] == "message":
                    raw = message["data"]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    data = json.loads(raw)
                    yield {
                        "event": data.get("event", "progress"),
                        "data": json.dumps(data),
                    }
                    if data.get("event") == "complete":
                        break
                else:
                    await asyncio.sleep(0.1)
        finally:
            pubsub.unsubscribe()
            pubsub.close()
            r.close()

    return EventSourceResponse(event_generator())


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(
    job_id: str,
    service: Annotated[JobService, Depends(get_job_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        await service.delete_job(session, current_user["id"], job_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return {"deleted": job_id}
