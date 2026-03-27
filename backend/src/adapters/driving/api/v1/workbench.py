from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.data_service import DataService
from src.application.workbench_service import WorkbenchService
from src.core.domain.models import SavedWorkbenchCreate, SavedWorkbenchResponse, WorkbenchRequest
from src.core.domain.types import UniversalCell, UniversalRow
from src.dependencies import get_current_user, get_data_service, get_workbench_service
from src.infrastructure.database import get_db_session

router = APIRouter(prefix="/workbench", tags=["workbench"])


def _serialize_pane(rows: list[UniversalRow]) -> dict[str, Any]:
    if not rows:
        return {"columns": [], "rows": []}
    columns = [{"name": cell.column, "type": cell.type.value} for cell in rows[0]]
    serialized = [
        [{"column": c.column, "type": c.type.value, "value": _safe_val(c)} for c in row]
        for row in rows
    ]
    return {"columns": columns, "rows": serialized}


def _safe_val(cell: UniversalCell) -> Any:
    val = cell.value
    if isinstance(val, (bytes, bytearray)):
        return val.hex()
    return val


@router.post("")
async def workbench(
    request: WorkbenchRequest,
    service: Annotated[DataService, Depends(get_data_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        pane_data = service.get_workbench_data(request)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"panes": {pane_id: _serialize_pane(rows) for pane_id, rows in pane_data.items()}}


# ---------------------------------------------------------------------------
# Saved workbench CRUD
# ---------------------------------------------------------------------------


@router.post("/saved", status_code=status.HTTP_201_CREATED, response_model=SavedWorkbenchResponse)
async def save_workbench(
    body: SavedWorkbenchCreate,
    wb_service: Annotated[WorkbenchService, Depends(get_workbench_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    wb_id = await wb_service.save_workbench(
        session, current_user["id"], body.name, body.panes_config, body.cleaning_cfg
    )
    wb = await wb_service.get_workbench(session, current_user["id"], wb_id)
    return wb  # type: ignore[return-value]


@router.get("/saved", response_model=list[SavedWorkbenchResponse])
async def list_saved_workbenches(
    wb_service: Annotated[WorkbenchService, Depends(get_workbench_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    return await wb_service.list_workbenches(session, current_user["id"])


@router.get("/saved/{workbench_id}", response_model=SavedWorkbenchResponse)
async def get_saved_workbench(
    workbench_id: str,
    wb_service: Annotated[WorkbenchService, Depends(get_workbench_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    wb = await wb_service.get_workbench(session, current_user["id"], workbench_id)
    if wb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workbench not found"
        )
    return wb


@router.delete("/saved/{workbench_id}", status_code=status.HTTP_200_OK)
async def delete_saved_workbench(
    workbench_id: str,
    wb_service: Annotated[WorkbenchService, Depends(get_workbench_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        await wb_service.delete_workbench(session, current_user["id"], workbench_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"deleted": workbench_id}
