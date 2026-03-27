"""Authentication API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.models import UserCreate, UserLogin, UserResponse
from src.dependencies import get_current_user
from src.infrastructure.database import get_db_session
from src.infrastructure.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_KEY = "access_token"


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_KEY,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True in production with HTTPS
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    """Register a new user and return an auth cookie."""
    from src.application.auth_service import AuthService

    auth = AuthService()
    try:
        user = await auth.register(session, data.email, data.username, data.password)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists.",
        ) from exc

    token = create_access_token(str(user.id))
    _set_auth_cookie(response, token)
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.post("/login")
async def login(
    data: UserLogin,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    """Authenticate and return an auth cookie."""
    from src.application.auth_service import AuthService

    auth = AuthService()
    user = await auth.authenticate(session, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(str(user.id))
    _set_auth_cookie(response, token)
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Clear the auth cookie."""
    response.delete_cookie(key=COOKIE_KEY, path="/")
    return {"detail": "Logged out"}


@router.get("/me")
async def me(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse(
        id=str(current_user["id"]),
        email=current_user["email"],
        username=current_user["username"],
        is_active=current_user["is_active"],
        created_at=current_user.get("created_at", ""),
    )
