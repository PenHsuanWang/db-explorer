# Python Coding Standards for Database Explorer

## Overview
This document defines the Python coding standards, best practices, and quality requirements for the Database Explorer project. All code must adhere to these standards to ensure maintainability, reliability, and security.

## Code Style & Formatting

### PEP 8 Compliance
All Python code must follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines.

### Black Formatter
- **Tool**: Black (The Uncompromising Code Formatter)
- **Line Length**: 100 characters
- **Configuration**: See `pyproject.toml.template`
- **Usage**: `black src/ tests/ --line-length 100`

**Example:**
```python
# Good: Black-formatted code
def fetch_table_metadata(
    connector: DatabasePort, table_name: str, include_indexes: bool = False
) -> dict[str, Any]:
    """Fetch metadata for a database table."""
    return connector.fetch_schema(table_name)


# Bad: Inconsistent formatting
def fetch_table_metadata(connector: DatabasePort,table_name:str,include_indexes:bool=False)->dict[str,Any]:
    """Fetch metadata for a database table."""
    return connector.fetch_schema(table_name)
```

### Import Sorting
- **Tool**: isort
- **Profile**: black (for compatibility)
- **Configuration**: See `pyproject.toml.template`
- **Usage**: `isort src/ tests/ --profile black`

**Example:**
```python
# Good: Properly sorted imports
import os
import sys
from pathlib import Path
from typing import Any, Iterator, Optional

from pydantic import BaseModel
from sqlalchemy import create_engine

from src.core.domain.types import UniversalDataType
from src.core.ports.database import DatabasePort

# Bad: Random import order
from src.core.ports.database import DatabasePort
import sys
from pydantic import BaseModel
from typing import Any, Iterator, Optional
import os
```

### Linting
- **Tool**: Ruff (Fast Python Linter)
- **Rules**: pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade
- **Configuration**: See `pyproject.toml.template`
- **Usage**: `ruff check src/ tests/`

## Type Hinting

### Modern Python Type Syntax (PEP 484, 585, 604)
Use modern Python 3.10+ type syntax for all type hints.

**Example:**
```python
# Good: Modern Python 3.10+ syntax
from typing import Any

def execute_query(
    sql: str,
    params: dict[str, Any] | None = None,
    max_rows: int = 1000,
) -> list[dict[str, Any]]:
    """Execute a query and return results."""
    pass


# Bad: Old-style Optional and typing generics
from typing import Optional, Dict, List, Any

def execute_query(
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    max_rows: int = 1000,
) -> List[Dict[str, Any]]:
    """Execute a query and return results."""
    pass
```

### Type Hints Requirements
- **Required**: All public functions, methods, and class attributes
- **Optional**: Private functions (prefixed with `_`) may omit type hints
- **Strict Mode**: Use `mypy --strict` for type checking

**Example:**
```python
# Good: Complete type hints
from abc import ABC, abstractmethod
from typing import Any, Iterator

class DatabasePort(ABC):
    """Abstract interface for database adapters."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Stream query results as dictionaries."""
        pass


# Bad: Missing type hints
class DatabasePort(ABC):
    def connect(self):
        pass
    
    def execute_query_stream(self, sql, params=None):
        pass
```

### Mypy Configuration
- **Mode**: Strict
- **Requirements**: `warn_return_any`, `warn_unused_configs`, `disallow_untyped_defs`
- **Configuration**: See `pyproject.toml.template`
- **Usage**: `mypy src/ --strict`

## Docstrings

### Google-Style Docstrings (PEP 257)
All public modules, classes, functions, and methods must have docstrings in Google style.

