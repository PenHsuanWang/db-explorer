"""Service for persisting database connections in PostgreSQL."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.models import ConnectionConfig
from src.core.domain.orm_models import Connection
from src.infrastructure.security import decrypt_credentials, encrypt_credentials


class ConnectionService:
    """CRUD operations for user-scoped database connections."""

    async def add_connection(
        self, session: AsyncSession, user_id: str, config: ConnectionConfig
    ) -> str:
        connection_id = config.id or str(uuid.uuid4())
        encrypted_creds: bytes | None = None
        if config.password:
            creds = json.dumps(
                {"username": config.username, "password": config.password.get_secret_value()}
            )
            encrypted_creds = encrypt_credentials(creds)

        conn = Connection(
            id=uuid.UUID(connection_id),
            user_id=uuid.UUID(user_id),
            name=config.name,
            db_type=config.db_type,
            host=config.host,
            port=config.port or 0,
            database_name=config.database,
            encrypted_creds=encrypted_creds,
            extra_params=config.extra_params or None,
        )
        session.add(conn)
        await session.flush()
        return connection_id

    async def list_connections(
        self, session: AsyncSession, user_id: str
    ) -> list[dict]:
        stmt = select(Connection).where(Connection.user_id == uuid.UUID(user_id))
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(row) for row in rows]

    async def get_connection(
        self, session: AsyncSession, user_id: str, connection_id: str
    ) -> Connection | None:
        stmt = select(Connection).where(
            Connection.id == uuid.UUID(connection_id),
            Connection.user_id == uuid.UUID(user_id),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_connection(
        self, session: AsyncSession, user_id: str, connection_id: str
    ) -> None:
        conn = await self.get_connection(session, user_id, connection_id)
        if conn is None:
            raise ValueError(f"Connection {connection_id} not found")
        await session.delete(conn)
        await session.flush()

    @staticmethod
    def _to_dict(conn: Connection) -> dict:
        creds: dict = {}
        if conn.encrypted_creds:
            creds = json.loads(decrypt_credentials(conn.encrypted_creds))
        return {
            "id": str(conn.id),
            "name": conn.name,
            "db_type": conn.db_type,
            "host": conn.host,
            "port": conn.port,
            "database": conn.database_name,
            "username": creds.get("username", ""),
            "extra_params": conn.extra_params or {},
            "created_at": conn.created_at.isoformat() if conn.created_at else "",
        }
