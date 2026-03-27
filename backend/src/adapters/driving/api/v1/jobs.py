"""Job CRUD endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.job_service import JobService
from src.core.domain.models import JobCreate, JobResponse
from src.dependencies import get_current_user, get_job_service
from src.infrastructure.database import get_db_session

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=JobResponse)
async def create_job(
    body: JobCreate,
    service: Annotated[JobService, Depends(get_job_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    job_id = await service.create_job(
        session, current_user["id"], body.job_type, body.payload
    )
    job = await service.get_job(session, current_user["id"], job_id)
    return job  # type: ignore[return-value]


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"deleted": job_id}