**Complete Example:**
```python
from typing import Any, Iterator


def execute_query_stream(
    sql: str,
    params: dict[str, Any] | None = None,
    max_rows: int = 1000,
) -> Iterator[dict[str, Any]]:
    """Stream query results row by row.
    
    This function executes a SQL query and yields results as they are
    fetched from the database, providing memory-efficient access to
    large result sets.
    
    Args:
        sql: SQL query string to execute. Must be a SELECT statement.
        params: Optional dictionary of query parameters for
            parameterized queries. Defaults to None.
        max_rows: Maximum number of rows to return. Prevents
            unbounded memory usage. Defaults to 1000.
    
    Returns:
        Iterator yielding dictionaries representing rows, where
        keys are column names and values are column values.
    
    Raises:
        ValueError: If sql is not a SELECT statement.
        ConnectorError: If database connection fails.
        QueryExecutionError: If query execution fails.
    
    Examples:
        >>> for row in execute_query_stream("SELECT * FROM users LIMIT 10"):
        ...     print(row["name"])
        Alice
        Bob
        
        >>> params = {"min_age": 18}
        >>> query = "SELECT * FROM users WHERE age >= :min_age"
        >>> for row in execute_query_stream(query, params):
        ...     print(row)
    """
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    
    # Implementation here
    yield from []


class OracleConnector:
    """Oracle database adapter implementing DatabasePort.
    
    This adapter provides streaming query execution for Oracle databases
    using the oracledb driver. It enforces read-only access by default
    and normalizes Oracle-specific types to UniversalDataType.
    
    Attributes:
        config: Connection configuration with host, port, service name.
        connection: Active database connection (None until connect() called).
        
    Examples:
        >>> config = OracleConfig(host="localhost", port=1521, service="ORCL")
        >>> connector = OracleConnector(config)
        >>> connector.connect()
        >>> try:
        ...     for row in connector.execute_query_stream("SELECT 1 FROM DUAL"):
        ...         print(row)
        ... finally:
        ...     connector.close()
    """
    
    def __init__(self, config: "OracleConfig") -> None:
        """Initialize Oracle connector with configuration.
        
        Args:
            config: Oracle connection configuration.
        """
        self.config = config
        self.connection = None
```

**Bad Example:**
```python
# Bad: Missing or incomplete docstrings
def execute_query_stream(sql, params=None, max_rows=1000):
    # Executes query
    pass


class OracleConnector:
    # Oracle adapter
    def __init__(self, config):
        self.config = config
```

## Error Handling Best Practices

### Custom Exception Hierarchy
Define a clear exception hierarchy for domain-specific errors.

**Example:**
```python
# Good: Clear exception hierarchy
class DatabaseExplorerError(Exception):
    """Base exception for all Database Explorer errors."""
    pass


class ConnectorError(DatabaseExplorerError):
    """Base exception for connector-related errors."""
    pass


class TransientError(ConnectorError):
    """Temporary error that may succeed on retry."""
    pass


class ConfigurationError(DatabaseExplorerError):
    """Configuration validation error."""
    pass


class QueryExecutionError(ConnectorError):
    """Query execution failed."""
    
    def __init__(self, query: str, original_error: Exception) -> None:
        self.query = query
        self.original_error = original_error
        super().__init__(f"Query failed: {query[:100]}...")


# Usage
try:
    results = connector.execute_query_stream(sql)
except TransientError as e:
    # Retry logic
    logger.warning(f"Transient error, retrying: {e}")
except QueryExecutionError as e:
    # Log and propagate
    logger.error(f"Query failed: {e.query}", exc_info=True)
    raise
```

### Context Managers for Resource Management
Always use context managers for resource cleanup.

**Example:**
```python
# Good: Context manager ensures cleanup
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def database_connection(config: dict[str, Any]) -> Iterator[DatabasePort]:
    """Context manager for database connections.
    
    Args:
        config: Database connection configuration.
        
    Yields:
        Connected DatabasePort instance.
    """
    connector = ConnectorFactory.create(config)
    try:
        connector.connect()
        yield connector
    finally:
        connector.close()


# Usage
with database_connection(config) as conn:
    for row in conn.execute_query_stream("SELECT * FROM users"):
        process_row(row)


# Bad: Manual resource management
connector = ConnectorFactory.create(config)
connector.connect()
try:
    for row in connector.execute_query_stream("SELECT * FROM users"):
        process_row(row)
finally:
    connector.close()
```

### Error Propagation Patterns
Preserve error context while converting to domain exceptions.

