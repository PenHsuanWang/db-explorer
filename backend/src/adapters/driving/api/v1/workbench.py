from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.data_service import DataService
from src.core.domain.models import WorkbenchRequest
from src.core.domain.types import UniversalCell, UniversalRow
from src.dependencies import get_current_user, get_data_service

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
