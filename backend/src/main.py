from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.driving.api.v1.router import router as v1_router
from src.config import get_settings
from src.core.domain.models import ConnectionConfig
from src.dependencies import get_data_service

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Register the built-in mock connector and index its metadata on startup."""
    service = get_data_service()
    mock_config = ConnectionConfig(
        id="mock-default",
        name="Demo Mock DB",
        db_type="mock",
    )
    try:
        service.add_connection(mock_config)
        logger.info("Mock connector registered and indexed.")
    except Exception:
        logger.exception("Failed to register mock connector at startup.")
    yield


app = FastAPI(
    title="DB Explorer API",
    version="0.1.0",
    description="Read-only database exploration and cleaning backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
