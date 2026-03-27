from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional

from src.core.domain.types import UniversalDataType
from src.core.ports.database import ConfigurationError, DatabasePort

try:
    import oracledb  # type: ignore[import-untyped]

    _HAS_ORACLEDB = True
except ImportError:
    _HAS_ORACLEDB = False

_ORACLE_TYPE_MAP: dict[str, UniversalDataType] = {
    "VARCHAR2": UniversalDataType.TEXT,
    "NVARCHAR2": UniversalDataType.TEXT,
    "CHAR": UniversalDataType.TEXT,
    "NCHAR": UniversalDataType.TEXT,
    "CLOB": UniversalDataType.TEXT,
    "NCLOB": UniversalDataType.TEXT,
    "NUMBER": UniversalDataType.FLOAT,
    "FLOAT": UniversalDataType.FLOAT,
    "BINARY_FLOAT": UniversalDataType.FLOAT,
    "BINARY_DOUBLE": UniversalDataType.FLOAT,
    "INTEGER": UniversalDataType.INTEGER,
    "INT": UniversalDataType.INTEGER,
    "SMALLINT": UniversalDataType.INTEGER,
    "DATE": UniversalDataType.TIMESTAMP,
    "TIMESTAMP": UniversalDataType.TIMESTAMP,
    "BLOB": UniversalDataType.BINARY,
    "RAW": UniversalDataType.BINARY,
}


class OracleConnector(DatabasePort):
    """Read-only Oracle DB connector using oracledb."""

    def __init__(
        self,
        host: str,
        port: int = 1521,
        service_name: str = "",
        username: str = "",
        password: str = "",
    ) -> None:
        if not _HAS_ORACLEDB:
            raise ConfigurationError(
                "oracledb package is not installed. "
                "Install it with: pip install oracledb"
            )
        self._host = host
        self._port = port
        self._service_name = service_name
        self._username = username
        self._password = password
        self._conn: Any = None

    def connect(self) -> None:
        dsn = oracledb.makedsn(self._host, self._port, service_name=self._service_name)
        self._conn = oracledb.connect(
            user=self._username,
            password=self._password,
            dsn=dsn,
        )
        with self._conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute_safe_read(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> list[dict[str, Any]]:
        self._validate_read_only(sql)
        with self._conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [desc[0].upper() for desc in cur.description]
            rows = cur.fetchmany(max_rows)
            return [dict(zip(cols, row)) for row in rows]

    def execute_query_stream(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Iterator[dict[str, Any]]:
        self._validate_read_only(sql)
        with self._conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [desc[0].upper() for desc in cur.description]
            for row in cur:
                yield dict(zip(cols, row))

    def fetch_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> dict[str, UniversalDataType]:
        owner = schema.upper() if schema else self._username.upper()
        sql = (
            "SELECT COLUMN_NAME, DATA_TYPE FROM ALL_TAB_COLUMNS "
            "WHERE OWNER = :owner AND TABLE_NAME = :table"
        )
        with self._conn.cursor() as cur:
            cur.execute(sql, {"owner": owner, "table": table.upper()})
            return {
                row[0]: _ORACLE_TYPE_MAP.get(
                    row[1].split("(")[0].upper(), UniversalDataType.UNKNOWN
                )
                for row in cur.fetchall()
            }

    def fetch_tables(self, schema: Optional[str] = None) -> list[dict[str, Any]]:
        owner = schema.upper() if schema else self._username.upper()
        sql = "SELECT OWNER, TABLE_NAME FROM ALL_TABLES WHERE OWNER = :owner ORDER BY TABLE_NAME"
        with self._conn.cursor() as cur:
            cur.execute(sql, {"owner": owner})
            return [{"schema_name": row[0], "table_name": row[1]} for row in cur.fetchall()]
