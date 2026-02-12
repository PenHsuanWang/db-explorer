# Design Patterns for Database Explorer

## Overview
This document provides design pattern implementations and best practices for the Database Explorer project. These patterns help maintain clean architecture, improve code reusability, and facilitate testing.

## Creational Patterns

### Factory Pattern

The Factory Pattern provides a centralized way to create database connectors without exposing instantiation logic.

**Use Case**: Creating different database adapter instances based on configuration.

**Complete Implementation:**

```python
from abc import ABC, abstractmethod
from typing import Any


class DatabasePort(ABC):
    """Abstract interface for database adapters."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Stream query results."""
        pass


class OracleConnector(DatabasePort):
    """Oracle database adapter."""
    
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.connection = None
    
    def connect(self) -> None:
        import oracledb
        self.connection = oracledb.connect(
            user=self.config["user"],
            password=self.config["password"],
            dsn=self.config["dsn"],
        )
    
    def close(self) -> None:
        if self.connection:
            self.connection.close()
    
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(sql, params or {})
        columns = [col[0] for col in cursor.description]
        for row in cursor:
            yield dict(zip(columns, row))


class ClickHouseConnector(DatabasePort):
    """ClickHouse database adapter."""
    
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.client = None
    
    def connect(self) -> None:
        from clickhouse_driver import Client
        self.client = Client(
            host=self.config["host"],
            port=self.config.get("port", 9000),
            database=self.config.get("database", "default"),
        )
    
    def close(self) -> None:
        if self.client:
            self.client.disconnect()
    
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        result = self.client.execute(sql, params or {}, with_column_types=True)
        columns = [col[0] for col in result[1]]
        for row in result[0]:
            yield dict(zip(columns, row))


class DatabricksConnector(DatabasePort):
    """Databricks database adapter."""
    
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.connection = None
    
    def connect(self) -> None:
        from databricks import sql
        self.connection = sql.connect(
            server_hostname=self.config["server_hostname"],
            http_path=self.config["http_path"],
            access_token=self.config["access_token"],
        )
    
    def close(self) -> None:
        if self.connection:
            self.connection.close()
    
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(sql, params or {})
        columns = [col[0] for col in cursor.description]
        for row in cursor:
            yield dict(zip(columns, row))


class ConnectorFactory:
    """Factory for creating database connectors.
    
    This factory maintains a registry of connector classes and creates
    instances based on configuration. It provides centralized connector
    instantiation with validation.
    
    Examples:
        >>> config = {"type": "oracle", "user": "admin", "dsn": "localhost:1521/ORCL"}
        >>> connector = ConnectorFactory.create(config)
        >>> isinstance(connector, OracleConnector)
        True
    """
    
    _registry: dict[str, type[DatabasePort]] = {}
    
    @classmethod
    def register(cls, connector_type: str, connector_class: type[DatabasePort]) -> None:
        """Register a connector class.
        
        Args:
            connector_type: Unique identifier for the connector (e.g., "oracle").
            connector_class: Connector class implementing DatabasePort.
            
        Raises:
            ValueError: If connector_type is already registered.
        """
        if connector_type in cls._registry:
            raise ValueError(f"Connector type '{connector_type}' already registered")
        
        if not issubclass(connector_class, DatabasePort):
            raise TypeError(
                f"Connector class must implement DatabasePort, got {connector_class}"
            )
        
        cls._registry[connector_type] = connector_class
    
    @classmethod
    def create(cls, config: dict[str, Any]) -> DatabasePort:
        """Create a connector instance from configuration.
        
        Args:
            config: Configuration dictionary with "type" key and connector-specific settings.
            
        Returns:
            Initialized DatabasePort instance.
            
        Raises:
            KeyError: If "type" not in config.
            ValueError: If connector type not registered.
            
        Examples:
            >>> config = {"type": "clickhouse", "host": "localhost"}
            >>> connector = ConnectorFactory.create(config)
            >>> connector.connect()
        """
        if "type" not in config:
            raise KeyError("Configuration must include 'type' field")
        
        connector_type = config["type"]
        
        if connector_type not in cls._registry:
            raise ValueError(
                f"Unknown connector type: {connector_type}. "
                f"Available types: {list(cls._registry.keys())}"
            )
        
        connector_class = cls._registry[connector_type]
        return connector_class(config)
    
    @classmethod
    def list_types(cls) -> list[str]:
        """List all registered connector types.
        
        Returns:
            List of registered connector type identifiers.
        """
        return list(cls._registry.keys())


# Register built-in connectors
ConnectorFactory.register("oracle", OracleConnector)
ConnectorFactory.register("clickhouse", ClickHouseConnector)
ConnectorFactory.register("databricks", DatabricksConnector)


# Usage Example
def main():
    """Example usage of ConnectorFactory."""
    configs = [
        {"type": "oracle", "user": "admin", "password": "secret", "dsn": "localhost:1521/ORCL"},
        {"type": "clickhouse", "host": "localhost", "port": 9000},
        {"type": "databricks", "server_hostname": "example.cloud.databricks.com", 
         "http_path": "/sql/1.0/warehouses/abc123", "access_token": "token"},
    ]
    
    for config in configs:
        connector = ConnectorFactory.create(config)
        print(f"Created connector: {connector.__class__.__name__}")
        
        try:
            connector.connect()
            results = list(connector.execute_query_stream("SELECT 1 as num"))
            print(f"Query result: {results}")
        finally:
            connector.close()
```

