from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.driven.factory import ConnectorFactory
from src.application.auth_service import AuthService
from src.application.cleaning_engine import CleaningEngine
from src.application.data_service import DataService
from src.application.metadata_indexer import MetadataIndexer
from src.infrastructure.database import get_db_session
from src.infrastructure.security import decode_token

# Single global instances (application-scoped singletons)
_factory = ConnectorFactory()
_indexer = MetadataIndexer()
_engine = CleaningEngine()
_data_service = DataService(factory=_factory, indexer=_indexer, cleaning_engine=_engine)
_auth_service = AuthService()


def get_data_service() -> DataService:
    return _data_service


def get_auth_service() -> AuthService:
    return _auth_service


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Extract and validate JWT from cookie, return user dict.

    Raises HTTP 401 if the token is missing, invalid, or the user is not found.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await _auth_service.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }
