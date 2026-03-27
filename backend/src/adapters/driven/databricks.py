from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional

from src.core.domain.types import UniversalDataType
from src.core.ports.database import ConfigurationError, DatabasePort

try:
    from databricks import sql as databricks_sql  # type: ignore[import-untyped]

    _HAS_DATABRICKS = True
except ImportError:
    _HAS_DATABRICKS = False

_SPARK_TYPE_MAP: dict[str, UniversalDataType] = {
    "STRING": UniversalDataType.TEXT,
    "VARCHAR": UniversalDataType.TEXT,
    "CHAR": UniversalDataType.TEXT,
    "INT": UniversalDataType.INTEGER,
    "INTEGER": UniversalDataType.INTEGER,
    "BIGINT": UniversalDataType.INTEGER,
    "SMALLINT": UniversalDataType.INTEGER,
    "TINYINT": UniversalDataType.INTEGER,
    "LONG": UniversalDataType.INTEGER,
    "FLOAT": UniversalDataType.FLOAT,
    "DOUBLE": UniversalDataType.FLOAT,
    "DECIMAL": UniversalDataType.FLOAT,
    "NUMERIC": UniversalDataType.FLOAT,
    "BOOLEAN": UniversalDataType.BOOLEAN,
    "BOOL": UniversalDataType.BOOLEAN,
    "DATE": UniversalDataType.TIMESTAMP,
    "TIMESTAMP": UniversalDataType.TIMESTAMP,
    "TIMESTAMP_NTZ": UniversalDataType.TIMESTAMP,
    "BINARY": UniversalDataType.BINARY,
    "BYTES": UniversalDataType.BINARY,
}


class DatabricksConnector(DatabasePort):
    """Read-only Databricks SQL connector."""

    def __init__(
        self,
        server_hostname: str,
        http_path: str,
        access_token: str,
        catalog: str = "hive_metastore",
        schema: str = "default",
    ) -> None:
        if not _HAS_DATABRICKS:
            raise ConfigurationError(
                "databricks-sql-connector package is not installed. "
                "Install it with: pip install databricks-sql-connector"
            )
        self._server_hostname = server_hostname
        self._http_path = http_path
        self._access_token = access_token
        self._catalog = catalog
        self._schema = schema
        self._conn: Any = None

    def connect(self) -> None:
        self._conn = databricks_sql.connect(
            server_hostname=self._server_hostname,
            http_path=self._http_path,
            access_token=self._access_token,
        )

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
        with self._conn.cursor() as cursor:
            cursor.execute(sql, parameters=params)
            cols = [desc[0] for desc in cursor.description]
            rows = cursor.fetchmany(max_rows)
            return [dict(zip(cols, row)) for row in rows]

    def execute_query_stream(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Iterator[dict[str, Any]]:
        self._validate_read_only(sql)
        with self._conn.cursor() as cursor:
            cursor.execute(sql, parameters=params)
            cols = [desc[0] for desc in cursor.description]
            while True:
                row = cursor.fetchone()
                if row is None:
                    break
                yield dict(zip(cols, row))

    def fetch_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> dict[str, UniversalDataType]:
        db_schema = schema or self._schema
        sql = f"DESCRIBE TABLE {self._catalog}.{db_schema}.{table}"  # noqa: S608
        self._validate_read_only(sql)
        with self._conn.cursor() as cursor:
            cursor.execute(sql)
            result: dict[str, UniversalDataType] = {}
            for row in cursor.fetchall():
                col_name, col_type = row[0], row[1]
                base_type = col_type.split("(")[0].upper()
                result[col_name] = _SPARK_TYPE_MAP.get(base_type, UniversalDataType.UNKNOWN)
            return result

    def fetch_tables(self, schema: Optional[str] = None) -> list[dict[str, Any]]:
        db_schema = schema or self._schema
        sql = f"SHOW TABLES IN {self._catalog}.{db_schema}"  # noqa: S608
        self._validate_read_only(sql)
        with self._conn.cursor() as cursor:
            cursor.execute(sql)
            return [
                {"schema_name": db_schema, "table_name": row[1]}
                for row in cursor.fetchall()
            ]
