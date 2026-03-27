"""Service for persisting jobs in PostgreSQL."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.orm_models import Job


class JobService:
    """CRUD operations for user-scoped jobs."""

    async def create_job(
        self,
        session: AsyncSession,
        user_id: str,
        job_type: str,
        payload: dict | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        job = Job(
            id=uuid.UUID(job_id),
            user_id=uuid.UUID(user_id),
            job_type=job_type,
            status="PENDING",
            payload=payload or {},
        )
        session.add(job)
        await session.flush()
        return job_id

    async def list_jobs(
        self, session: AsyncSession, user_id: str
    ) -> list[dict]:
        stmt = select(Job).where(Job.user_id == uuid.UUID(user_id))
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(row) for row in rows]

    async def get_job(
        self, session: AsyncSession, user_id: str, job_id: str
    ) -> dict | None:
        job = await self._get_by_id(session, user_id, job_id)
        if job is None:
            return None
        return self._to_dict(job)

    async def update_job_status(
        self,
        session: AsyncSession,
        job_id: str,
        status: str,
        progress_meta: dict[str, Any] | None = None,
        result_data: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        stmt = select(Job).where(Job.id == uuid.UUID(job_id))
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.status = status
        if progress_meta is not None:
            job.progress_meta = progress_meta
        if result_data is not None:
            job.result_data = result_data
        if error_message is not None:
            job.error_message = error_message
        await session.flush()

    async def delete_job(
        self, session: AsyncSession, user_id: str, job_id: str
    ) -> None:
        job = await self._get_by_id(session, user_id, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        await session.delete(job)
        await session.flush()

    async def _get_by_id(
        self, session: AsyncSession, user_id: str, job_id: str
    ) -> Job | None:
        stmt = select(Job).where(
            Job.id == uuid.UUID(job_id),
            Job.user_id == uuid.UUID(user_id),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _to_dict(job: Job) -> dict:
        return {
            "id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
            "payload": job.payload,
            "progress_meta": job.progress_meta,
            "result_data": job.result_data,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else "",
            "updated_at": job.updated_at.isoformat() if job.updated_at else "",
        }
