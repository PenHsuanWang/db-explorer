from __future__ import annotations

from src.core.domain.models import (
    CleaningConfig,
    ConnectionConfig,
    PeekRequest,
    SearchRequest,
    SearchResult,
    WorkbenchPane,
    WorkbenchRequest,
)
from src.core.domain.types import UniversalDataType


def test_cleaning_config_defaults() -> None:
    config = CleaningConfig()
    assert config.hide_null_values is False
    assert config.date_format == "ISO8601"
    assert config.trim_strings is True
    assert config.column_aliases == {}
    assert config.type_overrides == {}


def test_universal_data_type_values() -> None:
    assert UniversalDataType.TEXT == "TEXT"
    assert UniversalDataType.INTEGER == "INTEGER"
    assert UniversalDataType.FLOAT == "FLOAT"
    assert UniversalDataType.BOOLEAN == "BOOLEAN"
    assert UniversalDataType.TIMESTAMP == "TIMESTAMP"
    assert UniversalDataType.BINARY == "BINARY"
    assert UniversalDataType.UNKNOWN == "UNKNOWN"


def test_connection_config_optional_fields() -> None:
    config = ConnectionConfig(name="test", db_type="mock")
    assert config.id is None
    assert config.host == ""
    assert config.port is None
    assert config.password is None


def test_search_request_defaults() -> None:
    req = SearchRequest(query="foo")
    assert req.deep_search is False
    assert req.source_filter is None
    assert req.match_type_filter is None


def test_peek_request_default_cleaning_config() -> None:
    req = PeekRequest(connection_id="abc", table_name="MY_TABLE")
    assert req.cleaning_config.trim_strings is True
    assert req.schema_name is None


def test_workbench_request_structure() -> None:
    pane = WorkbenchPane(
        connection_id="conn-1",
        table_name="MY_TABLE",
        pane_id="p1",
    )
    req = WorkbenchRequest(panes=[pane])
    assert len(req.panes) == 1
    assert req.panes[0].pane_id == "p1"


def test_search_result_structure() -> None:
    result = SearchResult(
        id="r1",
        source_db="conn-1",
        db_type="mock",
        table_name="MY_TABLE",
        match_type="table",
        match_snippet="MY_TABLE",
    )
    assert result.column_name is None
    assert result.schema_name is None
    assert result.preview_columns == []
