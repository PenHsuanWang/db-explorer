from __future__ import annotations

from src.adapters.driven.factory import ConnectorFactory
from src.application.cleaning_engine import CleaningEngine
from src.application.data_service import DataService
from src.application.metadata_indexer import MetadataIndexer

# Single global instances (application-scoped singletons)
_factory = ConnectorFactory()
_indexer = MetadataIndexer()
_engine = CleaningEngine()
_data_service = DataService(factory=_factory, indexer=_indexer, cleaning_engine=_engine)


def get_data_service() -> DataService:
    return _data_service
