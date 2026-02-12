"""
Shared pytest configuration and fixtures.

This file is automatically loaded by pytest and provides:
- Common fixtures available to all tests
- Test configuration and markers
- Setup/teardown hooks
- Shared test utilities

Place this file in the tests/ directory root.
"""

import pytest
from typing import Any, Iterator
from pathlib import Path


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers and configure pytest.
    
    This hook is called during pytest initialization to register
    custom markers that can be used to categorize tests.
    
    Args:
        config: Pytest configuration object.
    """
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running (> 1 second)"
    )
    config.addinivalue_line(
        "markers",
        "smoke: mark test as smoke test (quick validation)"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify test collection to add markers automatically.
    
    This hook runs after test collection and can automatically add
    markers based on test location or name patterns.
    
    Args:
        config: Pytest configuration.
        items: List of collected test items.
    """
    for item in items:
        # Automatically mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Automatically mark unit tests
        if "unit" in item.nodeid or "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)


# ============================================================================
# Session-scoped Fixtures (run once per test session)
# ============================================================================


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Provide path to test data directory.
    
    Returns:
        Path to the test_data directory.
    """
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Provide path to project root directory.
    
    Returns:
        Path to project root.
    """
    return Path(__file__).parent.parent


# ============================================================================
# Module-scoped Fixtures (run once per test module)
# ============================================================================


@pytest.fixture(scope="module")
def database_container() -> Iterator[dict[str, Any]]:
    """Start a test database container for integration tests.
    
    This fixture starts a PostgreSQL container using testcontainers
    and provides connection details to tests. The container is shared
    across all tests in a module.
    
    Yields:
        Dictionary with database connection details.
        
    Example:
        >>> def test_query(database_container):
        ...     config = database_container
        ...     connector = create_connector(config)
    """
    # Example using testcontainers (requires testcontainers-python)
    try:
        from testcontainers.postgres import PostgresContainer
        
        with PostgresContainer("postgres:15") as postgres:
            yield {
                "type": "postgres",
                "host": postgres.get_container_host_ip(),
                "port": postgres.get_exposed_port(5432),
                "database": postgres.POSTGRES_DB,
                "user": postgres.POSTGRES_USER,
                "password": postgres.POSTGRES_PASSWORD,
            }
    except ImportError:
        # If testcontainers not available, provide mock config
        pytest.skip("testcontainers-python not installed")


# ============================================================================
# Function-scoped Fixtures (run for each test function)
# ============================================================================


