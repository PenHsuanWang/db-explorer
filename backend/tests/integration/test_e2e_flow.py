"""End-to-end integration tests for the full user flow.

These tests exercise the FastAPI application through the test client,
validating middleware behaviour (correlation-id, CSRF, rate-limiting),
the mock connector search → peek → workbench pipeline, and that
protected endpoints reject unauthenticated requests.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.core.domain.models import ConnectionConfig
from src.dependencies import get_current_user
from src.main import RateLimitMiddleware, app

_MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"


def _ensure_mock_connector_for_test_user() -> None:
    """Index mock connector under the test mock user so searches work."""
    from src.dependencies import _factory, _indexer, get_data_service

    svc = get_data_service()
    mock_cfg = ConnectionConfig(id="mock-default", name="Demo Mock DB", db_type="mock")
    try:
        svc.add_connection(mock_cfg, user_id=_MOCK_USER_ID)
    except Exception:
        # Already registered – just re-index metadata for this user
        connector = _factory.get("mock-default")
        _indexer.index_connection("mock-default", connector, _MOCK_USER_ID)

def _reset_rate_limiter() -> None:
    """Clear the in-memory rate-limit counters."""
    current: object = app.middleware_stack
    while current is not None:
        if isinstance(current, RateLimitMiddleware):
            current._requests.clear()
            return
        current = getattr(current, "app", None)


# ── client factories ──────────────────────────────────────────────────────


def _authed_client() -> TestClient:
    """TestClient that uses the global auth override (mock user)."""
    return TestClient(app, raise_server_exceptions=False)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Health endpoint
# ═══════════════════════════════════════════════════════════════════════════


class TestHealthEndpoint:
    def test_health_returns_expected_shape(self) -> None:
        resp = _authed_client().get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "status" in body
        assert body["status"] in ("ok", "degraded")
        services = body["services"]
        assert services["api"] == "ok"
        assert "postgres" in services
        assert "redis" in services

    def test_health_postgres_and_redis_values(self) -> None:
        services = _authed_client().get("/health").json()["services"]
        assert services["postgres"] in ("connected", "unavailable")
        assert services["redis"] in ("connected", "unavailable")


# ═══════════════════════════════════════════════════════════════════════════
# 2. Correlation-ID middleware
# ═══════════════════════════════════════════════════════════════════════════


class TestCorrelationId:
    def test_response_contains_correlation_id(self) -> None:
        assert "x-correlation-id" in _authed_client().get("/health").headers

    def test_echoes_provided_correlation_id(self) -> None:
        custom_id = "test-corr-id-12345"
        resp = _authed_client().get(
            "/health", headers={"X-Correlation-ID": custom_id}
        )
        assert resp.headers["x-correlation-id"] == custom_id

    def test_generates_unique_ids_per_request(self) -> None:
        client = _authed_client()
        ids = {client.get("/health").headers["x-correlation-id"] for _ in range(5)}
        assert len(ids) == 5


# ═══════════════════════════════════════════════════════════════════════════
# 3. Rate-limit middleware
# ═══════════════════════════════════════════════════════════════════════════


class TestRateLimiting:
    def test_rate_limit_triggers_after_threshold(self, test_client: TestClient) -> None:
        _reset_rate_limiter()
        last_status = 200
        for _ in range(101):
            resp = test_client.get("/health")
            last_status = resp.status_code
            if last_status == 429:
                break
        assert last_status == 429
        _reset_rate_limiter()


# ═══════════════════════════════════════════════════════════════════════════
# 4. Protected endpoints return 401 without auth
# ═══════════════════════════════════════════════════════════════════════════


class TestProtectedEndpointsRequireAuth:
    """Without the auth override, protected endpoints must return 401."""

    @pytest.fixture(autouse=True)
    def _no_auth(self) -> Generator[None, None, None]:
        override = app.dependency_overrides.pop(get_current_user, None)
        yield
        if override:
            app.dependency_overrides[get_current_user] = override

    def test_connections_list_401(self) -> None:
        assert _authed_client().get("/api/v1/connections").status_code == 401

    def test_connections_create_401(self) -> None:
        resp = _authed_client().post(
            "/api/v1/connections", json={"name": "x", "db_type": "mock"}
        )
        assert resp.status_code == 401

    def test_search_401(self) -> None:
        resp = _authed_client().post("/api/v1/search", json={"query": "test"})
        assert resp.status_code == 401

    def test_peek_401(self) -> None:
        resp = _authed_client().post(
            "/api/v1/peek", json={"connection_id": "x", "table_name": "y"}
        )
        assert resp.status_code == 401

    def test_workbench_401(self) -> None:
        resp = _authed_client().post("/api/v1/workbench", json={"panes": []})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 5. Mock connector is searchable
# ═══════════════════════════════════════════════════════════════════════════


class TestMockConnectorSearch:
    @pytest.fixture(autouse=True)
    def _ensure_mock_indexed(self) -> None:
        _ensure_mock_connector_for_test_user()

    def test_search_returns_results_for_mock(self, test_client: TestClient) -> None:
        resp = test_client.post("/api/v1/search", json={"query": ""})
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_search_by_table_name(self, test_client: TestClient) -> None:
        resp = test_client.post(
            "/api/v1/search", json={"query": "USER_PROFIT_SUMMARY"}
        )
        assert resp.status_code == 200
        assert any("USER_PROFIT_SUMMARY" in r.get("table_name", "") for r in resp.json())


# ═══════════════════════════════════════════════════════════════════════════
# 6. Search → peek flow
# ═══════════════════════════════════════════════════════════════════════════


class TestSearchPeekFlow:
    @pytest.fixture(autouse=True)
    def _ensure_mock_indexed(self) -> None:
        _ensure_mock_connector_for_test_user()

    def test_peek_mock_table(self, test_client: TestClient) -> None:
        resp = test_client.post(
            "/api/v1/peek",
            json={
                "connection_id": "mock-default",
                "table_name": "USER_PROFIT_SUMMARY",
                "schema_name": "FINANCE_SCHEMA",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "columns" in body
        assert len(body["rows"]) > 0

    def test_peek_returns_column_metadata(self, test_client: TestClient) -> None:
        resp = test_client.post(
            "/api/v1/peek",
            json={"connection_id": "mock-default", "table_name": "TRANSACTION_LOG"},
        )
        assert resp.status_code == 200
        col_names = [c["name"] for c in resp.json()["columns"]]
        assert "TX_ID" in col_names


# ═══════════════════════════════════════════════════════════════════════════
# 7. Workbench with mock connector
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkbenchFlow:
    @pytest.fixture(autouse=True)
    def _ensure_mock_indexed(self) -> None:
        _ensure_mock_connector_for_test_user()

    def test_workbench_single_pane(self, test_client: TestClient) -> None:
        resp = test_client.post(
            "/api/v1/workbench",
            json={
                "panes": [
                    {
                        "connection_id": "mock-default",
                        "table_name": "EMPLOYEE_RECORDS",
                        "schema_name": "HR_SCHEMA",
                        "pane_id": "p1",
                    }
                ],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "p1" in body["panes"]
        assert len(body["panes"]["p1"]["rows"]) > 0

    def test_workbench_multiple_panes(self, test_client: TestClient) -> None:
        resp = test_client.post(
            "/api/v1/workbench",
            json={
                "panes": [
                    {
                        "connection_id": "mock-default",
                        "table_name": "USER_PROFIT_SUMMARY",
                        "pane_id": "pane_a",
                    },
                    {
                        "connection_id": "mock-default",
                        "table_name": "TRANSACTION_LOG",
                        "pane_id": "pane_b",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        panes = resp.json()["panes"]
        assert "pane_a" in panes
        assert "pane_b" in panes


# ═══════════════════════════════════════════════════════════════════════════
# 8. CSRF middleware
# ═══════════════════════════════════════════════════════════════════════════


class TestCSRFMiddleware:
    @pytest.fixture(autouse=True)
    def _ensure_mock_indexed(self) -> None:
        _ensure_mock_connector_for_test_user()

    def test_csrf_blocks_post_with_origin_no_xhr_header(self) -> None:
        resp = _authed_client().post(
            "/api/v1/search",
            json={"query": "test"},
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]

    def test_csrf_allows_post_with_xhr_header(self) -> None:
        resp = _authed_client().post(
            "/api/v1/search",
            json={"query": ""},
            headers={
                "Origin": "http://localhost:5173",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        assert resp.status_code == 200

    def test_csrf_allows_post_without_origin(self) -> None:
        resp = _authed_client().post("/api/v1/search", json={"query": ""})
        assert resp.status_code == 200

    def test_csrf_allows_get_requests(self) -> None:
        resp = _authed_client().get(
            "/health", headers={"Origin": "https://evil.example.com"}
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# 9. Connection CRUD (with mocked auth)
# ═══════════════════════════════════════════════════════════════════════════


class TestConnectionCRUD:
    def test_list_connections(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/v1/connections")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_add_and_remove_connection(self, test_client: TestClient) -> None:
        resp = test_client.post(
            "/api/v1/connections",
            json={"name": "e2e-conn", "db_type": "mock", "id": "e2e-test-conn"},
        )
        assert resp.status_code == 201
        conn_id = resp.json()["connection_id"]

        listing = test_client.get("/api/v1/connections").json()
        assert any(c.get("id") == conn_id for c in listing)

        del_resp = test_client.delete(f"/api/v1/connections/{conn_id}")
        assert del_resp.status_code == 200
