from __future__ import annotations

import pytest

from src.adapters.driven.mock import MockConnector
from src.core.domain.types import UniversalDataType
from src.core.ports.database import ReadOnlyViolationError


@pytest.fixture
def connector() -> MockConnector:
    c = MockConnector()
    c.connect()
    return c


def test_execute_safe_read_returns_rows(connector: MockConnector) -> None:
    rows = connector.execute_safe_read("SELECT * FROM USER_PROFIT_SUMMARY")
    assert len(rows) > 0
    assert "USER_ID" in rows[0]


def test_execute_safe_read_respects_max_rows(connector: MockConnector) -> None:
    rows = connector.execute_safe_read("SELECT * FROM USER_PROFIT_SUMMARY", max_rows=1)
    assert len(rows) == 1


def test_read_only_violation_raised_on_insert(connector: MockConnector) -> None:
    with pytest.raises(ReadOnlyViolationError):
        connector.execute_safe_read("INSERT INTO users VALUES (1, 'x')")


def test_read_only_violation_raised_on_update(connector: MockConnector) -> None:
    with pytest.raises(ReadOnlyViolationError):
        connector.execute_safe_read("UPDATE users SET name='x' WHERE id=1")


def test_read_only_violation_raised_on_delete(connector: MockConnector) -> None:
    with pytest.raises(ReadOnlyViolationError):
        connector.execute_safe_read("DELETE FROM users WHERE id=1")


def test_read_only_violation_raised_on_drop(connector: MockConnector) -> None:
    with pytest.raises(ReadOnlyViolationError):
        connector.execute_safe_read("DROP TABLE users")


def test_fetch_schema_returns_types(connector: MockConnector) -> None:
    schema = connector.fetch_schema("USER_PROFIT_SUMMARY", "FINANCE_SCHEMA")
    assert schema["USER_ID"] == UniversalDataType.INTEGER
    assert schema["USERNAME"] == UniversalDataType.TEXT
    assert schema["PROFIT"] == UniversalDataType.FLOAT
    assert schema["ACTIVE"] == UniversalDataType.BOOLEAN


def test_fetch_tables_returns_all(connector: MockConnector) -> None:
    tables = connector.fetch_tables()
    assert len(tables) == 3
    table_names = [t["table_name"] for t in tables]
    assert "USER_PROFIT_SUMMARY" in table_names


def test_fetch_tables_filtered_by_schema(connector: MockConnector) -> None:
    tables = connector.fetch_tables(schema="FINANCE_SCHEMA")
    assert all(t["schema_name"] == "FINANCE_SCHEMA" for t in tables)


def test_stream_rows(connector: MockConnector) -> None:
    rows = list(connector.execute_query_stream("SELECT * FROM TRANSACTION_LOG"))
    assert len(rows) == 2


def test_close_and_reconnect(connector: MockConnector) -> None:
    connector.close()
    assert not connector._connected
    connector.connect()
    assert connector._connected
