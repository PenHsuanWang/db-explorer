"""Authentication business logic."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.orm_models import User
from src.infrastructure.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration and authentication."""

    async def register(
        self,
        session: AsyncSession,
        email: str,
        username: str,
        password: str,
    ) -> User:
        """Create a new user with an Argon2id-hashed password."""
        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            hashed_pw=hash_password(password),
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        logger.info("Registered new user %s (%s)", user.username, user.id)
        return user

    async def authenticate(
        self,
        session: AsyncSession,
        email: str,
        password: str,
    ) -> User | None:
        """Verify credentials and return the user, or None on failure."""
        stmt = select(User).where(User.email == email, User.is_active.is_(True))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.hashed_pw):
            return None
        return user

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> User | None:
        """Fetch a user by their UUID."""
        stmt = select(User).where(User.id == uuid.UUID(user_id), User.is_active.is_(True))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
