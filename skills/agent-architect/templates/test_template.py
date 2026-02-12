"""
Test template demonstrating pytest best practices.

This module shows examples of:
- Fixtures for test setup
- Parametrized tests
- Mocking external dependencies
- Testing async code (if applicable)
- Contract tests for interface compliance

Follow these patterns when writing tests for the Database Explorer project.
"""

import pytest
from typing import Any, Iterator
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Provide sample database configuration for tests.
    
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
    }


@pytest.fixture
def mock_connector(mocker) -> Mock:
    """Create a mocked database connector.
    
    Uses pytest-mock (mocker fixture) to create a connector mock
    with predefined behavior for testing.
    
    Args:
        mocker: pytest-mock fixture for creating mocks.
        
    Returns:
        Mocked DatabasePort connector.
    """
    connector = mocker.Mock()
    connector.connect.return_value = None
    connector.close.return_value = None
    connector.execute_query_stream.return_value = iter([
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ])
    return connector


@pytest.fixture
def sample_query_result() -> list[dict[str, Any]]:
    """Provide sample query result data.
    
    Returns:
        List of dictionaries representing query results.
    """
    return [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 3, "name": "Charlie", "age": 35},
    ]


# ============================================================================
# Basic Unit Tests
# ============================================================================


def test_example_function() -> None:
    """Test basic functionality of example_function.
    
    This demonstrates a simple unit test with assertion.
    """
    result = example_function(42)
    assert result == 84
    assert isinstance(result, int)


def test_with_fixture(sample_config: dict[str, Any]) -> None:
    """Test using a fixture for test data.
    
    Fixtures provide reusable test data and setup logic.
    
    Args:
        sample_config: Injected fixture with configuration.
    """
    assert sample_config["host"] == "localhost"
    assert sample_config["port"] == 1521
    assert "type" in sample_config


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
])
def test_parametrized(input_value: int, expected: int) -> None:
    """Test with multiple parameter sets.
    
    Parametrized tests run the same test logic with different inputs,
    making it easy to test edge cases and various scenarios.
    
    Args:
        input_value: Input to test function.
        expected: Expected output value.
    """
    assert example_function(input_value) == expected


@pytest.mark.parametrize("sql,is_valid", [
    ("SELECT * FROM users", True),
    ("SELECT id, name FROM users WHERE age > 18", True),
    ("DELETE FROM users", False),
    ("UPDATE users SET name = 'Alice'", False),
    ("DROP TABLE users", False),
])
def test_query_validation(sql: str, is_valid: bool) -> None:
    """Test SQL query validation with various inputs.
    
    Args:
        sql: SQL query string to validate.
        is_valid: Whether query should be considered valid.
    """
    # Replace with actual validation function
    result = validate_query(sql)
    assert result == is_valid


# ============================================================================
# Mocking Tests
# ============================================================================


def test_with_mock(mock_connector: Mock) -> None:
    """Test using mocked dependencies.
    
    Mocking allows testing code that depends on external services
    without actually connecting to them.
    
    Args:
        mock_connector: Mocked database connector fixture.
    """
    # Execute query using mock
    results = list(mock_connector.execute_query_stream("SELECT * FROM users"))
    
    # Verify results
    assert len(results) == 2
    assert results[0]["name"] == "Alice"
    assert results[1]["name"] == "Bob"
    
    # Verify mock was called correctly
    mock_connector.execute_query_stream.assert_called_once_with("SELECT * FROM users")


def test_with_patch() -> None:
    """Test using patch to mock external dependencies.
    
    The patch decorator temporarily replaces the target with a mock.
    """
    with patch("module.external_api_call") as mock_api:
        # Configure mock behavior
        mock_api.return_value = {"status": "success", "data": [1, 2, 3]}
        
        # Call function that uses external API
        result = function_that_calls_api()
        
        # Verify results
        assert result["status"] == "success"
        assert len(result["data"]) == 3
        
        # Verify API was called
        mock_api.assert_called_once()


# ============================================================================
# Exception Testing
# ============================================================================


def test_raises_exception() -> None:
    """Test that appropriate exceptions are raised.
    
    Use pytest.raises context manager to verify exception behavior.
    """
    with pytest.raises(ValueError, match="Invalid input"):
        risky_function(-1)


def test_exception_message() -> None:
    """Test exception message content."""
    with pytest.raises(ValueError) as exc_info:
        risky_function(-1)
    
    assert "Invalid input" in str(exc_info.value)
    assert exc_info.value.args[0] == "Invalid input: -1"


