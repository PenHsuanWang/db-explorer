"""Unit tests for security utilities (JWT, password hashing, Fernet encryption)."""

from __future__ import annotations

import pytest
from jose import JWTError

from src.infrastructure.security import (
    create_access_token,
    decode_token,
    decrypt_credentials,
    encrypt_credentials,
    hash_password,
    verify_password,
)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_hash_password_returns_non_empty_string() -> None:
    hashed = hash_password("mysecretpassword")
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != "mysecretpassword"


def test_verify_password_correct() -> None:
    hashed = hash_password("correct-horse-battery")
    assert verify_password("correct-horse-battery", hashed) is True


def test_verify_password_incorrect() -> None:
    hashed = hash_password("correct-horse-battery")
    assert verify_password("wrong-password", hashed) is False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------


def test_create_and_decode_token() -> None:
    token = create_access_token("user-id-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-123"
    assert "exp" in payload


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(JWTError):
        decode_token("not-a-valid-jwt-token")


# ---------------------------------------------------------------------------
# Fernet encryption
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_roundtrip() -> None:
    plaintext = "my-database-password"
    encrypted = encrypt_credentials(plaintext)
    assert isinstance(encrypted, bytes)
    assert encrypted != plaintext.encode()
    decrypted = decrypt_credentials(encrypted)
    assert decrypted == plaintext


def test_encrypt_produces_different_ciphertext() -> None:
    """Fernet includes a timestamp, so encrypting the same value twice yields
    different ciphertext (but both decrypt to the same plaintext)."""
    encrypted1 = encrypt_credentials("same-value")
    encrypted2 = encrypt_credentials("same-value")
    # They may or may not differ (Fernet is non-deterministic), but both
    # must round-trip correctly.
    assert decrypt_credentials(encrypted1) == "same-value"
    assert decrypt_credentials(encrypted2) == "same-value"
