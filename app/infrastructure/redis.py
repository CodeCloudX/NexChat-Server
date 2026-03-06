import redis.asyncio as redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Asynchronous Redis client wrapper for managing presence and caching.
    Optimized for cloud-hosted Redis providers like Upstash.
    """
    def __init__(self):
        self.redis = None

    async def connect(self) -> bool:
        """
        Initializes the Redis connection pool and verifies connectivity.
        Returns True if connection is successful, False otherwise.
        """
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Basic connectivity check performed only on startup
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Failed to establish Redis connection: {e}")
            self.redis = None
            return False

    async def disconnect(self):
        """
        Gracefully closes the Redis connection pool.
        """
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection pool closed.")

    async def set(self, key: str, value: str, expire: int = None):
        """
        Sets a string value in Redis with an optional expiration time (seconds).
        """
        if self.redis:
            await self.redis.set(key, value, ex=expire)

    async def get(self, key: str) -> str:
        """
        Retrieves a string value from Redis by key.
        Returns None if key does not exist or client is offline.
        """
        if self.redis:
            return await self.redis.get(key)
        return None

    async def delete(self, key: str):
        """
        Removes a specific key from Redis.
        """
        if self.redis:
            await self.redis.delete(key)

redis_client = RedisClient()