# ============================================================================
# Contract Tests (Interface Compliance)
# ============================================================================


@pytest.mark.parametrize("connector_class", [
    "OracleConnector",
    "ClickHouseConnector",
    "DatabricksConnector",
])
def test_connector_contract(connector_class: str) -> None:
    """Verify all connectors implement the DatabasePort interface.
    
    Contract tests ensure all implementations follow the same interface,
    making them interchangeable.
    
    Args:
        connector_class: Name of connector class to test.
    """
    # Import connector class (replace with actual imports)
    # connector_cls = get_connector_class(connector_class)
    
    # Check it implements DatabasePort
    # assert issubclass(connector_cls, DatabasePort)
    
    # Check required methods exist
    required_methods = [
        "connect",
        "close",
        "execute_query_stream",
        "fetch_schema",
    ]
    
    for method in required_methods:
        # assert hasattr(connector_cls, method)
        # assert callable(getattr(connector_cls, method))
        pass  # Replace with actual checks


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
def test_database_integration(sample_config: dict[str, Any]) -> None:
    """Integration test against real database.
    
    Integration tests require external services (databases, APIs).
    They are marked with @pytest.mark.integration so they can be
    run separately from fast unit tests.
    
    Note: This example requires testcontainers or a test database.
    
    Args:
        sample_config: Database configuration fixture.
    """
    # Example using testcontainers
    # from testcontainers.postgres import PostgresContainer
    
    # with PostgresContainer("postgres:15") as postgres:
    #     config = {
    #         "host": postgres.get_container_host_ip(),
    #         "port": postgres.get_exposed_port(5432),
    #         "database": postgres.POSTGRES_DB,
    #     }
    #     
    #     connector = create_connector(config)
    #     connector.connect()
    #     
    #     try:
    #         results = list(connector.execute_query_stream("SELECT 1 as num"))
    #         assert len(results) == 1
    #         assert results[0]["num"] == 1
    #     finally:
    #         connector.close()
    
    pass  # Replace with actual integration test


@pytest.mark.integration
@pytest.mark.slow
def test_large_result_set() -> None:
    """Test handling of large result sets.
    
    This test is marked as both integration and slow, so it can be
    skipped in quick test runs.
    """
    # Test with large dataset
    pass


# ============================================================================
# Async Tests (if using async code)
# ============================================================================


@pytest.mark.asyncio
async def test_async_function() -> None:
    """Test async functions.
    
    Requires pytest-asyncio plugin.
    Use @pytest.mark.asyncio decorator for async tests.
    """
    result = await async_example_function(42)
    assert result == 84


# ============================================================================
# Test Helpers and Utilities
# ============================================================================


def example_function(x: int) -> int:
    """Example function to test.
    
    Args:
        x: Input integer.
        
    Returns:
        Input multiplied by 2.
    """
    return x * 2


def risky_function(x: int) -> int:
    """Example function that raises exceptions.
    
    Args:
        x: Input integer.
        
    Returns:
        Input value.
        
    Raises:
        ValueError: If x is negative.
    """
    if x < 0:
        raise ValueError(f"Invalid input: {x}")
    return x


def validate_query(sql: str) -> bool:
    """Validate SQL query.
    
    Args:
        sql: SQL query string.
        
    Returns:
        True if query is valid (SELECT), False otherwise.
    """
    return sql.strip().upper().startswith("SELECT")


def function_that_calls_api() -> dict[str, Any]:
    """Example function that calls external API.
    
    Returns:
        API response.
    """
    # This would normally call external_api_call()
    return {"status": "success", "data": []}


# ============================================================================
# Test Classes (optional grouping)
# ============================================================================


class TestConnectorFactory:
    """Group related tests in a class.
    
    Test classes provide a way to organize related tests and share
    fixtures within the class.
    """
    
    def test_create_oracle_connector(self, sample_config: dict[str, Any]) -> None:
        """Test Oracle connector creation."""
        # connector = ConnectorFactory.create(sample_config)
        # assert isinstance(connector, OracleConnector)
        pass
    
    def test_create_invalid_type(self) -> None:
        """Test error handling for invalid connector type."""
        with pytest.raises(ValueError, match="Unknown connector type"):
            # ConnectorFactory.create({"type": "invalid"})
            pass
    
    def test_missing_config(self) -> None:
        """Test error handling for missing configuration."""
        with pytest.raises(KeyError, match="type"):
            # ConnectorFactory.create({})
            pass
