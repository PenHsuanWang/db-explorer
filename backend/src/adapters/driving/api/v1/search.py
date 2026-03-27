from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.data_service import DataService
from src.core.domain.models import SearchRequest, SearchResult
from src.dependencies import get_current_user, get_data_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
async def search(
    request: SearchRequest,
    service: Annotated[DataService, Depends(get_data_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[SearchResult]:
    try:
        return service.search(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