**Example:**
```python
# Good: Preserve context with 'from' clause
import oracledb


def connect(self) -> None:
    """Establish Oracle database connection."""
    try:
        self.connection = oracledb.connect(
            user=self.config.user,
            password=self.config.password,
            dsn=self.config.dsn,
        )
    except oracledb.DatabaseError as e:
        raise ConnectorError(f"Failed to connect to Oracle: {e}") from e


# Bad: Loses original exception context
def connect(self) -> None:
    try:
        self.connection = oracledb.connect(...)
    except Exception as e:
        raise ConnectorError("Connection failed")
```

## SOLID Principles Application

### Single Responsibility Principle (SRP)
Each class should have one reason to change.

**Example:**
```python
# Good: Separate responsibilities
class QueryParser:
    """Parse and validate SQL queries."""
    
    def parse(self, sql: str) -> "ParsedQuery":
        """Parse SQL into structured format."""
        pass
    
    def validate(self, query: "ParsedQuery") -> bool:
        """Validate parsed query for safety."""
        pass


class QueryExecutor:
    """Execute validated queries."""
    
    def execute(self, query: "ParsedQuery") -> Iterator[dict[str, Any]]:
        """Execute query and stream results."""
        pass


# Bad: Multiple responsibilities in one class
class QueryProcessor:
    def parse(self, sql: str) -> "ParsedQuery":
        pass
    
    def validate(self, query: "ParsedQuery") -> bool:
        pass
    
    def execute(self, query: "ParsedQuery") -> Iterator[dict[str, Any]]:
        pass
    
    def log_execution(self, query: "ParsedQuery") -> None:
        pass
    
    def cache_results(self, results: list[dict[str, Any]]) -> None:
        pass
```

### Open/Closed Principle (OCP)
Use Abstract Base Classes for extension.

**Example:**
```python
# Good: Open for extension via ABC
from abc import ABC, abstractmethod


class DatabasePort(ABC):
    """Abstract interface for database adapters."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection."""
        pass
    
    @abstractmethod
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Stream query results."""
        pass


class OracleConnector(DatabasePort):
    """Oracle implementation."""
    
    def connect(self) -> None:
        # Oracle-specific implementation
        pass
    
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        # Oracle-specific implementation
        yield from []
```

### Liskov Substitution Principle (LSP)
All DatabasePort implementations must be interchangeable.

**Example:**
```python
# Good: Consistent interface across implementations
def process_query(connector: DatabasePort, sql: str) -> list[dict[str, Any]]:
    """Process query using any DatabasePort implementation."""
    return list(connector.execute_query_stream(sql))


# Works with any connector
oracle_conn = OracleConnector(config)
results = process_query(oracle_conn, "SELECT * FROM users")

clickhouse_conn = ClickHouseConnector(config)
results = process_query(clickhouse_conn, "SELECT * FROM users")
```

### Interface Segregation Principle (ISP)
Create focused interfaces instead of monolithic ones.

**Example:**
```python
# Good: Focused interfaces
class Connectable(ABC):
    """Interface for connection management."""
    
    @abstractmethod
    def connect(self) -> None:
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass


class Queryable(ABC):
    """Interface for query execution."""
    
    @abstractmethod
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        pass


class SchemaInspectable(ABC):
    """Interface for schema inspection."""
    
    @abstractmethod
    def fetch_schema(self, table: str) -> dict[str, "UniversalDataType"]:
        pass


# DatabasePort combines these focused interfaces
class DatabasePort(Connectable, Queryable, SchemaInspectable):
    """Complete database adapter interface."""
    pass
```

### Dependency Inversion Principle (DIP)
Depend on abstractions, not concrete implementations.

**Example:**
```python
# Good: Depends on abstraction (DatabasePort)
class QueryService:
    """Application service for query execution."""
    
    def __init__(self, connector: DatabasePort) -> None:
        """Initialize with DatabasePort interface.
        
        Args:
            connector: Any DatabasePort implementation.
        """
        self.connector = connector
    
    def execute_safe_query(self, sql: str) -> list[dict[str, Any]]:
        """Execute query safely with limits."""
        return list(self.connector.execute_query_stream(sql))


# Bad: Depends on concrete implementation
class QueryService:
    def __init__(self, connector: OracleConnector) -> None:
        self.connector = connector
```

