from __future__ import annotations

import pytest

from src.application.cleaning_engine import CleaningEngine
from src.core.domain.models import CleaningConfig
from src.core.domain.types import UniversalDataType


@pytest.fixture
def engine() -> CleaningEngine:
    return CleaningEngine()


@pytest.fixture
def simple_schema() -> dict[str, UniversalDataType]:
    return {
        "name": UniversalDataType.TEXT,
        "age": UniversalDataType.INTEGER,
        "score": UniversalDataType.FLOAT,
        "active": UniversalDataType.BOOLEAN,
        "created_at": UniversalDataType.TIMESTAMP,
    }


def test_normalize_nulls(
    engine: CleaningEngine, simple_schema: dict[str, UniversalDataType]
) -> None:
    rows = [
        {"name": "null", "age": "N/A", "score": float("nan"), "active": True, "created_at": None}
    ]
    result = engine.apply(rows, simple_schema, CleaningConfig())
    assert len(result) == 1
    row = {cell.column: cell.value for cell in result[0]}
    assert row["name"] is None
    assert row["age"] is None
    assert row["score"] is None
    assert row["created_at"] is None


def test_deduplicate(
    engine: CleaningEngine, simple_schema: dict[str, UniversalDataType]
) -> None:
    row = {"name": "alice", "age": 30, "score": 9.5, "active": True, "created_at": None}
    rows = [row, row, row]
    result = engine.apply(rows, simple_schema, CleaningConfig())
    assert len(result) == 1


def test_type_cast(
    engine: CleaningEngine, simple_schema: dict[str, UniversalDataType]
) -> None:
    rows = [
        {
            "name": 42,
            "age": "25",
            "score": "3.14",
            "active": "true",
            "created_at": "2024-01-01T00:00:00",
        }
    ]
    result = engine.apply(rows, simple_schema, CleaningConfig())
    assert len(result) == 1
    row = {cell.column: cell.value for cell in result[0]}
    assert row["name"] == "42"
    assert row["age"] == 25
    assert abs(row["score"] - 3.14) < 1e-9
    assert row["active"] is True


def test_hide_null_values(
    engine: CleaningEngine, simple_schema: dict[str, UniversalDataType]
) -> None:
    rows = [{"name": None, "age": 25, "score": None, "active": True, "created_at": None}]
    config = CleaningConfig(hide_null_values=True)
    result = engine.apply(rows, simple_schema, config)
    assert len(result) == 1
    columns = [cell.column for cell in result[0]]
    assert "name" not in columns
    assert "score" not in columns
    assert "age" in columns


def test_date_format(
    engine: CleaningEngine, simple_schema: dict[str, UniversalDataType]
) -> None:
    rows = [
        {
            "name": "x",
            "age": 1,
            "score": 1.0,
            "active": False,
            "created_at": "2024-06-15T12:00:00",
        }
    ]
    result = engine.apply(rows, simple_schema, CleaningConfig())
    row = {cell.column: cell.value for cell in result[0]}
    # Should be ISO 8601 string
    assert "2024-06-15" in str(row["created_at"])


def test_trim_strings(engine: CleaningEngine, simple_schema: dict[str, UniversalDataType]) -> None:
    rows = [{"name": "  bob  ", "age": 20, "score": 1.0, "active": True, "created_at": None}]
    result = engine.apply(rows, simple_schema, CleaningConfig(trim_strings=True))
    row = {cell.column: cell.value for cell in result[0]}
    assert row["name"] == "bob"


def test_column_aliases(engine: CleaningEngine) -> None:
    schema = {"old_col": UniversalDataType.TEXT}
    rows = [{"old_col": "value"}]
    config = CleaningConfig(column_aliases={"old_col": "new_col"})
    result = engine.apply(rows, schema, config)
    columns = [cell.column for cell in result[0]]
    assert "new_col" in columns
    assert "old_col" not in columns


def test_type_overrides(engine: CleaningEngine) -> None:
    schema = {"amount": UniversalDataType.TEXT}
    rows = [{"amount": "42"}]
    config = CleaningConfig(type_overrides={"amount": "FLOAT"})
    result = engine.apply(rows, schema, config)
    row = {cell.column: cell.value for cell in result[0]}
    assert isinstance(row["amount"], float)
