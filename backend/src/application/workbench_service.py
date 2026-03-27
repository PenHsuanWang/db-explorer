"""Service for persisting saved workbenches in PostgreSQL."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.orm_models import SavedWorkbench


class WorkbenchService:
    """CRUD operations for user-scoped saved workbenches."""

    async def save_workbench(
        self,
        session: AsyncSession,
        user_id: str,
        name: str,
        panes_config: dict,
        cleaning_cfg: dict | None = None,
    ) -> str:
        wb_id = str(uuid.uuid4())
        wb = SavedWorkbench(
            id=uuid.UUID(wb_id),
            user_id=uuid.UUID(user_id),
            name=name,
            panes_config=panes_config,
            cleaning_cfg=cleaning_cfg or {},
        )
        session.add(wb)
        await session.flush()
        return wb_id

    async def list_workbenches(
        self, session: AsyncSession, user_id: str
    ) -> list[dict]:
        stmt = select(SavedWorkbench).where(
            SavedWorkbench.user_id == uuid.UUID(user_id)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(row) for row in rows]

    async def get_workbench(
        self, session: AsyncSession, user_id: str, workbench_id: str
    ) -> dict | None:
        wb = await self._get_by_id(session, user_id, workbench_id)
        if wb is None:
            return None
        return self._to_dict(wb)

    async def delete_workbench(
        self, session: AsyncSession, user_id: str, workbench_id: str
    ) -> None:
        wb = await self._get_by_id(session, user_id, workbench_id)
        if wb is None:
            raise ValueError(f"Workbench {workbench_id} not found")
        await session.delete(wb)
        await session.flush()

    async def _get_by_id(
        self, session: AsyncSession, user_id: str, workbench_id: str
    ) -> SavedWorkbench | None:
        stmt = select(SavedWorkbench).where(
            SavedWorkbench.id == uuid.UUID(workbench_id),
            SavedWorkbench.user_id == uuid.UUID(user_id),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _to_dict(wb: SavedWorkbench) -> dict:
        return {
            "id": str(wb.id),
            "name": wb.name,
            "panes_config": wb.panes_config or {},
            "cleaning_cfg": wb.cleaning_cfg or {},
            "created_at": wb.created_at.isoformat() if wb.created_at else "",
            "updated_at": wb.updated_at.isoformat() if wb.updated_at else "",
        }
