"""Redis client wrapper for caching and Pub/Sub."""
from __future__ import annotations

import redis

from src.config import get_settings


def get_redis_client() -> redis.Redis:
    """Create a Redis client instance."""
    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True)
