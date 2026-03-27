"""Integration tests for authentication flow via HTTP endpoints.

Note: These tests use the dependency override for get_current_user,
so they do NOT test actual database-backed auth. They test routing,
response shapes, and cookie handling.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.dependencies import get_current_user
from src.main import app


def test_me_returns_user_when_auth_overridden() -> None:
    """GET /auth/me should return the mock user when auth is overridden."""
    client = TestClient(app)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


def test_protected_search_requires_auth() -> None:
    """Without the dependency override, /search should return 401."""
    # Temporarily remove the override
    override = app.dependency_overrides.pop(get_current_user, None)
    try:
        client = TestClient(app)
        response = client.post("/api/v1/search", json={"query": "test"})
        assert response.status_code == 401
    finally:
        # Restore the override for other tests
        if override:
            app.dependency_overrides[get_current_user] = override


def test_protected_connections_requires_auth() -> None:
    """Without the dependency override, /connections should return 401."""
    override = app.dependency_overrides.pop(get_current_user, None)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/connections")
        assert response.status_code == 401
    finally:
        if override:
            app.dependency_overrides[get_current_user] = override


def test_protected_peek_requires_auth() -> None:
    """Without the dependency override, /peek should return 401."""
    override = app.dependency_overrides.pop(get_current_user, None)
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/peek",
            json={"connection_id": "x", "table_name": "y"},
        )
        assert response.status_code == 401
    finally:
        if override:
            app.dependency_overrides[get_current_user] = override


def test_protected_workbench_requires_auth() -> None:
    """Without the dependency override, /workbench should return 401."""
    override = app.dependency_overrides.pop(get_current_user, None)
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/workbench",
            json={"panes": []},
        )
        assert response.status_code == 401
    finally:
        if override:
            app.dependency_overrides[get_current_user] = override


def test_logout_clears_cookie() -> None:
    """POST /auth/logout should clear the access_token cookie."""
    client = TestClient(app)
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["detail"] == "Logged out"