## Testing Requirements

### Minimum Coverage Target
- **Target**: 80% code coverage
- **Tool**: pytest with coverage plugin
- **Configuration**: See `pyproject.toml.template`
- **Usage**: `pytest --cov=src --cov-report=term-missing`

### Testing Framework: pytest
Use pytest for all testing with fixtures for setup/teardown.

**Example:**
```python
import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_connector():
    """Provide mocked database connector."""
    connector = Mock(spec=DatabasePort)
    connector.execute_query_stream.return_value = iter([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ])
    return connector


def test_query_service(mock_connector):
    """Test QueryService with mocked connector."""
    service = QueryService(mock_connector)
    results = service.execute_safe_query("SELECT * FROM users")
    
    assert len(results) == 2
    assert results[0]["name"] == "Alice"
    mock_connector.execute_query_stream.assert_called_once()
```

### Mocking
Use `unittest.mock` or `pytest-mock` for dependencies.

### Unit Tests
Test individual components in isolation.

**Example:**
```python
def test_query_parser_validates_select():
    """Test parser validates SELECT queries."""
    parser = QueryParser()
    query = parser.parse("SELECT * FROM users")
    assert parser.validate(query) is True


def test_query_parser_rejects_delete():
    """Test parser rejects DELETE queries."""
    parser = QueryParser()
    with pytest.raises(ValueError, match="Only SELECT"):
        parser.parse("DELETE FROM users")
```

### Integration Tests
Test adapters against real databases using testcontainers.

**Example:**
```python
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def postgres_container():
    """Start PostgreSQL container for tests."""
    with PostgresContainer("postgres:15") as postgres:
        yield {
            "host": postgres.get_container_host_ip(),
            "port": postgres.get_exposed_port(5432),
            "database": postgres.POSTGRES_DB,
        }


@pytest.mark.integration
def test_postgres_connector_integration(postgres_container):
    """Integration test for PostgreSQL connector."""
    connector = PostgresConnector(postgres_container)
    connector.connect()
    
    try:
        results = list(connector.execute_query_stream("SELECT 1 as num"))
        assert len(results) == 1
        assert results[0]["num"] == 1
    finally:
        connector.close()
```

### Contract Tests
Use parametrize to test interface compliance.

**Example:**
```python
@pytest.mark.parametrize("connector_class", [
    OracleConnector,
    ClickHouseConnector,
    DatabricksConnector,
])
def test_database_port_contract(connector_class):
    """Verify all connectors implement DatabasePort."""
    assert issubclass(connector_class, DatabasePort)
    
    required_methods = ["connect", "close", "execute_query_stream", "fetch_schema"]
    for method in required_methods:
        assert hasattr(connector_class, method)
        assert callable(getattr(connector_class, method))
```

## Performance Best Practices

### Lazy Evaluation with Generators
Use generators for streaming data processing.

**Example:**
```python
# Good: Generator for memory-efficient streaming
def execute_query_stream(sql: str) -> Iterator[dict[str, Any]]:
    """Stream results without loading all into memory."""
    cursor = connection.cursor()
    cursor.execute(sql)
    
    for row in cursor:
        yield dict(zip([col[0] for col in cursor.description], row))


# Bad: Load entire result set into memory
def execute_query(sql: str) -> list[dict[str, Any]]:
    cursor = connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()  # Loads all results into memory
```

### Connection Pooling
Reuse connections for better performance.

**Example:**
```python
# Good: Connection pool
from sqlalchemy.pool import QueuePool


class PooledConnector:
    """Connector with connection pooling."""
    
    def __init__(self, config: dict[str, Any]) -> None:
        self.pool = QueuePool(
            lambda: create_connection(config),
            max_overflow=10,
            pool_size=5,
            timeout=30,
        )
    
    def get_connection(self):
        """Get connection from pool."""
        return self.pool.connect()
```

### Batch Operations
Process records in batches for efficiency.

**Example:**
```python
# Good: Batch processing
def process_large_result_set(sql: str, batch_size: int = 100) -> None:
    """Process results in batches."""
    batch = []
    for row in execute_query_stream(sql):
        batch.append(row)
        if len(batch) >= batch_size:
            process_batch(batch)
            batch = []
    
    if batch:  # Process remaining items
        process_batch(batch)
```

