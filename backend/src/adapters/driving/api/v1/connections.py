from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.data_service import DataService
from src.core.domain.models import ConnectionConfig
from src.dependencies import get_current_user, get_data_service

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_connection(
    config: ConnectionConfig,
    service: Annotated[DataService, Depends(get_data_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    if not config.id:
        config = config.model_copy(update={"id": str(uuid.uuid4())})
    try:
        connection_id = service.add_connection(config, user_id=current_user["id"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"connection_id": connection_id}


@router.get("")
async def list_connections(
    service: Annotated[DataService, Depends(get_data_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[dict]:
    return service.list_connections()


@router.delete("/{connection_id}", status_code=status.HTTP_200_OK)
async def remove_connection(
    connection_id: str,
    service: Annotated[DataService, Depends(get_data_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    try:
        service.remove_connection(connection_id, user_id=current_user["id"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"deleted": connection_id}
