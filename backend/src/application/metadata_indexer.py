from __future__ import annotations

import logging
import sqlite3
import uuid

from src.core.domain.models import SearchResult
from src.core.ports.database import DatabasePort

logger = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS metadata (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    connection_id TEXT NOT NULL,
    db_type     TEXT NOT NULL,
    schema_name TEXT,
    table_name  TEXT NOT NULL,
    column_name TEXT,
    entry_type  TEXT NOT NULL,   -- 'table' or 'column'
    full_text   TEXT NOT NULL    -- searchable blob
);
CREATE INDEX IF NOT EXISTS idx_full_text ON metadata(full_text);
CREATE INDEX IF NOT EXISTS idx_user_id ON metadata(user_id);
"""


class MetadataIndexer:
    """Indexes database metadata (tables/columns) in SQLite for fuzzy search."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(_DDL)
        self._conn.commit()

    def index_connection(
        self, connection_id: str, connector: DatabasePort, *, user_id: str
    ) -> None:
        """Crawl tables and columns from connector and store in SQLite."""
        try:
            tables = connector.fetch_tables()
        except Exception:
            logger.exception("Failed to fetch tables for connection %s", connection_id)
            return

        db_type = type(connector).__name__.lower().replace("connector", "")

        rows_to_insert: list[tuple] = []
        for table_meta in tables:
            table_name = table_meta.get("table_name", "")
            schema_name = table_meta.get("schema_name")

            table_id = str(uuid.uuid4())
            full_text = " ".join(filter(None, [schema_name, table_name])).lower()
            rows_to_insert.append(
                (
                    table_id,
                    user_id,
                    connection_id,
                    db_type,
                    schema_name,
                    table_name,
                    None,
                    "table",
                    full_text,
                )
            )

            try:
                schema = connector.fetch_schema(table_name, schema_name)
            except Exception:
                logger.debug("Could not fetch schema for %s.%s", schema_name, table_name)
                schema = {}

            for col_name in schema:
                col_id = str(uuid.uuid4())
                col_full_text = " ".join(
                    filter(None, [schema_name, table_name, col_name])
                ).lower()
                rows_to_insert.append(
                    (
                        col_id,
                        user_id,
                        connection_id,
                        db_type,
                        schema_name,
                        table_name,
                        col_name,
                        "column",
                        col_full_text,
                    )
                )

        self._conn.executemany(
            "INSERT OR REPLACE INTO metadata VALUES (?,?,?,?,?,?,?,?,?)",
            rows_to_insert,
        )
        self._conn.commit()
        logger.info(
            "Indexed %d entries for connection %s", len(rows_to_insert), connection_id
        )

    def search(self, query: str, *, user_id: str, limit: int = 50) -> list[SearchResult]:
        """Fuzzy (LIKE) search over indexed metadata scoped to a user."""
        pattern = f"%{query.lower()}%"
        cursor = self._conn.execute(
            """
            SELECT id, connection_id, db_type, schema_name, table_name, column_name, entry_type
            FROM metadata
            WHERE user_id = ? AND full_text LIKE ?
            ORDER BY
                CASE entry_type WHEN 'table' THEN 0 ELSE 1 END,
                table_name
            LIMIT ?
            """,
            (user_id, pattern, limit),
        )
        results: list[SearchResult] = []
        for row in cursor.fetchall():
            rid, conn_id, db_type, schema_name, table_name, col_name, entry_type = row
            match_type = "table" if entry_type == "table" else "column"
            snippet_parts = [p for p in [schema_name, table_name, col_name] if p]
            results.append(
                SearchResult(
                    id=rid,
                    source_db=conn_id,
                    db_type=db_type,
                    schema_name=schema_name,
                    table_name=table_name,
                    column_name=col_name,
                    match_type=match_type,
                    match_snippet=".".join(snippet_parts),
                )
            )
        return results

    def remove_connection(self, connection_id: str, *, user_id: str) -> None:
        self._conn.execute(
            "DELETE FROM metadata WHERE connection_id = ? AND user_id = ?",
            (connection_id, user_id),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
