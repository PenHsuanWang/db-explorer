from __future__ import annotations

from typing import Any

from src.adapters.driven.clickhouse import ClickHouseConnector
from src.adapters.driven.databricks import DatabricksConnector
from src.adapters.driven.mock import MockConnector
from src.adapters.driven.oracle import OracleConnector
from src.core.domain.models import ConnectionConfig
from src.core.ports.database import ConfigurationError, DatabasePort

_REGISTRY: dict[str, type[DatabasePort]] = {
    "oracle": OracleConnector,  # type: ignore[type-abstract]
    "clickhouse": ClickHouseConnector,  # type: ignore[type-abstract]
    "databricks": DatabricksConnector,  # type: ignore[type-abstract]
    "mock": MockConnector,  # type: ignore[type-abstract]
}


class ConnectorFactory:
    """Creates and manages DatabasePort instances by connection_id."""

    def __init__(self) -> None:
        self._instances: dict[str, DatabasePort] = {}
        self._configs: dict[str, ConnectionConfig] = {}

    def create(self, config: ConnectionConfig) -> DatabasePort:
        db_type = config.db_type.lower()
        if db_type not in _REGISTRY:
            raise ConfigurationError(
                f"Unsupported db_type '{config.db_type}'. "
                f"Supported types: {list(_REGISTRY)}"
            )
        connector = self._build(db_type, config)
        self._instances[config.id] = connector  # type: ignore[index]
        self._configs[config.id] = config  # type: ignore[index]
        return connector

    def get(self, connection_id: str) -> DatabasePort:
        if connection_id not in self._instances:
            raise ConfigurationError(f"No connector registered for id '{connection_id}'")
        return self._instances[connection_id]

    def remove(self, connection_id: str) -> None:
        connector = self._instances.pop(connection_id, None)
        if connector:
            try:
                connector.close()
            except Exception:  # noqa: BLE001
                pass
        self._configs.pop(connection_id, None)

    def list_connections(self) -> list[dict[str, Any]]:
        result = []
        for cid, cfg in self._configs.items():
            result.append(
                {
                    "id": cid,
                    "name": cfg.name,
                    "db_type": cfg.db_type,
                    "host": cfg.host,
                    "database": cfg.database,
                }
            )
        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _build(db_type: str, config: ConnectionConfig) -> DatabasePort:
        password = config.password.get_secret_value() if config.password else ""
        if db_type == "mock":
            return MockConnector(name=config.name)
        if db_type == "oracle":
            return OracleConnector(
                host=config.host,
                port=config.port or 1521,
                service_name=config.database,
                username=config.username,
                password=password,
            )
        if db_type == "clickhouse":
            return ClickHouseConnector(
                host=config.host,
                port=config.port or 9000,
                database=config.database,
                username=config.username,
                password=password,
            )
        if db_type == "databricks":
            return DatabricksConnector(
                server_hostname=config.host,
                http_path=config.extra_params.get("http_path", ""),
                access_token=password,
                catalog=config.extra_params.get("catalog", "hive_metastore"),
                schema=config.database,
            )
        raise ConfigurationError(f"No builder for db_type '{db_type}'")