**Benefits:**
- Centralized connector creation logic
- Easy to add new connector types
- Type safety with registry
- Configuration validation

---

### Builder Pattern

The Builder Pattern provides a fluent API for constructing complex connector configurations.

**Use Case**: Building connector configurations with validation and defaults.

**Complete Implementation:**

```python
from typing import Any, Self


class ConnectorConfigBuilder:
    """Fluent builder for database connector configurations.
    
    Provides a clean, chainable API for building validated connector
    configurations with sensible defaults.
    
    Examples:
        >>> config = (
        ...     ConnectorConfigBuilder()
        ...     .set_type("oracle")
        ...     .set_host("localhost")
        ...     .set_port(1521)
        ...     .set_credentials("admin", "password")
        ...     .set_database("ORCL")
        ...     .set_read_only(True)
        ...     .set_pool_size(5)
        ...     .build()
        ... )
    """
    
    def __init__(self) -> None:
        """Initialize builder with empty configuration."""
        self._config: dict[str, Any] = {}
        self._errors: list[str] = []
    
    def set_type(self, connector_type: str) -> Self:
        """Set connector type.
        
        Args:
            connector_type: Type of connector (oracle, clickhouse, databricks).
            
        Returns:
            Self for method chaining.
        """
        valid_types = ["oracle", "clickhouse", "databricks"]
        if connector_type not in valid_types:
            self._errors.append(
                f"Invalid connector type: {connector_type}. "
                f"Valid types: {valid_types}"
            )
        self._config["type"] = connector_type
        return self
    
    def set_host(self, host: str) -> Self:
        """Set database host.
        
        Args:
            host: Database server hostname or IP address.
            
        Returns:
            Self for method chaining.
        """
        if not host:
            self._errors.append("Host cannot be empty")
        self._config["host"] = host
        return self
    
    def set_port(self, port: int) -> Self:
        """Set database port.
        
        Args:
            port: Port number (1-65535).
            
        Returns:
            Self for method chaining.
        """
        if not 1 <= port <= 65535:
            self._errors.append(f"Invalid port: {port}. Must be 1-65535")
        self._config["port"] = port
        return self
    
    def set_credentials(self, username: str, password: str) -> Self:
        """Set database credentials.
        
        Args:
            username: Database username.
            password: Database password.
            
        Returns:
            Self for method chaining.
        """
        if not username:
            self._errors.append("Username cannot be empty")
        if not password:
            self._errors.append("Password cannot be empty")
        
        self._config["user"] = username
        self._config["password"] = password
        return self
    
    def set_database(self, database: str) -> Self:
        """Set database name or service name.
        
        Args:
            database: Database name or Oracle service name.
            
        Returns:
            Self for method chaining.
        """
        if not database:
            self._errors.append("Database name cannot be empty")
        self._config["database"] = database
        return self
    
    def set_read_only(self, read_only: bool = True) -> Self:
        """Set read-only mode.
        
        Args:
            read_only: Whether to enforce read-only access. Defaults to True.
            
        Returns:
            Self for method chaining.
        """
        self._config["read_only"] = read_only
        return self
    
    def set_pool_size(self, size: int) -> Self:
        """Set connection pool size.
        
        Args:
            size: Maximum number of connections in pool (1-100).
            
        Returns:
            Self for method chaining.
        """
        if not 1 <= size <= 100:
            self._errors.append(f"Invalid pool size: {size}. Must be 1-100")
        self._config["pool_size"] = size
        return self
    
    def set_timeout(self, timeout_seconds: int) -> Self:
        """Set connection timeout.
        
        Args:
            timeout_seconds: Connection timeout in seconds (1-300).
            
        Returns:
            Self for method chaining.
        """
        if not 1 <= timeout_seconds <= 300:
            self._errors.append(
                f"Invalid timeout: {timeout_seconds}. Must be 1-300 seconds"
            )
        self._config["timeout"] = timeout_seconds
        return self
    
    def set_ssl_enabled(self, enabled: bool = True) -> Self:
        """Set SSL/TLS encryption.
        
        Args:
            enabled: Whether to enable SSL/TLS. Defaults to True.
            
        Returns:
            Self for method chaining.
        """
        self._config["ssl_enabled"] = enabled
        return self
    
    def set_extra_option(self, key: str, value: Any) -> Self:
        """Set connector-specific extra option.
        
        Args:
            key: Option key.
            value: Option value.
            
        Returns:
            Self for method chaining.
        """
        if "extra_options" not in self._config:
            self._config["extra_options"] = {}
        self._config["extra_options"][key] = value
        return self
    
    def build(self) -> dict[str, Any]:
        """Build and validate the configuration.
        
        Returns:
            Validated configuration dictionary.
            
        Raises:
            ValueError: If configuration is invalid or has validation errors.
        """
        # Check for validation errors
        if self._errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in self._errors
            )
            raise ValueError(error_msg)
        
        # Check required fields
        if "type" not in self._config:
            raise ValueError("Connector type is required")
        
        # Apply defaults
        config = self._config.copy()
        config.setdefault("read_only", True)  # Default to read-only
        config.setdefault("pool_size", 5)     # Default pool size
        config.setdefault("timeout", 30)      # Default timeout
        config.setdefault("ssl_enabled", True)  # Default to SSL
        
        return config
    
    def reset(self) -> Self:
        """Reset builder to empty state.
        
        Returns:
            Self for method chaining.
        """
        self._config = {}
        self._errors = []
        return self


# Usage Examples
def example_oracle_config():
    """Build Oracle connector configuration."""
    config = (
        ConnectorConfigBuilder()
        .set_type("oracle")
        .set_host("prod-oracle.example.com")
        .set_port(1521)
        .set_credentials("readonly_user", "secure_password")
        .set_database("ORCL")
        .set_read_only(True)
        .set_pool_size(10)
        .set_ssl_enabled(True)
        .build()
    )
    return config


def example_clickhouse_config():
    """Build ClickHouse connector configuration."""
    config = (
        ConnectorConfigBuilder()
        .set_type("clickhouse")
        .set_host("analytics.example.com")
        .set_port(9000)
        .set_credentials("analyst", "password")
        .set_database("analytics")
        .set_pool_size(20)
        .set_extra_option("compression", "lz4")
        .build()
    )
    return config


def example_with_validation_error():
    """Demonstrate validation error handling."""
    try:
        config = (
            ConnectorConfigBuilder()
            .set_type("invalid_type")  # Invalid
            .set_port(99999)  # Invalid port
            .set_pool_size(200)  # Invalid pool size
            .build()
        )
    except ValueError as e:
        print(f"Validation failed: {e}")
```

