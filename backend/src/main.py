from __future__ import annotations

import json
import logging
import time
import uuid as uuid_mod
from collections import defaultdict
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.adapters.driving.api.v1.router import router as v1_router
from src.config import get_settings
from src.core.domain.models import ConnectionConfig
from src.dependencies import _cache, _factory, get_data_service

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def _configure_logging() -> None:
    settings = get_settings()
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level)


_configure_logging()

logger = logging.getLogger(__name__)

settings = get_settings()


# ---------------------------------------------------------------------------
# Middleware classes
# ---------------------------------------------------------------------------


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique correlation ID to every request/response."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Callable]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid_mod.uuid4()))
        request.state.correlation_id = correlation_id
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory per-IP rate limiter."""

    def __init__(self, app: FastAPI, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Callable]
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        # Prune expired timestamps
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < self.window_seconds
        ]
        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        self._requests[client_ip].append(now)
        return await call_next(request)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection for browser-originated state-changing requests.

    Only enforced when an ``Origin`` header is present (i.e. browser
    requests).  Direct API / test-client calls without ``Origin`` are
    allowed through so that existing tests remain unaffected.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    EXEMPT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/health"}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Callable]
    ) -> Response:
        if request.method not in self.SAFE_METHODS:
            origin = request.headers.get("origin")
            if origin:
                path = request.url.path
                if not any(path.startswith(p) for p in self.EXEMPT_PATHS):
                    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
                        return JSONResponse(
                            status_code=403, content={"detail": "CSRF check failed"}
                        )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


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
        service.add_connection(mock_config, user_id="system")
        logger.info("Mock connector registered and indexed.")
    except Exception:
        logger.exception("Failed to register mock connector at startup.")
    yield
    # Graceful shutdown
    logger.info("Shutting down gracefully...")
    for conn_id in list(_factory._instances.keys()):
        try:
            _factory.remove(conn_id)
        except Exception:
            pass
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DB Explorer API",
    version="0.1.0",
    description="Read-only database exploration and cleaning backend.",
    lifespan=lifespan,
)

# Middleware ordering: last-added runs first.
# Desired execution order (outermost → innermost):
#   CorrelationId → RateLimit → CORS → CSRF
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(v1_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    """Return service health including Redis and PostgreSQL status."""
    redis_ok = _cache.health_check()

    db_ok = True
    try:
        from src.infrastructure.database import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    overall = "ok" if (redis_ok and db_ok) else "degraded"
    return {
        "status": overall,
        "services": {
            "api": "ok",
            "postgres": "connected" if db_ok else "unavailable",
            "redis": "connected" if redis_ok else "unavailable",
        },
    }
