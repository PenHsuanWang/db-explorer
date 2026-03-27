from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.adapters.driven.factory import ConnectorFactory
from src.adapters.driven.mock import MockConnector
from src.application.cleaning_engine import CleaningEngine
from src.application.data_service import DataService
from src.application.metadata_indexer import MetadataIndexer
from src.core.domain.models import ConnectionConfig
from src.main import app


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
    indexer.index_connection("test-mock", mock_connector)
    engine = CleaningEngine()
    return DataService(factory=factory, indexer=indexer, cleaning_engine=engine)


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)
