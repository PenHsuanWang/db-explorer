"""Redis client wrapper for caching and Pub/Sub."""
from __future__ import annotations

import json
import logging
from typing import Any

import redis as redis_lib

from src.config import get_settings

logger = logging.getLogger(__name__)

_CACHE_TTLS = {
    "search": 300,  # 5 minutes
    "connections": 60,  # 1 minute
    "peek": 120,  # 2 minutes
}


def get_redis_client() -> redis_lib.Redis:
    """Create a Redis client instance."""
    settings = get_settings()
    return redis_lib.from_url(settings.REDIS_URL, decode_responses=True)


class RedisCache:
    """Optional Redis caching layer with graceful degradation."""

    def __init__(self) -> None:
        self._client: redis_lib.Redis | None = None

    def _get_client(self) -> redis_lib.Redis | None:
        if self._client is None:
            try:
                self._client = get_redis_client()
                self._client.ping()
            except Exception:
                logger.debug("Redis not available, caching disabled")
                self._client = None
        return self._client

    def get(self, key: str) -> Any | None:
        client = self._get_client()
        if client is None:
            return None
        try:
            val = client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl_category: str = "search") -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            ttl = _CACHE_TTLS.get(ttl_category, 300)
            client.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            logger.debug("Failed to set cache key %s", key)

    def invalidate(self, pattern: str) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            cursor = "0"
            while cursor != 0:
                cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    client.delete(*keys)
        except Exception:
            logger.debug("Failed to invalidate cache pattern %s", pattern)

    def health_check(self) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            return client.ping()
        except Exception:
            return False