### Future async/await Considerations
Design for potential async migration.

**Example:**
```python
# Future: Async query execution
async def execute_query_stream_async(
    sql: str, params: dict[str, Any] | None = None
) -> AsyncIterator[dict[str, Any]]:
    """Async streaming query execution."""
    async with async_connection() as conn:
        async for row in conn.execute(sql, params):
            yield row
```

## Security Coding Standards

### No Secrets in Code
Never hardcode credentials or secrets.

**Example:**
```python
# Good: Load secrets from environment or secrets manager
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration loaded from environment."""
    
    host: str
    port: int
    username: str
    password: str  # Loaded from environment, not hardcoded
    
    class Config:
        env_prefix = "DB_"


# Usage: Load from environment
config = DatabaseConfig()  # Reads DB_HOST, DB_PORT, etc.


# Bad: Hardcoded credentials
config = {
    "host": "prod-db.example.com",
    "username": "admin",
    "password": "SuperSecret123!",  # NEVER DO THIS
}
```

### Parameterized Queries (SQL Injection Prevention)
Always use parameterized queries, never string concatenation.

**Example:**
```python
# Good: Parameterized query
def get_user_by_id(user_id: int) -> dict[str, Any]:
    """Fetch user by ID using parameterized query."""
    sql = "SELECT * FROM users WHERE id = :user_id"
    params = {"user_id": user_id}
    return next(execute_query_stream(sql, params))


# Bad: String concatenation (SQL INJECTION VULNERABLE!)
def get_user_by_id(user_id: int) -> dict[str, Any]:
    sql = f"SELECT * FROM users WHERE id = {user_id}"  # VULNERABLE!
    return next(execute_query_stream(sql))


# Very Bad: User input concatenation (CRITICAL VULNERABILITY!)
def search_users(search_term: str) -> list[dict[str, Any]]:
    sql = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"  # CRITICAL!
    return list(execute_query_stream(sql))
```

### Least Privilege Database Access
Use read-only database users by default.

**Example:**
```python
# Good: Read-only connection by default
class DatabaseConfig(BaseSettings):
    """Database configuration with security defaults."""
    
    read_only: bool = True  # Default to read-only
    allowed_operations: list[str] = ["SELECT"]  # Whitelist operations


def validate_query(sql: str, config: DatabaseConfig) -> None:
    """Validate query against allowed operations."""
    sql_upper = sql.strip().upper()
    
    if config.read_only:
        if not any(sql_upper.startswith(op) for op in config.allowed_operations):
            raise SecurityError(f"Operation not allowed in read-only mode: {sql[:50]}")
```

### Audit Logging Requirements
Log all database access for security audit trail.

**Example:**
```python
# Good: Comprehensive audit logging
import structlog

logger = structlog.get_logger()


def execute_query_stream_with_audit(
    sql: str, params: dict[str, Any] | None = None, user_id: str | None = None
) -> Iterator[dict[str, Any]]:
    """Execute query with audit logging."""
    query_id = str(uuid.uuid4())
    
    logger.info(
        "query_started",
        query_id=query_id,
        user_id=user_id,
        sql=sql[:200],  # Truncate for logging
        params=params,
    )
    
    try:
        row_count = 0
        start_time = time.time()
        
        for row in execute_query_stream(sql, params):
            row_count += 1
            yield row
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "query_completed",
            query_id=query_id,
            row_count=row_count,
            duration_ms=duration_ms,
        )
    except Exception as e:
        logger.error(
            "query_failed",
            query_id=query_id,
            error=str(e),
            exc_info=True,
        )
        raise
```

## Logging Standards

### Structured Logging with structlog
Use structured logging for better observability.

**Configuration:**
```python
import structlog


# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Log Levels
Use appropriate log levels for different scenarios.

**Example:**
```python
import structlog

logger = structlog.get_logger()

# DEBUG: Detailed diagnostic information
logger.debug("parsing_query", sql=sql, params=params)

