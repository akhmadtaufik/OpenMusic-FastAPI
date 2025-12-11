"""Cache service for Redis operations.

Uses redis.asyncio for async Redis client. Provides get/set/delete
operations with TTL support.
"""

import redis.asyncio as redis
from app.core.config import settings


class CacheService:
    """Service for caching operations using Redis.

    Attributes:
        client: Redis async client instance.
    """

    def __init__(self):
        """Initialize Redis connection params; clients are created per call."""
        self._host = settings.REDIS_HOST
        self._port = settings.REDIS_PORT

    def _client(self):
        """Create a new Redis client to avoid cross-event-loop reuse in tests."""
        return redis.Redis(
            host=self._host,
            port=self._port,
            decode_responses=True
        )

    async def get(self, key: str) -> str | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        try:
            client = self._client()
            try:
                return await client.get(key)
            finally:
                await client.close()
        except redis.RedisError as e:
            # Log error but don't crash - cache miss is acceptable
            print(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: str, expiration: int = 1800) -> bool:
        """Set value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            expiration: TTL in seconds (default 30 minutes).

        Returns:
            True if successful, False otherwise.
        """
        try:
            client = self._client()
            try:
                await client.set(key, value, ex=expiration)
            finally:
                await client.close()
            return True
        except redis.RedisError as e:
            print(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if deleted, False otherwise.
        """
        try:
            client = self._client()
            try:
                await client.delete(key)
            finally:
                await client.close()
            return True
        except redis.RedisError as e:
            print(f"Redis DELETE error: {e}")
            return False

    async def close(self):
        """No-op retained for API compatibility."""
        return None


# Singleton instance for dependency injection
cache_service = CacheService()
