"""Redis client for caching and session management."""
import json
from typing import Any

import redis.asyncio as redis

from src.config import settings


class RedisClient:
    """Async Redis client wrapper."""
    
    def __init__(self) -> None:
        """Initialize Redis connection pool."""
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=50,
        )
        self.client: redis.Redis | None = None
    
    async def connect(self) -> None:
        """Create Redis client connection."""
        if self.client is None:
            self.client = redis.Redis(connection_pool=self.pool)
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            await self.pool.disconnect()
    
    async def get(self, key: str) -> str | None:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.client:
            await self.connect()
        return await self.client.get(key)  # type: ignore
    
    async def set(
        self,
        key: str,
        value: str,
        expire: int | None = None,
    ) -> bool:
        """
        Set value in Redis.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: TTL in seconds
            
        Returns:
            True if successful
        """
        if not self.client:
            await self.connect()
        return await self.client.set(key, value, ex=expire)  # type: ignore
    
    async def delete(self, key: str) -> int:
        """
        Delete key from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            await self.connect()
        return await self.client.delete(key)  # type: ignore
    
    async def get_json(self, key: str) -> Any:
        """
        Get JSON value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized JSON value or None
        """
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """
        Set JSON value in Redis.
        
        Args:
            key: Cache key
            value: Value to serialize and cache
            expire: TTL in seconds
            
        Returns:
            True if successful
        """
        return await self.set(key, json.dumps(value), expire)


# Global Redis client instance
redis_client = RedisClient()


# Cache key prefixes
CACHE_PREFIX_PLAN = "plan:"
CACHE_PREFIX_SCHEDULE = "schedule:"
CACHE_PREFIX_PROGRESS = "progress:"

# Cache TTLs (in seconds)
CACHE_TTL_PLAN = 300  # 5 minutes
CACHE_TTL_SCHEDULE = 60  # 1 minute
CACHE_TTL_PROGRESS = 180  # 3 minutes


def get_redis_client() -> RedisClient:
    """Get the global Redis client instance."""
    return redis_client


async def cache_user_plan(user_id: str, plan_data: dict) -> bool:
    """Cache user's active fitness plan.

    Args:
        user_id: User ID
        plan_data: Plan data to cache

    Returns:
        True if cached successfully
    """
    key = f"{CACHE_PREFIX_PLAN}{user_id}:active"
    return await redis_client.set_json(key, plan_data, expire=CACHE_TTL_PLAN)


async def get_cached_user_plan(user_id: str) -> dict | None:
    """Get cached fitness plan for user.

    Args:
        user_id: User ID

    Returns:
        Cached plan data or None
    """
    key = f"{CACHE_PREFIX_PLAN}{user_id}:active"
    return await redis_client.get_json(key)


async def invalidate_user_plan_cache(user_id: str) -> int:
    """Invalidate cached plan for user.

    Args:
        user_id: User ID

    Returns:
        Number of keys deleted
    """
    key = f"{CACHE_PREFIX_PLAN}{user_id}:active"
    return await redis_client.delete(key)


async def cache_user_schedule(user_id: str, date: str, schedule_data: dict) -> bool:
    """Cache user's schedule for a specific date.

    Args:
        user_id: User ID
        date: Date in YYYY-MM-DD format
        schedule_data: Schedule data to cache

    Returns:
        True if cached successfully
    """
    key = f"{CACHE_PREFIX_SCHEDULE}{user_id}:{date}"
    return await redis_client.set_json(key, schedule_data, expire=CACHE_TTL_SCHEDULE)


async def get_cached_user_schedule(user_id: str, date: str) -> dict | None:
    """Get cached schedule for user and date.

    Args:
        user_id: User ID
        date: Date in YYYY-MM-DD format

    Returns:
        Cached schedule data or None
    """
    key = f"{CACHE_PREFIX_SCHEDULE}{user_id}:{date}"
    return await redis_client.get_json(key)


async def invalidate_user_schedule_cache(user_id: str, date: str | None = None) -> int:
    """Invalidate cached schedule for user.

    Args:
        user_id: User ID
        date: Specific date to invalidate, or None to invalidate all dates

    Returns:
        Number of keys deleted
    """
    if date:
        key = f"{CACHE_PREFIX_SCHEDULE}{user_id}:{date}"
        return await redis_client.delete(key)
    else:
        # Invalidate all schedule keys for user
        # Note: This requires SCAN operation in production
        # For now, this is a simplified version
        return 0


async def cache_user_progress(user_id: str, progress_data: dict) -> bool:
    """Cache user's progress summary.

    Args:
        user_id: User ID
        progress_data: Progress data to cache

    Returns:
        True if cached successfully
    """
    key = f"{CACHE_PREFIX_PROGRESS}{user_id}:summary"
    return await redis_client.set_json(key, progress_data, expire=CACHE_TTL_PROGRESS)


async def get_cached_user_progress(user_id: str) -> dict | None:
    """Get cached progress summary for user.

    Args:
        user_id: User ID

    Returns:
        Cached progress data or None
    """
    key = f"{CACHE_PREFIX_PROGRESS}{user_id}:summary"
    return await redis_client.get_json(key)


async def invalidate_user_progress_cache(user_id: str) -> int:
    """Invalidate cached progress for user.

    Args:
        user_id: User ID

    Returns:
        Number of keys deleted
    """
    key = f"{CACHE_PREFIX_PROGRESS}{user_id}:summary"
    return await redis_client.delete(key)