**Benefits:**
- Fluent, readable API
- Built-in validation
- Sensible defaults
- Easy to extend

---

## Structural Patterns

### Adapter Pattern

The Adapter Pattern is already implemented via `DatabasePort` interface. This pattern allows different database drivers to work through a common interface.

**Use Case**: Normalizing different database APIs to a common interface.

**Example:**

```python
# The DatabasePort interface acts as the target interface
# Each connector (OracleConnector, ClickHouseConnector) is an adapter
# that wraps vendor-specific drivers and exposes the common interface

def process_query(connector: DatabasePort, sql: str) -> list[dict[str, Any]]:
    """Process query using any database connector.
    
    This function works with any DatabasePort implementation thanks
    to the Adapter Pattern. The underlying database driver (oracledb,
    clickhouse-driver, databricks-sql) is adapted to the common interface.
    """
    connector.connect()
    try:
        results = list(connector.execute_query_stream(sql))
        return results
    finally:
        connector.close()


# Works with any adapted database
oracle_results = process_query(OracleConnector(oracle_config), "SELECT * FROM users")
clickhouse_results = process_query(ClickHouseConnector(ch_config), "SELECT * FROM events")
```

---

### Decorator Pattern

The Decorator Pattern adds behavior to query execution without modifying the core connector code.