# INFO: Normal operational events
logger.info("connection_established", adapter="oracle", host=config.host)

# WARNING: Unexpected but handled situations
logger.warning("slow_query_detected", duration_ms=5000, sql=sql[:100])

# ERROR: Error conditions that need attention
logger.error("connection_failed", adapter="oracle", error=str(e), exc_info=True)

# CRITICAL: System-wide failures
logger.critical("all_connections_exhausted", pool_size=10, waiting_requests=50)
```

### Required Context Fields
Include these fields in all database operation logs.

**Example:**
```python
# Required fields for query logging
logger.info(
    "query_executed",
    query_id=query_id,          # Unique query identifier
    adapter_name="oracle",       # Database adapter name
    duration_ms=250.5,          # Query execution time
    row_count=42,               # Number of rows returned
    sql=sql[:200],              # Truncated SQL (prevent log spam)
    user_id=user_id,            # User who executed query
    timestamp=datetime.utcnow().isoformat(),
)
```

### Complete Logging Example
```python
import structlog
import time
import uuid
from typing import Any, Iterator


logger = structlog.get_logger(__name__)


def execute_query_with_logging(
    connector: DatabasePort,
    sql: str,
    params: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Execute query with comprehensive logging.
    
    Args:
        connector: Database connector instance.
        sql: SQL query to execute.
        params: Query parameters.
        user_id: User executing the query.
        
    Yields:
        Query result rows as dictionaries.
    """
    query_id = str(uuid.uuid4())
    start_time = time.time()
    row_count = 0
    
    log_context = {
        "query_id": query_id,
        "adapter_name": connector.__class__.__name__,
        "sql": sql[:200],
        "user_id": user_id,
    }
    
    logger.info("query_started", **log_context)
    
    try:
        for row in connector.execute_query_stream(sql, params):
            row_count += 1
            yield row
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "query_completed",
            **log_context,
            duration_ms=duration_ms,
            row_count=row_count,
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "query_failed",
            **log_context,
            duration_ms=duration_ms,
            error_type=e.__class__.__name__,
            error_message=str(e),
            exc_info=True,
        )
        raise
```

## Dependency Management

### Lock Files
Always commit lock files for reproducible builds.

**Tools:**
- **Poetry**: `poetry.lock`
- **Pip**: `requirements.lock` (generated with `pip-compile`)

**Example with Poetry:**
```bash
# Install dependencies
poetry install

# Add new dependency
poetry add requests

# Update dependencies
poetry update

# Commit poetry.lock
git add poetry.lock
git commit -m "Update dependencies"
```

### Version Pinning in Production
Pin exact versions in production for stability.

**Example:**
```toml
# pyproject.toml - For development (flexible)
[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.109.0"
pydantic = "^2.0"

# requirements.txt - For production (pinned)
fastapi==0.109.2
pydantic==2.5.3
pydantic-core==2.14.6
```

### Security Scanning
Regularly scan dependencies for vulnerabilities.

**Tools:**
- **safety**: Check Python dependencies for known vulnerabilities
- **pip-audit**: Audit Python packages for security issues

**Example:**
```bash
# Using safety
pip install safety
safety check

# Using pip-audit
pip install pip-audit
pip-audit

# In CI/CD pipeline
safety check --json | python -m json.tool
```

## Summary Checklist

Before merging any code, ensure:

- [ ] Code formatted with Black (100 char line length)
- [ ] Imports sorted with isort
- [ ] All linting checks pass (ruff)
- [ ] Type hints on all public functions (mypy --strict passes)
- [ ] Google-style docstrings on all public APIs
- [ ] Custom exceptions used appropriately
- [ ] Resources managed with context managers
- [ ] SOLID principles followed
- [ ] Test coverage >= 80%
- [ ] pytest tests pass
- [ ] No hardcoded secrets
- [ ] Parameterized queries used
- [ ] Structured logging in place
- [ ] Security scan completed (safety/pip-audit)
- [ ] Lock files committed

## References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 585 - Type Hinting Generics In Standard Collections](https://peps.python.org/pep-0585/)
- [PEP 604 - Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [Black Code Style](https://black.readthedocs.io/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
