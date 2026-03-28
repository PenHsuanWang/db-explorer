"""Security audit tests.

Verifies the core security invariants of the application:

1. Read-only enforcement — DatabasePort rejects INSERT, UPDATE, DELETE, DROP
2. Password hashing uses Argon2id
3. JWT tokens expire and are correctly rejected after expiry
4. Fernet encryption/decryption roundtrips work
5. CSRF middleware blocks requests with an unknown Origin
"""

from __future__ import annotations

import time

import pytest
from jose import JWTError, jwt

from src.adapters.driven.mock import MockConnector
from src.config import get_settings
from src.core.ports.database import ReadOnlyViolationError
from src.infrastructure.security import (
    create_access_token,
    decode_token,
    decrypt_credentials,
    encrypt_credentials,
    hash_password,
    verify_password,
)
from src.main import app

# ═══════════════════════════════════════════════════════════════════════════
# 1. Read-only enforcement
# ═══════════════════════════════════════════════════════════════════════════


class TestReadOnlyEnforcement:
    """DatabasePort._validate_read_only must reject write/DDL keywords."""

    @pytest.fixture()
    def connector(self) -> MockConnector:
        c = MockConnector()
        c.connect()
        return c

    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO users VALUES (1, 'x')",
            "UPDATE users SET name='y' WHERE id=1",
            "DELETE FROM users WHERE id=1",
            "DROP TABLE users",
            "CREATE TABLE evil (id INT)",
            "ALTER TABLE users ADD COLUMN hack TEXT",
            "TRUNCATE TABLE users",
            "MERGE INTO target USING source ON 1=1 WHEN MATCHED THEN UPDATE SET a=1",
        ],
    )
    def test_rejects_write_statements(self, connector: MockConnector, sql: str) -> None:
        with pytest.raises(ReadOnlyViolationError):
            connector.execute_safe_read(sql)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users",
            "SELECT 1",
            "SELECT u.name FROM users u WHERE u.id = 1",
        ],
    )
    def test_allows_read_statements(self, connector: MockConnector, sql: str) -> None:
        # Should NOT raise — the mock will return an empty list for unknown tables
        connector.execute_safe_read(sql)

    def test_rejects_hidden_write_keyword(self, connector: MockConnector) -> None:
        """A SELECT that embeds DELETE inside should still be caught."""
        with pytest.raises(ReadOnlyViolationError):
            connector.execute_safe_read(
                "SELECT * FROM users; DELETE FROM users"
            )

    def test_stream_rejects_write(self, connector: MockConnector) -> None:
        with pytest.raises(ReadOnlyViolationError):
            list(connector.execute_query_stream("INSERT INTO t VALUES (1)"))


# ═══════════════════════════════════════════════════════════════════════════
# 2. Password hashing uses Argon2id
# ═══════════════════════════════════════════════════════════════════════════


class TestArgon2idHashing:
    def test_hash_starts_with_argon2id_marker(self) -> None:
        hashed = hash_password("audit-test-password")
        assert hashed.startswith("$argon2id$"), (
            f"Expected Argon2id hash prefix, got: {hashed[:20]}"
        )

    def test_hash_verification_succeeds(self) -> None:
        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    def test_hash_verification_fails_for_wrong_password(self) -> None:
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_different_passwords_produce_different_hashes(self) -> None:
        h1 = hash_password("password-one")
        h2 = hash_password("password-two")
        assert h1 != h2


# ═══════════════════════════════════════════════════════════════════════════
# 3. JWT token expiry
# ═══════════════════════════════════════════════════════════════════════════


class TestJWTExpiry:
    def test_valid_token_decodes(self) -> None:
        token = create_access_token("user-42")
        payload = decode_token(token)
        assert payload["sub"] == "user-42"

    def test_expired_token_is_rejected(self) -> None:
        """Manually create a token that is already expired and verify
        that ``decode_token`` raises ``JWTError``."""
        settings = get_settings()
        expired_payload = {
            "sub": "user-expired",
            "exp": int(time.time()) - 10,  # 10 seconds in the past
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        with pytest.raises(JWTError):
            decode_token(expired_token)

    def test_tampered_token_is_rejected(self) -> None:
        token = create_access_token("user-42")
        tampered = token + "x"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_token_with_wrong_secret_is_rejected(self) -> None:
        settings = get_settings()
        payload = {"sub": "user-x", "exp": int(time.time()) + 3600}
        bad_token = jwt.encode(payload, "wrong-secret", algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(JWTError):
            decode_token(bad_token)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Fernet encryption roundtrip
# ═══════════════════════════════════════════════════════════════════════════


class TestFernetEncryption:
    def test_roundtrip(self) -> None:
        plaintext = "super-secret-db-password"
        encrypted = encrypt_credentials(plaintext)
        assert isinstance(encrypted, bytes)
        assert encrypted != plaintext.encode()
        assert decrypt_credentials(encrypted) == plaintext

    def test_different_plaintext_different_ciphertext(self) -> None:
        a = encrypt_credentials("password-a")
        b = encrypt_credentials("password-b")
        assert a != b

    def test_unicode_roundtrip(self) -> None:
        plaintext = "pässwörd-日本語"
        assert decrypt_credentials(encrypt_credentials(plaintext)) == plaintext

    def test_empty_string_roundtrip(self) -> None:
        assert decrypt_credentials(encrypt_credentials("")) == ""


# ═══════════════════════════════════════════════════════════════════════════
# 5. CSRF middleware blocks unknown Origin
# ═══════════════════════════════════════════════════════════════════════════


class TestCSRFSecurity:
    def test_post_with_evil_origin_blocked(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/api/v1/search",
            json={"query": "x"},
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]

    def test_post_with_origin_and_xhr_allowed(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/api/v1/search",
            json={"query": ""},
            headers={
                "Origin": "http://localhost:5173",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        # Will succeed (auth is overridden globally in conftest)
        assert resp.status_code == 200

    def test_delete_with_evil_origin_blocked(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.delete(
            "/api/v1/connections/some-id",
            headers={"Origin": "https://evil.example.com"},
        )
        assert resp.status_code == 403