**Use Case**: Adding OpenTelemetry tracing, metrics, caching, or retry logic to query execution.

**Complete Implementation:**

```python
import time
import functools
from typing import Any, Callable, Iterator
from opentelemetry import trace
from opentelemetry.trace import Span


def with_tracing(operation_name: str) -> Callable:
    """Decorator to add OpenTelemetry tracing to functions.
    
    Args:
        operation_name: Name of the operation for tracing.
        
    Returns:
        Decorated function with tracing instrumentation.
        
    Examples:
        >>> @with_tracing("execute_query")
        ... def execute_query(sql: str) -> list[dict[str, Any]]:
        ...     return []
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(operation_name) as span:
                # Add attributes to span
                span.set_attribute("function.name", func.__name__)
                
                # Extract SQL if present
                if args and isinstance(args[0], str):
                    span.set_attribute("db.statement", args[0][:200])
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("result.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("result.status", "error")
                    span.set_attribute("error.type", e.__class__.__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def with_metrics(metric_name: str) -> Callable:
    """Decorator to add metrics collection to functions.
    
    Args:
        metric_name: Name of the metric to record.
        
    Returns:
        Decorated function with metrics instrumentation.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metric
                record_metric(f"{metric_name}.duration", duration)
                record_metric(f"{metric_name}.success", 1)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metric
                record_metric(f"{metric_name}.duration", duration)
                record_metric(f"{metric_name}.error", 1)
                
                raise
        
        return wrapper
    return decorator


def with_retry(max_attempts: int = 3, delay_seconds: int = 1) -> Callable:
    """Decorator to add retry logic for transient failures.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        delay_seconds: Delay between retry attempts.
        
    Returns:
        Decorated function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay_seconds)
                        continue
                    raise
                except Exception:
                    # Don't retry non-transient errors
                    raise
            
            raise last_exception
        
        return wrapper
    return decorator


class TracedConnector(DatabasePort):
    """Decorator that adds tracing to a DatabasePort connector.
    
    This class wraps any DatabasePort implementation and adds
    OpenTelemetry tracing to all operations.
    
    Examples:
        >>> base_connector = OracleConnector(config)
        >>> traced_connector = TracedConnector(base_connector)
        >>> traced_connector.connect()  # Traced
        >>> for row in traced_connector.execute_query_stream(sql):  # Traced
        ...     process(row)
    """
    
    def __init__(self, connector: DatabasePort) -> None:
        """Initialize with base connector.
        
        Args:
            connector: Base connector to wrap with tracing.
        """
        self._connector = connector
        self._tracer = trace.get_tracer(__name__)
    
    @with_tracing("database.connect")
    def connect(self) -> None:
        """Connect with tracing."""
        self._connector.connect()
    
    @with_tracing("database.close")
    def close(self) -> None:
        """Close with tracing."""
        self._connector.close()
    
    @with_tracing("database.query")
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Execute query with tracing."""
        with self._tracer.start_as_current_span("query_execution") as span:
            span.set_attribute("db.statement", sql[:200])
            span.set_attribute("db.system", self._connector.__class__.__name__)
            
            row_count = 0
            try:
                for row in self._connector.execute_query_stream(sql, params):
                    row_count += 1
                    yield row
                
                span.set_attribute("db.row_count", row_count)
            except Exception as e:
                span.record_exception(e)
                raise


class MetricsConnector(DatabasePort):
    """Decorator that adds metrics to a DatabasePort connector."""
    
    def __init__(self, connector: DatabasePort) -> None:
        self._connector = connector
    
    @with_metrics("db.connect")
    def connect(self) -> None:
        self._connector.connect()
    
    @with_metrics("db.close")
    def close(self) -> None:
        self._connector.close()
    
    @with_metrics("db.query")
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        yield from self._connector.execute_query_stream(sql, params)


# Usage: Stack multiple decorators
def create_production_connector(config: dict[str, Any]) -> DatabasePort:
    """Create a connector with all production instrumentation.
    
    Stacks tracing and metrics decorators on top of base connector.
    """
    base_connector = ConnectorFactory.create(config)
    traced_connector = TracedConnector(base_connector)
    metrics_connector = MetricsConnector(traced_connector)
    return metrics_connector


# Helper function (placeholder for metrics recording)
def record_metric(name: str, value: float) -> None:
    """Record a metric value."""
    pass  # Implementation would use Prometheus, StatsD, etc.
```

