# Hexagonal Architecture Reference (Database Explorer)

This document defines the implementation contracts and connector requirements for the Database Explorer project following a hexagonal (ports & adapters) architecture.

## 1. Layers and Allowed Dependencies

| Layer | Path | Allowed Imports |
| :--- | :--- | :--- |
| **Domain** | `src/core/domain` | Python stdlib, typing, small pure helpers, pydantic models (value objects) |
| **Ports** | `src/core/ports` | Domain |
| **Application** | `src/application` | Domain, Ports |
| **Adapters (Driving / Driven)** | `src/adapters` | Application, Ports, 3rd-party drivers (DB clients), frameworks (FastAPI) |

Rules:
- Inner layers must not import outer layers.
- Side effects (I/O) belong in adapters only; domain and application layers should be pure or orchestrating.

## 2. Core Components

- `UniversalDataType` (enum): Canonical types exposed by adapters. Example members: `TEXT`, `INTEGER`, `FLOAT`, `BOOLEAN`, `TIMESTAMP`, `BINARY`.
- `DatabasePort` (abstract interface): Defines the contract every driver/adapter must implement. See interface section below.
- `ConnectorFactory`: Registry that maps adapter IDs (e.g., `oracle`, `clickhouse`, `databricks`) to concrete connector classes.

## 3. `DatabasePort` Interface (suggested contract)

Methods every adapter must implement:

- `connect() -> None` : Establish connections or validate configuration.
- `close() -> None` : Cleanly close resources.
- `execute_query_stream(sql: str, params: Optional[Mapping[str, Any]] = None) -> Iterator[Mapping[str, Any]]` : Stream rows as dictionaries (generator/yield).
- `fetch_schema(table: str) -> Mapping[str, UniversalDataType]` : Return canonical column types.
- `execute_safe_read(sql: str, params: Optional[Mapping[str, Any]] = None, max_rows: int = 1000) -> List[Mapping[str, Any]]` : Convenience method that enforces limits and read-only checks.

Behavioral requirements:
- Adapters must enforce read-only connections by default and throw when write operations are attempted unless explicitly enabled in configuration and audited.
- Adapters must normalize provider-specific types into `UniversalDataType`.
- Errors must be converted into a common exception hierarchy (e.g., `ConnectorError`, `TransientError`) for the application layer to handle.

## 4. Streaming & Transport Contract

- Streaming query execution (`execute_query_stream`) must yield rows as soon as they are received from the driver.
- Driving adapters (FastAPI endpoints) should expose streaming responses using `StreamingResponse` (or SSE) and must support backpressure when applicable.
- For non-streaming endpoints, adapters should still enforce `max_rows` and pagination to avoid memory spikes.

## 5. Security & Secrets

- DB credentials and external API keys must be stored in a dedicated secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager) and referenced by `config` via secret URIs.
- Principle of least privilege: connectors should use database users with minimized permissions (read-only roles unless admin workflows require otherwise).
- All adapter network egress must be reviewed; restrict outbound access where possible and use VPC peering/private endpoints for cloud DBs.

## 6. Observability & Testing

- Metrics: connection counts, query latency, rows streamed, error rates.
- Tracing: add OpenTelemetry spans around query execution and adapter calls.
- Logging: adapters must add structured logs with `query_id`, `adapter`, `duration_ms`, and `row_count`.
- Testing: provide unit tests for domain and application layers, and integration tests for each adapter (containerized DB instances or local emulators). Include contract tests that validate `DatabasePort` behavior across adapters.

## 7. Recommended Libraries & Patterns

- Oracle: `oracledb` (or `cx_Oracle`) with SQLAlchemy dialect when convenient.
- ClickHouse: `clickhouse-driver` or `clickhouse-sqlalchemy`.
- Databricks: use `databricks-sql-connector` or the JDBC/ODBC endpoint; prefer the official connector when available.
- Use `SQLAlchemy` for query templating and safety where practical, but keep adapter responsibilities clear.
- Use `pydantic` for config models and input validation.

## 8. Deployment & Scaling

- Run the API and connectors in containerized services behind an autoscaling group (Kubernetes, ECS).
- For long-running or heavy queries, use background workers (Celery, RQ) with result storage in Redis or object storage and notify via events.
- Add caching for expensive, repeatable queries (Redis or memcached) with TTLs and cache invalidation strategies.

## 9. Example: minimal adapter skeleton

```python
class DatabasePort(ABC):
	def connect(self) -> None: ...
	def close(self) -> None: ...
	def execute_query_stream(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> Iterator[Mapping[str, Any]]: ...
	def fetch_schema(self, table: str) -> Mapping[str, "UniversalDataType"]: ...

class OracleConnector(DatabasePort):
	def connect(self):
		# initialize driver connection pool
		pass

	def execute_query_stream(self, sql, params=None):
		# yield rows as dictionaries
		yield from []
```

## 10. Operational Checklist (pre-release)
- Integration tests pass for each adapter.
- Secrets configured and validated in staging.
- Metrics & tracing enabled and dashboards created.
- Security review of database permissions completed.

