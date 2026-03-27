from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional

from src.core.domain.types import UniversalDataType
from src.core.ports.database import ConfigurationError, DatabasePort, sanitize_identifier

try:
    from clickhouse_driver import Client  # type: ignore[import-untyped]

    _HAS_CLICKHOUSE = True
except ImportError:
    _HAS_CLICKHOUSE = False

_CH_TYPE_MAP: dict[str, UniversalDataType] = {
    "String": UniversalDataType.TEXT,
    "FixedString": UniversalDataType.TEXT,
    "UUID": UniversalDataType.TEXT,
    "Int8": UniversalDataType.INTEGER,
    "Int16": UniversalDataType.INTEGER,
    "Int32": UniversalDataType.INTEGER,
    "Int64": UniversalDataType.INTEGER,
    "UInt8": UniversalDataType.INTEGER,
    "UInt16": UniversalDataType.INTEGER,
    "UInt32": UniversalDataType.INTEGER,
    "UInt64": UniversalDataType.INTEGER,
    "Float32": UniversalDataType.FLOAT,
    "Float64": UniversalDataType.FLOAT,
    "Decimal": UniversalDataType.FLOAT,
    "Bool": UniversalDataType.BOOLEAN,
    "Date": UniversalDataType.TIMESTAMP,
    "Date32": UniversalDataType.TIMESTAMP,
    "DateTime": UniversalDataType.TIMESTAMP,
    "DateTime64": UniversalDataType.TIMESTAMP,
}


class ClickHouseConnector(DatabasePort):
    """Read-only ClickHouse connector using clickhouse-driver."""

    def __init__(
        self,
        host: str,
        port: int = 9000,
        database: str = "default",
        username: str = "default",
        password: str = "",
    ) -> None:
        if not _HAS_CLICKHOUSE:
            raise ConfigurationError(
                "clickhouse-driver package is not installed. "
                "Install it with: pip install clickhouse-driver"
            )
        self._host = host
        self._port = port
        self._database = database
        self._username = username
        self._password = password
        self._client: Any = None

    def connect(self) -> None:
        self._client = Client(
            host=self._host,
            port=self._port,
            database=self._database,
            user=self._username,
            password=self._password,
            settings={"readonly": 1},
        )

    def close(self) -> None:
        if self._client:
            self._client.disconnect()
            self._client = None

    def execute_safe_read(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> list[dict[str, Any]]:
        self._validate_read_only(sql)
        rows, cols_meta = self._client.execute(sql, params or {}, with_column_types=True)
        cols = [meta[0] for meta in cols_meta]
        return [dict(zip(cols, row)) for row in rows[:max_rows]]

    def execute_query_stream(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Iterator[dict[str, Any]]:
        self._validate_read_only(sql)
        rows, cols_meta = self._client.execute(sql, params or {}, with_column_types=True)
        cols = [meta[0] for meta in cols_meta]
        for row in rows:
            yield dict(zip(cols, row))

    def fetch_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> dict[str, UniversalDataType]:
        db = sanitize_identifier(schema or self._database)
        safe_table = sanitize_identifier(table)
        sql = f"DESCRIBE TABLE {db}.{safe_table}"  # noqa: S608
        self._validate_read_only(sql)
        rows = self._client.execute(sql)
        result: dict[str, UniversalDataType] = {}
        for row in rows:
            col_name, col_type = row[0], row[1]
            base_type = col_type.split("(")[0].split("<")[0].strip("Nullable(").strip(")")
            result[col_name] = _CH_TYPE_MAP.get(base_type, UniversalDataType.UNKNOWN)
        return result

    def fetch_tables(self, schema: Optional[str] = None) -> list[dict[str, Any]]:
        db = sanitize_identifier(schema or self._database)
        sql = f"SHOW TABLES FROM {db}"  # noqa: S608
        self._validate_read_only(sql)
        rows = self._client.execute(sql)
        return [{"schema_name": db, "table_name": row[0]} for row in rows]