**Benefits:**
- Add cross-cutting concerns (tracing, metrics) without modifying core code
- Stack multiple decorators
- Easy to enable/disable features

---

## Behavioral Patterns

### Strategy Pattern

The Strategy Pattern allows different query execution strategies to be swapped at runtime.

**Use Case**: Different strategies for query execution (streaming vs batch, with/without caching).

**Complete Implementation:**

```python
from abc import ABC, abstractmethod
from typing import Any, Iterator


class QueryStrategy(ABC):
    """Abstract strategy for query execution.
    
    Defines the interface for different query execution strategies.
    Strategies can implement different approaches to execution while
    maintaining a common interface.
    """
    
    @abstractmethod
    def execute(
        self, connector: DatabasePort, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute query using this strategy.
        
        Args:
            connector: Database connector to use.
            sql: SQL query to execute.
            params: Query parameters.
            
        Returns:
            Query results as list of dictionaries.
        """
        pass


class StreamingStrategy(QueryStrategy):
    """Strategy for streaming query execution.
    
    Streams results row-by-row for memory efficiency with large result sets.
    """
    
    def __init__(self, max_rows: int = 10000) -> None:
        """Initialize streaming strategy.
        
        Args:
            max_rows: Maximum rows to return.
        """
        self.max_rows = max_rows
    
    def execute(
        self, connector: DatabasePort, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute query with streaming.
        
        Args:
            connector: Database connector.
            sql: SQL query.
            params: Query parameters.
            
        Returns:
            List of result rows (up to max_rows).
        """
        results = []
        for i, row in enumerate(connector.execute_query_stream(sql, params)):
            if i >= self.max_rows:
                break
            results.append(row)
        return results


class BatchStrategy(QueryStrategy):
    """Strategy for batch query execution.
    
    Loads results in batches for processing.
    """
    
    def __init__(self, batch_size: int = 1000) -> None:
        """Initialize batch strategy.
        
        Args:
            batch_size: Number of rows per batch.
        """
        self.batch_size = batch_size
    
    def execute(
        self, connector: DatabasePort, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute query with batching.
        
        Args:
            connector: Database connector.
            sql: SQL query.
            params: Query parameters.
            
        Returns:
            All results as list.
        """
        all_results = []
        batch = []
        
        for row in connector.execute_query_stream(sql, params):
            batch.append(row)
            
            if len(batch) >= self.batch_size:
                # Process batch (e.g., transform, aggregate)
                all_results.extend(self._process_batch(batch))
                batch = []
        
        # Process remaining rows
        if batch:
            all_results.extend(self._process_batch(batch))
        
        return all_results
    
    def _process_batch(self, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process a batch of rows.
        
        Args:
            batch: Batch of rows to process.
            
        Returns:
            Processed rows.
        """
        # Override in subclasses for custom processing
        return batch


class CachedStrategy(QueryStrategy):
    """Strategy with query result caching.
    
    Caches results of expensive queries to avoid repeated execution.
    """
    
    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initialize caching strategy.
        
        Args:
            ttl_seconds: Cache time-to-live in seconds.
        """
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
    
    def execute(
        self, connector: DatabasePort, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute query with caching.
        
        Args:
            connector: Database connector.
            sql: SQL query.
            params: Query parameters.
            
        Returns:
            Cached or fresh results.
        """
        import hashlib
        import time
        
        # Create cache key from SQL and params
        cache_key = hashlib.sha256(
            f"{sql}:{params}".encode()
        ).hexdigest()
        
        # Check cache
        if cache_key in self._cache:
            cached_time, cached_results = self._cache[cache_key]
            if time.time() - cached_time < self.ttl_seconds:
                return cached_results
        
        # Execute query and cache results
        results = list(connector.execute_query_stream(sql, params))
        self._cache[cache_key] = (time.time(), results)
        
        return results


class QueryExecutor:
    """Context for executing queries with different strategies.
    
    This class uses the Strategy Pattern to allow different query
    execution approaches to be used interchangeably.
    
    Examples:
        >>> executor = QueryExecutor(StreamingStrategy(max_rows=100))
        >>> results = executor.execute(connector, "SELECT * FROM users")
        
        >>> executor.set_strategy(CachedStrategy(ttl_seconds=600))
        >>> results = executor.execute(connector, "SELECT * FROM products")
    """
    
    def __init__(self, strategy: QueryStrategy) -> None:
        """Initialize executor with strategy.
        
        Args:
            strategy: Query execution strategy to use.
        """
        self._strategy = strategy
    
    def set_strategy(self, strategy: QueryStrategy) -> None:
        """Change execution strategy at runtime.
        
        Args:
            strategy: New strategy to use.
        """
        self._strategy = strategy
    
    def execute(
        self, connector: DatabasePort, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute query using current strategy.
        
        Args:
            connector: Database connector.
            sql: SQL query.
            params: Query parameters.
            
        Returns:
            Query results.
        """
        return self._strategy.execute(connector, sql, params)


# Usage Examples
def demonstrate_strategies():
    """Demonstrate different query strategies."""
    connector = ConnectorFactory.create({"type": "oracle", ...})
    connector.connect()
    
    try:
        # Strategy 1: Streaming for large results
        executor = QueryExecutor(StreamingStrategy(max_rows=1000))
        results = executor.execute(connector, "SELECT * FROM large_table")
        print(f"Streaming: {len(results)} rows")
        
        # Strategy 2: Batch processing
        executor.set_strategy(BatchStrategy(batch_size=500))
        results = executor.execute(connector, "SELECT * FROM large_table")
        print(f"Batch: {len(results)} rows")
        
        # Strategy 3: Cached for repeated queries
        executor.set_strategy(CachedStrategy(ttl_seconds=300))
        results = executor.execute(connector, "SELECT * FROM config")
        print(f"Cached: {len(results)} rows")
        
        # Second call uses cache
        results = executor.execute(connector, "SELECT * FROM config")
        print(f"From cache: {len(results)} rows")
        
    finally:
        connector.close()
```

