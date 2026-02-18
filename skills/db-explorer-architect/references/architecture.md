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

- `connect() -> None` : Establish connections in **read-only mode**; raise `ConfigurationError` if a read-only connection cannot be guaranteed.
- `close() -> None` : Cleanly close resources.
- `execute_query_stream(sql: str, params: Optional[Mapping[str, Any]] = None) -> Iterator[Mapping[str, Any]]` : Stream rows as dictionaries (generator/yield).
- `fetch_schema(table: str) -> Mapping[str, UniversalDataType]` : Return canonical column types.
- `execute_safe_read(sql: str, params: Optional[Mapping[str, Any]] = None, max_rows: int = 1000) -> List[Mapping[str, Any]]` : Convenience method that enforces limits and read-only checks.

Behavioral requirements:
- **Strict read-only enforcement**: before executing any SQL statement, `execute_safe_read` and `execute_query_stream` must parse the statement and raise `ReadOnlyViolationError` if any of the following keywords are detected at the statement level: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `MERGE`, `REPLACE`. This check must happen **before** the query is sent to the database driver.
- Where the database driver supports it, connections must also be opened with a read-only session flag (e.g., `SET TRANSACTION READ ONLY` for Oracle, `readonly=True` for psycopg2, or a DB user restricted to `SELECT` / `SHOW` privileges only).
- Adapters must normalize provider-specific types into `UniversalDataType`.
- Errors must be converted into a common exception hierarchy (e.g., `ConnectorError`, `TransientError`, `ReadOnlyViolationError`) for the application layer to handle.

## 4. CleaningEngine (Application Layer)

The `CleaningEngine` lives in `src/application/cleaning_engine.py` and is responsible for all in-memory data transformations **after** raw rows have been fetched by a `DatabasePort`. It must never issue additional database calls.

### 4.1 Data Flow

```
API (FastAPI)
    │  receives QueryRequest + CleaningConfig
    ▼
DataService
    │  calls DatabasePort.execute_safe_read(sql) → raw rows
    ▼
CleaningEngine.apply(raw_rows, config) → List[UniversalRow]
    │  normalization → deduplication → type casting → rule application
    ▼
API
    │  serialises List[UniversalRow] to JSON
    ▼
Frontend (React)
    │  always receives UniversalFormat — consistent schema regardless of source DB
```

### 4.2 CleaningEngine Responsibilities

| Responsibility | Description |
| :--- | :--- |
| **Normalization** | Standardise string encoding (UTF-8), strip leading/trailing whitespace, unify `NULL`-like sentinel values (`""`, `"N/A"`, `"null"`) to `None`. |
| **Deduplication** | Remove exact-duplicate rows (all column values identical) before returning the result set. |
| **Type Casting** | Map the provider-specific raw type to the canonical `UniversalDataType` defined in the domain layer. |
| **Rule Application** | Apply optional per-request `CleaningConfig` rules (hide nulls, date format override, column aliasing, type override). |

### 4.3 UniversalRow / UniversalFormat

Every row returned by `CleaningEngine` must conform to `UniversalRow`:

```python
@dataclass
class UniversalCell:
    column: str
    type: UniversalDataType
    value: Any  # already cast to the Python equivalent of UniversalDataType

UniversalRow = list[UniversalCell]
```

The API serialises `List[UniversalRow]` to a JSON array of objects with keys `column`, `type`, and `value`.

### 4.4 CleaningConfig (user-defined rules)

`CleaningConfig` is passed by the frontend along with the SQL query and contains optional per-request cleaning rules:

```python
class CleaningConfig(BaseModel):
    hide_null_values: bool = False          # exclude cells / rows where value is None
    date_format: str = "ISO8601"            # normalise all date/timestamp columns
    trim_strings: bool = True               # strip whitespace from string columns
    column_aliases: dict[str, str] = {}     # rename columns in the response
    type_overrides: dict[str, UniversalDataType] = {}  # force column types
```

## 5. Streaming & Transport Contract

- Streaming query execution (`execute_query_stream`) must yield rows as soon as they are received from the driver.
- Driving adapters (FastAPI endpoints) should expose streaming responses using `StreamingResponse` (or SSE) and must support backpressure when applicable.
- For non-streaming endpoints, adapters should still enforce `max_rows` and pagination to avoid memory spikes.

## 6. Security & Secrets

- DB credentials and external API keys must be stored in a dedicated secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager) and referenced by `config` via secret URIs.
- Principle of least privilege: connectors should use database users with minimized permissions (read-only roles unless admin workflows require otherwise).
- All adapter network egress must be reviewed; restrict outbound access where possible and use VPC peering/private endpoints for cloud DBs.

## 7. Observability & Testing

- Metrics: connection counts, query latency, rows streamed, error rates.
- Tracing: add OpenTelemetry spans around query execution and adapter calls.
- Logging: adapters must add structured logs with `query_id`, `adapter`, `duration_ms`, and `row_count`.
- Testing: provide unit tests for domain and application layers, and integration tests for each adapter (containerized DB instances or local emulators). Include contract tests that validate `DatabasePort` behavior across adapters.

## 8. Recommended Libraries & Patterns

- Oracle: `oracledb` (or `cx_Oracle`) with SQLAlchemy dialect when convenient.
- ClickHouse: `clickhouse-driver` or `clickhouse-sqlalchemy`.
- Databricks: use `databricks-sql-connector` or the JDBC/ODBC endpoint; prefer the official connector when available.
- Use `SQLAlchemy` for query templating and safety where practical, but keep adapter responsibilities clear.
- Use `pydantic` for config models and input validation.

## 9. Deployment & Scaling

- Run the API and connectors in containerized services behind an autoscaling group (Kubernetes, ECS).
- For long-running or heavy queries, use background workers (Celery, RQ) with result storage in Redis or object storage and notify via events.
- Add caching for expensive, repeatable queries (Redis or memcached) with TTLs and cache invalidation strategies.

## 10. Example: minimal adapter skeleton

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

## 11. Operational Checklist (pre-release)
- Integration tests pass for each adapter.
- Secrets configured and validated in staging.
- Metrics & tracing enabled and dashboards created.
- Security review of database permissions completed.

