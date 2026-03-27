from __future__ import annotations

from src.application.data_service import DataService
from src.core.domain.models import PeekRequest, SearchRequest, WorkbenchPane, WorkbenchRequest


def test_search_returns_results(data_service: DataService) -> None:
    results = data_service.search(SearchRequest(query="user"))
    assert len(results) > 0
    table_names = [r.table_name for r in results]
    assert any("USER" in t.upper() for t in table_names)


def test_search_empty_query_returns_results(data_service: DataService) -> None:
    results = data_service.search(SearchRequest(query=""))
    # empty LIKE pattern '%' matches everything
    assert isinstance(results, list)


def test_search_with_source_filter(data_service: DataService) -> None:
    results = data_service.search(SearchRequest(query="profit", source_filter=["test-mock"]))
    assert all(r.source_db == "test-mock" for r in results)


def test_peek_returns_sample_data(data_service: DataService) -> None:
    request = PeekRequest(
        connection_id="test-mock",
        table_name="USER_PROFIT_SUMMARY",
        schema_name="FINANCE_SCHEMA",
    )
    rows = data_service.peek(request)
    assert len(rows) > 0
    # Check it deduplicated (4 raw rows → 3 unique)
    assert len(rows) == 3


def test_peek_returns_universal_rows(data_service: DataService) -> None:
    request = PeekRequest(
        connection_id="test-mock",
        table_name="TRANSACTION_LOG",
        schema_name="FINANCE_SCHEMA",
    )
    rows = data_service.peek(request)
    assert len(rows) == 2
    first_row_cols = {cell.column for cell in rows[0]}
    assert "TX_ID" in first_row_cols


def test_workbench_returns_pane_data(data_service: DataService) -> None:
    request = WorkbenchRequest(
        panes=[
            WorkbenchPane(
                connection_id="test-mock",
                table_name="USER_PROFIT_SUMMARY",
                schema_name="FINANCE_SCHEMA",
                pane_id="pane-1",
            ),
            WorkbenchPane(
                connection_id="test-mock",
                table_name="TRANSACTION_LOG",
                schema_name="FINANCE_SCHEMA",
                pane_id="pane-2",
            ),
        ]
    )
    result = data_service.get_workbench_data(request)
    assert "pane-1" in result
    assert "pane-2" in result
    assert len(result["pane-1"]) > 0
    assert len(result["pane-2"]) > 0


def test_list_connections(data_service: DataService) -> None:
    connections = data_service.list_connections()
    assert len(connections) == 1
    assert connections[0]["id"] == "test-mock"