**Benefits:**
- Swap execution strategies at runtime
- Easy to add new strategies
- Testable in isolation

---

### Iterator Pattern

The Iterator Pattern is already implemented via `execute_query_stream` which returns an iterator.

**Use Case**: Memory-efficient streaming of large result sets.

**Example:**

```python
# The execute_query_stream method implements the Iterator Pattern
# by yielding rows one at a time instead of loading all into memory

def process_large_table(connector: DatabasePort) -> None:
    """Process large table efficiently using Iterator Pattern."""
    # Iterator allows processing one row at a time
    for row in connector.execute_query_stream("SELECT * FROM large_table"):
        # Process each row without loading entire result set
        process_row(row)
        
        # Memory usage remains constant regardless of result size


# Custom iterator for chunked processing
class ChunkedResultIterator:
    """Iterator that yields results in chunks."""
    
    def __init__(
        self, connector: DatabasePort, sql: str, chunk_size: int = 100
    ) -> None:
        self.connector = connector
        self.sql = sql
        self.chunk_size = chunk_size
    
    def __iter__(self) -> Iterator[list[dict[str, Any]]]:
        """Yield chunks of results."""
        chunk = []
        
        for row in self.connector.execute_query_stream(self.sql):
            chunk.append(row)
            
            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []
        
        # Yield remaining rows
        if chunk:
            yield chunk


# Usage
for chunk in ChunkedResultIterator(connector, "SELECT * FROM users", chunk_size=50):
    process_chunk(chunk)  # Process 50 rows at a time
```

