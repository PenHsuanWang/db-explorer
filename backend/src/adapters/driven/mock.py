from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional

from src.core.domain.types import UniversalDataType
from src.core.ports.database import DatabasePort

_SAMPLE_TABLES = [
    {"schema_name": "FINANCE_SCHEMA", "table_name": "USER_PROFIT_SUMMARY"},
    {"schema_name": "FINANCE_SCHEMA", "table_name": "TRANSACTION_LOG"},
    {"schema_name": "HR_SCHEMA", "table_name": "EMPLOYEE_RECORDS"},
]

_SAMPLE_SCHEMAS: dict[str, dict[str, UniversalDataType]] = {
    "USER_PROFIT_SUMMARY": {
        "USER_ID": UniversalDataType.INTEGER,
        "USERNAME": UniversalDataType.TEXT,
        "PROFIT": UniversalDataType.FLOAT,
        "RECORDED_AT": UniversalDataType.TIMESTAMP,
        "ACTIVE": UniversalDataType.BOOLEAN,
    },
    "TRANSACTION_LOG": {
        "TX_ID": UniversalDataType.TEXT,
        "AMOUNT": UniversalDataType.FLOAT,
        "CURRENCY": UniversalDataType.TEXT,
        "TX_DATE": UniversalDataType.TIMESTAMP,
    },
    "EMPLOYEE_RECORDS": {
        "EMP_ID": UniversalDataType.INTEGER,
        "FULL_NAME": UniversalDataType.TEXT,
        "DEPARTMENT": UniversalDataType.TEXT,
        "SALARY": UniversalDataType.FLOAT,
    },
}

_SAMPLE_ROWS: dict[str, list[dict[str, Any]]] = {
    "USER_PROFIT_SUMMARY": [
        {
            "USER_ID": 1,
            "USERNAME": "alice",
            "PROFIT": 1500.75,
            "RECORDED_AT": "2024-01-15T10:30:00",
            "ACTIVE": True,
        },
        {
            "USER_ID": 2,
            "USERNAME": "bob",
            "PROFIT": None,
            "RECORDED_AT": "2024-01-16T08:00:00",
            "ACTIVE": False,
        },
        {
            "USER_ID": 3,
            "USERNAME": "  carol  ",
            "PROFIT": 3200.00,
            "RECORDED_AT": "2024-01-17T12:00:00",
            "ACTIVE": True,
        },
        # Duplicate to test dedup
        {
            "USER_ID": 1,
            "USERNAME": "alice",
            "PROFIT": 1500.75,
            "RECORDED_AT": "2024-01-15T10:30:00",
            "ACTIVE": True,
        },
    ],
    "TRANSACTION_LOG": [
        {"TX_ID": "T001", "AMOUNT": 250.00, "CURRENCY": "USD", "TX_DATE": "2024-01-10T09:00:00"},
        {"TX_ID": "T002", "AMOUNT": 99.99, "CURRENCY": "EUR", "TX_DATE": "2024-01-11T14:30:00"},
    ],
    "EMPLOYEE_RECORDS": [
        {"EMP_ID": 101, "FULL_NAME": "Dave Smith", "DEPARTMENT": "Engineering", "SALARY": 95000.0},
        {"EMP_ID": 102, "FULL_NAME": "Eve Johnson", "DEPARTMENT": "Finance", "SALARY": 88000.0},
    ],
}


class MockConnector(DatabasePort):
    """In-memory connector used for testing and demos."""

    def __init__(self, name: str = "mock") -> None:
        self.name = name
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def execute_safe_read(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> list[dict[str, Any]]:
        self._validate_read_only(sql)
        table_name = self._extract_table(sql)
        rows = _SAMPLE_ROWS.get(table_name, [])
        return rows[:max_rows]

    def execute_query_stream(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Iterator[dict[str, Any]]:
        self._validate_read_only(sql)
        table_name = self._extract_table(sql)
        yield from _SAMPLE_ROWS.get(table_name, [])

    def fetch_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> dict[str, UniversalDataType]:
        return _SAMPLE_SCHEMAS.get(table, {})

    def fetch_tables(self, schema: Optional[str] = None) -> list[dict[str, Any]]:
        if schema:
            return [t for t in _SAMPLE_TABLES if t.get("schema_name") == schema]
        return list(_SAMPLE_TABLES)

    # ------------------------------------------------------------------

    @staticmethod
    def _extract_table(sql: str) -> str:
        """Naive extraction of the table name from a SELECT … FROM <table> statement."""
        parts = sql.upper().split()
        try:
            idx = parts.index("FROM")
            full = sql.split()[idx + 1]
            # Strip schema prefix if present (e.g. FINANCE_SCHEMA.USER_PROFIT_SUMMARY)
            return full.split(".")[-1]
        except (ValueError, IndexError):
            return ""

    def raise_on_write(self, sql: str) -> None:
        """Public helper used in tests to verify write rejection."""
        self._validate_read_only(sql)

    def _validate_read_only(self, sql: str) -> None:
        """Override to raise ReadOnlyViolationError on write statements."""
        super()._validate_read_only(sql)