@pytest.fixture
def sample_data() -> dict[str, list[dict[str, Any]]]:
    """Provide sample data for tests.
    
    Returns:
        Dictionary containing sample data for different entities.
    """
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com", "age": 35},
        ],
        "products": [
            {"id": 101, "name": "Widget", "price": 9.99, "stock": 100},
            {"id": 102, "name": "Gadget", "price": 19.99, "stock": 50},
            {"id": 103, "name": "Doohickey", "price": 14.99, "stock": 75},
        ],
        "orders": [
            {"id": 1, "user_id": 1, "product_id": 101, "quantity": 2},
            {"id": 2, "user_id": 2, "product_id": 102, "quantity": 1},
        ],
    }


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files.
    
    Uses pytest's built-in tmp_path fixture to create a temporary
    directory that is automatically cleaned up after the test.
    
    Args:
        tmp_path: Pytest's temporary directory fixture.
        
    Returns:
        Path to temporary directory.
    """
    return tmp_path


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Provide sample database configuration.
    
    Returns:
        Dictionary with database connection settings.
    """
    return {
        "type": "oracle",
        "host": "localhost",
        "port": 1521,
        "database": "testdb",
        "user": "testuser",
        "password": "testpass",
        "read_only": True,
        "pool_size": 5,
    }


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables before each test.
    
    This fixture runs automatically before each test and ensures
    a clean environment state.
    
    Args:
        monkeypatch: Pytest's monkeypatch fixture for modifying environment.
    """
    # Clear environment variables that might affect tests
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)


# ============================================================================
# Async Fixtures (for testing async code)
# ============================================================================


@pytest.fixture
async def async_client():
    """Provide an async HTTP client for testing.
    
    Yields:
        Async HTTP client instance.
        
    Example:
        >>> async def test_api(async_client):
        ...     response = await async_client.get("/api/users")
        ...     assert response.status_code == 200
    """
    # Example for httpx
    try:
        from httpx import AsyncClient
        
        async with AsyncClient(base_url="http://test") as client:
            yield client
    except ImportError:
        pytest.skip("httpx not installed")


# ============================================================================
# Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_logger(mocker):
    """Provide a mocked logger.
    
    Args:
        mocker: pytest-mock's mocker fixture.
        
    Returns:
        Mocked logger instance.
    """
    return mocker.patch("logging.getLogger")


@pytest.fixture
def mock_connector(mocker):
    """Provide a mocked database connector.
    
    Args:
        mocker: pytest-mock's mocker fixture.
        
    Returns:
        Mocked DatabasePort connector.
    """
    connector = mocker.Mock()
    connector.connect.return_value = None
    connector.close.return_value = None
    connector.execute_query_stream.return_value = iter([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ])
    connector.fetch_schema.return_value = {
        "id": "INTEGER",
        "name": "TEXT",
    }
    return connector


# ============================================================================
# Test Hooks for Reporting
# ============================================================================


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Add custom information to test reports.
    
    This hook is called after each test phase (setup, call, teardown)
    to create a test report.
    
    Args:
        item: Test item that was run.
        call: Information about the test call.
    """
    if call.when == "call":
        # Store test result for potential cleanup or reporting
        if hasattr(item, "rep_call"):
            item.rep_call = call


def pytest_report_header(config: pytest.Config) -> list[str]:
    """Add custom header information to test report.
    
    Args:
        config: Pytest configuration.
        
    Returns:
        List of strings to add to report header.
    """
    return [
        "Database Explorer Test Suite",
        f"Project root: {Path(__file__).parent.parent}",
    ]


# ============================================================================
# Utility Functions for Tests
# ============================================================================


def load_fixture_data(filename: str) -> Any:
    """Load fixture data from JSON or YAML file.
    
    Args:
        filename: Name of fixture file in test_data directory.
        
    Returns:
        Parsed fixture data.
    """
    import json
    
    fixture_path = Path(__file__).parent / "test_data" / filename
    
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")
    
    if filename.endswith(".json"):
        with open(fixture_path) as f:
            return json.load(f)
    elif filename.endswith((".yml", ".yaml")):
        try:
            import yaml
            with open(fixture_path) as f:
                return yaml.safe_load(f)
        except ImportError:
            pytest.skip("PyYAML not installed")
    else:
        raise ValueError(f"Unsupported fixture file format: {filename}")


def create_test_table(connector, table_name: str, schema: dict[str, str]) -> None:
    """Create a test table in the database.
    
    Helper function for integration tests that need to create tables.
    
    Args:
        connector: Database connector instance.
        table_name: Name of table to create.
        schema: Dictionary mapping column names to types.
    """
    columns = ", ".join(f"{name} {dtype}" for name, dtype in schema.items())
    sql = f"CREATE TABLE {table_name} ({columns})"
    # Execute table creation
    pass  # Implement based on connector API


# ============================================================================
# Pytest Plugins Configuration
# ============================================================================


# Configure pytest-timeout (if installed)
def pytest_timeout_func_only() -> bool:
    """Configure pytest-timeout to only timeout on function, not fixtures."""
    return True


# Configure pytest-xdist (if installed)
def pytest_xdist_setupnodes(config: pytest.Config, specs) -> None:
    """Configure pytest-xdist for parallel test execution."""
    pass  # Add custom xdist configuration if needed