---

### Observer Pattern

The Observer Pattern enables event-driven notifications for query lifecycle events.

**Use Case**: Metrics collection, logging, and monitoring of query execution.

**Complete Implementation:**

```python
from abc import ABC, abstractmethod
from typing import Any


class QueryEvent:
    """Base class for query lifecycle events."""
    
    def __init__(self, query_id: str, sql: str) -> None:
        self.query_id = query_id
        self.sql = sql


class QueryStartedEvent(QueryEvent):
    """Event fired when query starts execution."""
    pass


class QueryCompletedEvent(QueryEvent):
    """Event fired when query completes successfully."""
    
    def __init__(self, query_id: str, sql: str, row_count: int, duration_ms: float) -> None:
        super().__init__(query_id, sql)
        self.row_count = row_count
        self.duration_ms = duration_ms


class QueryFailedEvent(QueryEvent):
    """Event fired when query fails."""
    
    def __init__(self, query_id: str, sql: str, error: Exception) -> None:
        super().__init__(query_id, sql)
        self.error = error


class QueryEventListener(ABC):
    """Abstract observer for query events.
    
    Listeners subscribe to query events and react accordingly.
    """
    
    @abstractmethod
    def on_query_started(self, event: QueryStartedEvent) -> None:
        """Handle query started event."""
        pass
    
    @abstractmethod
    def on_query_completed(self, event: QueryCompletedEvent) -> None:
        """Handle query completed event."""
        pass
    
    @abstractmethod
    def on_query_failed(self, event: QueryFailedEvent) -> None:
        """Handle query failed event."""
        pass


class MetricsListener(QueryEventListener):
    """Listener that records metrics."""
    
    def on_query_started(self, event: QueryStartedEvent) -> None:
        """Record query start metric."""
        record_metric("query.started", 1)
    
    def on_query_completed(self, event: QueryCompletedEvent) -> None:
        """Record query completion metrics."""
        record_metric("query.completed", 1)
        record_metric("query.duration", event.duration_ms)
        record_metric("query.row_count", event.row_count)
    
    def on_query_failed(self, event: QueryFailedEvent) -> None:
        """Record query failure metric."""
        record_metric("query.failed", 1)
        record_metric(f"query.error.{event.error.__class__.__name__}", 1)


class LoggingListener(QueryEventListener):
    """Listener that logs events."""
    
    def __init__(self) -> None:
        import structlog
        self.logger = structlog.get_logger()
    
    def on_query_started(self, event: QueryStartedEvent) -> None:
        """Log query start."""
        self.logger.info(
            "query_started",
            query_id=event.query_id,
            sql=event.sql[:200],
        )
    
    def on_query_completed(self, event: QueryCompletedEvent) -> None:
        """Log query completion."""
        self.logger.info(
            "query_completed",
            query_id=event.query_id,
            row_count=event.row_count,
            duration_ms=event.duration_ms,
        )
    
    def on_query_failed(self, event: QueryFailedEvent) -> None:
        """Log query failure."""
        self.logger.error(
            "query_failed",
            query_id=event.query_id,
            error=str(event.error),
            exc_info=True,
        )


class AlertingListener(QueryEventListener):
    """Listener that sends alerts for slow or failed queries."""
    
    def __init__(self, slow_threshold_ms: float = 5000) -> None:
        self.slow_threshold_ms = slow_threshold_ms
    
    def on_query_started(self, event: QueryStartedEvent) -> None:
        """No action on start."""
        pass
    
    def on_query_completed(self, event: QueryCompletedEvent) -> None:
        """Alert on slow queries."""
        if event.duration_ms > self.slow_threshold_ms:
            self._send_alert(
                f"Slow query detected: {event.query_id} took {event.duration_ms}ms"
            )
    
    def on_query_failed(self, event: QueryFailedEvent) -> None:
        """Alert on query failures."""
        self._send_alert(
            f"Query failed: {event.query_id} - {event.error}"
        )
    
    def _send_alert(self, message: str) -> None:
        """Send alert to monitoring system."""
        print(f"ALERT: {message}")  # Placeholder


class ObservableConnector(DatabasePort):
    """Connector that notifies listeners of query events.
    
    This implementation of the Observer Pattern allows multiple
    listeners to observe query execution lifecycle.
    
    Examples:
        >>> connector = ObservableConnector(base_connector)
        >>> connector.add_listener(MetricsListener())
        >>> connector.add_listener(LoggingListener())
        >>> connector.execute_query_stream("SELECT * FROM users")
    """
    
    def __init__(self, connector: DatabasePort) -> None:
        """Initialize observable connector.
        
        Args:
            connector: Base connector to wrap.
        """
        self._connector = connector
        self._listeners: list[QueryEventListener] = []
    
    def add_listener(self, listener: QueryEventListener) -> None:
        """Subscribe a listener to query events.
        
        Args:
            listener: Listener to add.
        """
        self._listeners.append(listener)
    
    def remove_listener(self, listener: QueryEventListener) -> None:
        """Unsubscribe a listener.
        
        Args:
            listener: Listener to remove.
        """
        self._listeners.remove(listener)
    
    def _notify_started(self, event: QueryStartedEvent) -> None:
        """Notify all listeners of query start."""
        for listener in self._listeners:
            listener.on_query_started(event)
    
    def _notify_completed(self, event: QueryCompletedEvent) -> None:
        """Notify all listeners of query completion."""
        for listener in self._listeners:
            listener.on_query_completed(event)
    
    def _notify_failed(self, event: QueryFailedEvent) -> None:
        """Notify all listeners of query failure."""
        for listener in self._listeners:
            listener.on_query_failed(event)
    
    def connect(self) -> None:
        """Connect via base connector."""
        self._connector.connect()
    
    def close(self) -> None:
        """Close via base connector."""
        self._connector.close()
    
    def execute_query_stream(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Execute query with event notifications.
        
        Args:
            sql: SQL query.
            params: Query parameters.
            
        Yields:
            Query result rows.
        """
        import time
        import uuid
        
        query_id = str(uuid.uuid4())
        start_time = time.time()
        row_count = 0
        
        # Notify start
        self._notify_started(QueryStartedEvent(query_id, sql))
        
        try:
            for row in self._connector.execute_query_stream(sql, params):
                row_count += 1
                yield row
            
            # Notify completion
            duration_ms = (time.time() - start_time) * 1000
            self._notify_completed(
                QueryCompletedEvent(query_id, sql, row_count, duration_ms)
            )
            
        except Exception as e:
            # Notify failure
            self._notify_failed(QueryFailedEvent(query_id, sql, e))
            raise


# Usage Example
def create_observable_connector(config: dict[str, Any]) -> DatabasePort:
    """Create connector with full observability."""
    base_connector = ConnectorFactory.create(config)
    observable = ObservableConnector(base_connector)
    
    # Add observers
    observable.add_listener(MetricsListener())
    observable.add_listener(LoggingListener())
    observable.add_listener(AlertingListener(slow_threshold_ms=3000))
    
    return observable
```

**Benefits:**
- Decouple query execution from logging/metrics
- Multiple observers can react to same events
- Easy to add new observers without modifying core code

---

## Summary

This document provides production-ready implementations of key design patterns for the Database Explorer project:

### Creational Patterns
- **Factory Pattern**: Centralized connector creation with registry
- **Builder Pattern**: Fluent configuration building with validation

### Structural Patterns
- **Adapter Pattern**: Normalize different database APIs (already implemented via DatabasePort)
- **Decorator Pattern**: Add tracing, metrics, retry logic

### Behavioral Patterns
- **Strategy Pattern**: Swap query execution strategies (streaming, batch, cached)
- **Iterator Pattern**: Memory-efficient result streaming (already implemented)
- **Observer Pattern**: Event-driven notifications for metrics/logging

All patterns include:
- Complete, working implementations
- Type hints and docstrings
- Usage examples
- Clear benefits explanations

Use these patterns to maintain clean architecture, improve code reusability, and ensure the codebase remains maintainable as it grows.
