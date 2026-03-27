from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.adapters.driven.factory import ConnectorFactory
from src.adapters.driven.mock import MockConnector
from src.application.cleaning_engine import CleaningEngine
from src.application.data_service import DataService
from src.application.metadata_indexer import MetadataIndexer
from src.core.domain.models import ConnectionConfig
from src.dependencies import get_current_user
from src.main import app

# ---------------------------------------------------------------------------
# A fixed mock user returned by the overridden auth dependency so that
# existing endpoint tests do not need a real database or JWT cookies.
# ---------------------------------------------------------------------------

_MOCK_USER: dict = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "test@example.com",
    "username": "testuser",
    "is_active": True,
    "created_at": "2024-01-01T00:00:00+00:00",
}


async def _override_get_current_user() -> dict:
    return _MOCK_USER


# Override the auth dependency globally for the test suite
app.dependency_overrides[get_current_user] = _override_get_current_user


@pytest.fixture
def mock_connector() -> MockConnector:
    connector = MockConnector(name="test-mock")
    connector.connect()
    return connector


@pytest.fixture
def cleaning_engine() -> CleaningEngine:
    return CleaningEngine()


@pytest.fixture
def data_service(mock_connector: MockConnector) -> DataService:
    factory = ConnectorFactory()
    config = ConnectionConfig(id="test-mock", name="Test Mock", db_type="mock")
    factory.create(config)
    indexer = MetadataIndexer(db_path=":memory:")
    indexer.index_connection("test-mock", mock_connector, user_id=_MOCK_USER["id"])
    engine = CleaningEngine()
    return DataService(factory=factory, indexer=indexer, cleaning_engine=engine)


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)
