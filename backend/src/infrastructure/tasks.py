"""Celery tasks for background job processing."""
from __future__ import annotations

import json
import logging
from typing import Any

import redis

from src.config import get_settings
from src.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_redis_client() -> redis.Redis:
    """Create a Redis client for publishing progress events."""
    return redis.from_url(settings.REDIS_URL)


def _publish_progress(job_id: str, event_type: str, data: dict[str, Any]) -> None:
    """Publish a progress event to Redis Pub/Sub."""
    r: redis.Redis | None = None
    try:
        r = _get_redis_client()
        message = json.dumps({"event": event_type, **data})
        r.publish(f"job_progress:{job_id}", message)
    except Exception:
        logger.exception("Failed to publish progress for job %s", job_id)
    finally:
        if r is not None:
            r.close()


def _update_job_sync(
    job_id: str,
    status: str,
    progress_meta: dict | None = None,
    result_data: dict | None = None,
    error_message: str | None = None,
) -> None:
    """Update job status using a synchronous database connection."""
    from sqlalchemy import create_engine, text

    db_url = settings.DATABASE_URL
    # Convert async driver URL to sync psycopg2 for Celery workers.
    # DATABASE_URL is always 'postgresql+asyncpg://...' per config.py.
    sync_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    engine = create_engine(sync_url)
    try:
        with engine.connect() as conn:
            params: dict[str, Any] = {"status": status, "job_id": job_id}
            set_clauses = ["status = :status", "updated_at = NOW()"]
            if progress_meta is not None:
                set_clauses.append("progress_meta = :progress_meta")
                params["progress_meta"] = json.dumps(progress_meta)
            if result_data is not None:
                set_clauses.append("result_data = :result_data")
                params["result_data"] = json.dumps(result_data)
            if error_message is not None:
                set_clauses.append("error_message = :error_message")
                params["error_message"] = error_message
            # Safe: set_clauses are hardcoded column names, not user input
            sql = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = :job_id"  # noqa: E501
            conn.execute(text(sql), params)
            conn.commit()
    finally:
        engine.dispose()


@celery_app.task(name="deep_search", bind=True)
def deep_search_job(
    self, job_id: str, user_id: str, query: str, connection_ids: list[str]
) -> dict:
    """Scan data values across connections for deep search matches."""
    from src.core.ports.database import sanitize_identifier
    from src.dependencies import _factory

    total = len(connection_ids)
    _update_job_sync(
        job_id,
        "STARTED",
        progress_meta={
            "current": 0,
            "total": total,
            "percent": 0,
            "message": "Starting deep search...",
        },
    )
    _publish_progress(
        job_id, "started", {"current": 0, "total": total, "percent": 0}
    )

    all_matches: list[dict] = []

    for idx, conn_id in enumerate(connection_ids, 1):
        try:
            connector = _factory.get(conn_id)
            tables = connector.fetch_tables()
            for table_meta in tables:
                table_name = table_meta.get("table_name", "")
                schema_name = table_meta.get("schema_name")
                try:
                    qualified = sanitize_identifier(table_name)
                    if schema_name:
                        qualified = (
                            f"{sanitize_identifier(schema_name)}.{qualified}"
                        )
                    rows = connector.execute_safe_read(
                        f"SELECT * FROM {qualified}", max_rows=100
                    )
                    for row in rows:
                        for col_name, value in row.items():
                            if value and query.lower() in str(value).lower():
                                all_matches.append(
                                    {
                                        "source_db": conn_id,
                                        "db_type": type(connector)
                                        .__name__.lower()
                                        .replace("connector", ""),
                                        "schema_name": schema_name,
                                        "table_name": table_name,
                                        "column_name": col_name,
                                        "match_type": "data_value",
                                        "match_snippet": str(value)[:200],
                                    }
                                )
                                break  # one match per column is enough
                except Exception:
                    logger.debug("Could not scan table %s", table_name)
        except Exception:
            logger.exception("Failed to scan connection %s", conn_id)

        percent = int(idx / total * 100)
        progress = {
            "current": idx,
            "total": total,
            "percent": percent,
            "message": f"Scanned {idx}/{total} connections",
        }
        _update_job_sync(job_id, "PROGRESS", progress_meta=progress)
        _publish_progress(job_id, "progress", progress)

    _update_job_sync(
        job_id,
        "SUCCESS",
        result_data={
            "matches": all_matches,
            "total_matches": len(all_matches),
        },
    )
    _publish_progress(
        job_id,
        "complete",
        {"status": "SUCCESS", "total_matches": len(all_matches)},
    )
    return {"status": "SUCCESS", "total_matches": len(all_matches)}


@celery_app.task(name="reindex_metadata", bind=True)
def reindex_metadata_job(
    self, job_id: str, user_id: str, connection_id: str
) -> dict:
    """Re-crawl a connection and rebuild its metadata index."""
    from src.dependencies import _factory, _indexer

    _update_job_sync(
        job_id,
        "STARTED",
        progress_meta={
            "current": 0,
            "total": 1,
            "percent": 0,
            "message": "Starting metadata reindex...",
        },
    )
    _publish_progress(
        job_id, "started", {"current": 0, "total": 1, "percent": 0}
    )

    try:
        connector = _factory.get(connection_id)
        _indexer.remove_connection(connection_id, user_id)
        _indexer.index_connection(connection_id, connector, user_id)

        _update_job_sync(
            job_id,
            "SUCCESS",
            progress_meta={
                "current": 1,
                "total": 1,
                "percent": 100,
                "message": "Reindex complete",
            },
        )
        _publish_progress(job_id, "complete", {"status": "SUCCESS"})
        return {"status": "SUCCESS"}
    except Exception as exc:
        error_msg = str(exc)
        _update_job_sync(job_id, "FAILURE", error_message=error_msg)
        _publish_progress(
            job_id, "complete", {"status": "FAILURE", "error": error_msg}
        )
        return {"status": "FAILURE", "error": error_msg}
