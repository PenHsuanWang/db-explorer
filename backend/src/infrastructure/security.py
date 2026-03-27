"""JWT, password hashing, and credential encryption utilities."""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from src.config import get_settings

# ---------------------------------------------------------------------------
# Password hashing (Argon2id)
# ---------------------------------------------------------------------------

_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    return _password_hash.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------


def create_access_token(user_id: str, extra_data: dict[str, Any] | None = None) -> str:
    """Create a JWT access token with configurable expiry."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": str(user_id), "exp": expire}
    if extra_data:
        payload.update(extra_data)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise
    return payload


# ---------------------------------------------------------------------------
# Fernet encryption (for connection credentials at rest)
# ---------------------------------------------------------------------------


def _derive_fernet_key(secret: str) -> bytes:
    """Derive a valid Fernet key from an arbitrary-length secret string."""
    raw = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(raw)


def encrypt_credentials(data: str) -> bytes:
    """Encrypt a string using Fernet symmetric encryption."""
    settings = get_settings()
    key = _derive_fernet_key(settings.ENCRYPTION_KEY)
    f = Fernet(key)
    return f.encrypt(data.encode())


def decrypt_credentials(encrypted: bytes) -> str:
    """Decrypt Fernet-encrypted bytes back to a string."""
    settings = get_settings()
    key = _derive_fernet_key(settings.ENCRYPTION_KEY)
    f = Fernet(key)
    return f.decrypt(encrypted).decode()
