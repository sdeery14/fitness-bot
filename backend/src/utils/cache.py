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
