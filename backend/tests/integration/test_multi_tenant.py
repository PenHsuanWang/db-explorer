"""Integration tests for multi-tenant (user-scoped) metadata indexing."""

from __future__ import annotations

import pytest

from src.adapters.driven.mock import MockConnector
from src.application.metadata_indexer import MetadataIndexer


@pytest.fixture
def indexer() -> MetadataIndexer:
    return MetadataIndexer(db_path=":memory:")


@pytest.fixture
def connector_a() -> MockConnector:
    connector = MockConnector(name="conn-a")
    connector.connect()
    return connector


@pytest.fixture
def connector_b() -> MockConnector:
    connector = MockConnector(name="conn-b")
    connector.connect()
    return connector


USER_A = "00000000-0000-0000-0000-00000000000a"
USER_B = "00000000-0000-0000-0000-00000000000b"


class TestUserScopedSearch:
    """Verify that search results are scoped to the requesting user."""

    def test_user_a_sees_only_own_data(
        self,
        indexer: MetadataIndexer,
        connector_a: MockConnector,
        connector_b: MockConnector,
    ) -> None:
        indexer.index_connection("conn-a", connector_a, user_id=USER_A)
        indexer.index_connection("conn-b", connector_b, user_id=USER_B)

        results_a = indexer.search("", user_id=USER_A)
        assert len(results_a) > 0
        assert all(r.source_db == "conn-a" for r in results_a)

    def test_user_b_sees_only_own_data(
        self,
        indexer: MetadataIndexer,
        connector_a: MockConnector,
        connector_b: MockConnector,
    ) -> None:
        indexer.index_connection("conn-a", connector_a, user_id=USER_A)
        indexer.index_connection("conn-b", connector_b, user_id=USER_B)

        results_b = indexer.search("", user_id=USER_B)
        assert len(results_b) > 0
        assert all(r.source_db == "conn-b" for r in results_b)

    def test_users_have_independent_result_sets(
        self,
        indexer: MetadataIndexer,
        connector_a: MockConnector,
        connector_b: MockConnector,
    ) -> None:
        indexer.index_connection("conn-a", connector_a, user_id=USER_A)
        indexer.index_connection("conn-b", connector_b, user_id=USER_B)

        results_a = indexer.search("", user_id=USER_A)
        results_b = indexer.search("", user_id=USER_B)

        ids_a = {r.id for r in results_a}
        ids_b = {r.id for r in results_b}
        assert ids_a.isdisjoint(ids_b), "User result sets must not overlap"


class TestUserScopedRemoval:
    """Verify that removing a connection for one user doesn't affect another."""

    def test_remove_connection_scoped_to_user(
        self,
        indexer: MetadataIndexer,
        connector_a: MockConnector,
        connector_b: MockConnector,
    ) -> None:
        # Both users index the same connection id but separately
        indexer.index_connection("shared-conn", connector_a, user_id=USER_A)
        indexer.index_connection("shared-conn", connector_b, user_id=USER_B)

        # Remove for user A only
        indexer.remove_connection("shared-conn", user_id=USER_A)

        results_a = indexer.search("", user_id=USER_A)
        results_b = indexer.search("", user_id=USER_B)

        assert len(results_a) == 0, "User A's data should be gone"
        assert len(results_b) > 0, "User B's data should remain intact"

    def test_remove_nonexistent_connection_is_safe(
        self,
        indexer: MetadataIndexer,
    ) -> None:
        # Should not raise
        indexer.remove_connection("does-not-exist", user_id=USER_A)
