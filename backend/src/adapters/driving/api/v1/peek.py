from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.data_service import DataService
from src.core.domain.models import PeekRequest
from src.core.domain.types import UniversalCell, UniversalRow
from src.dependencies import get_current_user, get_data_service

router = APIRouter(prefix="/peek", tags=["peek"])


def _serialize_rows(rows: list[UniversalRow]) -> dict[str, Any]:
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
async def peek(
    request: PeekRequest,
    service: Annotated[DataService, Depends(get_data_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        rows = service.peek(request)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _serialize_rows(rows)
