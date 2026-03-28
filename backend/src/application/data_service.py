from __future__ import annotations

import logging
import uuid
from typing import Any

from src.application.cleaning_engine import CleaningEngine
from src.application.metadata_indexer import MetadataIndexer
from src.core.domain.models import (
    ConnectionConfig,
    PeekRequest,
    SearchRequest,
    SearchResult,
    WorkbenchRequest,
)
from src.core.domain.types import UniversalRow
from src.core.ports.database import DatabasePort, sanitize_identifier

logger = logging.getLogger(__name__)


class DataService:
    """Orchestrates data fetching, cleaning, and search across connectors."""

    def __init__(
        self,
        factory: Any,
        indexer: MetadataIndexer,
        cleaning_engine: CleaningEngine,
    ) -> None:
        self._factory = factory
        self._indexer = indexer
        self._engine = cleaning_engine

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def add_connection(self, config: ConnectionConfig, *, user_id: str) -> str:
        if not config.id:
            config = config.model_copy(update={"id": str(uuid.uuid4())})
        connector = self._factory.create(config)
        connector.connect()
        self._indexer.index_connection(config.id, connector, user_id=user_id)  # type: ignore[arg-type]
        logger.info("Added connection %s (%s)", config.id, config.name)
        return config.id  # type: ignore[return-value]

    def list_connections(self) -> list[dict[str, Any]]:
        return self._factory.list_connections()

    def remove_connection(self, connection_id: str, *, user_id: str) -> None:
        self._factory.remove(connection_id)
        self._indexer.remove_connection(connection_id, user_id=user_id)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, request: SearchRequest, *, user_id: str) -> list[SearchResult]:
        results = self._indexer.search(request.query, user_id=user_id)
        if request.source_filter:
            results = [r for r in results if r.source_db in request.source_filter]
        if request.match_type_filter:
            results = [r for r in results if r.match_type == request.match_type_filter]
        return results

    # ------------------------------------------------------------------
    # Peek
    # ------------------------------------------------------------------

    def peek(self, request: PeekRequest) -> list[UniversalRow]:
        connector: DatabasePort = self._factory.get(request.connection_id)
        qualified = self._qualify(request.table_name, request.schema_name)
        sql = f"SELECT * FROM {qualified}"  # noqa: S608
        raw_rows = connector.execute_safe_read(sql, max_rows=50)
        schema = connector.fetch_schema(request.table_name, request.schema_name)
        return self._engine.apply(raw_rows, schema, request.cleaning_config)

    # ------------------------------------------------------------------
    # Workbench
    # ------------------------------------------------------------------

    def get_workbench_data(
        self, request: WorkbenchRequest
    ) -> dict[str, list[UniversalRow]]:
        result: dict[str, list[UniversalRow]] = {}
        for pane in request.panes:
            connector: DatabasePort = self._factory.get(pane.connection_id)
            qualified = self._qualify(pane.table_name, pane.schema_name)
            sql = f"SELECT * FROM {qualified}"  # noqa: S608
            raw_rows = connector.execute_safe_read(sql, max_rows=1000)
            schema = connector.fetch_schema(pane.table_name, pane.schema_name)
            result[pane.pane_id] = self._engine.apply(
                raw_rows, schema, request.cleaning_config
            )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _qualify(table: str, schema: str | None) -> str:
        safe_table = sanitize_identifier(table)
        if schema:
            return f"{sanitize_identifier(schema)}.{safe_table}"
        return safe_table
