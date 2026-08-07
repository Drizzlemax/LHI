"""
PANDORA Quiz Service Redis Cache
"""
import json
from typing import Any, AsyncGenerator

import redis.asyncio as redis

from src.core.config import get_settings

settings = get_settings()

# Global Redis client
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class QuizCache:
    """Redis cache for quiz data."""
    
    def __init__(self, client: redis.Redis):
        self.client = client
    
    async def get_quiz_session(self, session_id: str) -> dict | None:
        """Get quiz session from cache."""
        key = f"quiz:session:{session_id}"
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set_quiz_session(self, session_id: str, session_data: dict, ttl: int = 3600) -> None:
        """Cache quiz session."""
        key = f"quiz:session:{session_id}"
        await self.client.setex(key, ttl, json.dumps(session_data))
    
    async def delete_quiz_session(self, session_id: str) -> None:
        """Delete quiz session from cache."""
        key = f"quiz:session:{session_id}"
        await self.client.delete(key)
    
    async def get_item(self, item_id: str) -> dict | None:
        """Get quiz item from cache."""
        key = f"quiz:item:{item_id}"
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set_item(self, item_id: str, item_data: dict, ttl: int = 86400) -> None:
        """Cache quiz item."""
        key = f"quiz:item:{item_id}"
        await self.client.setex(key, ttl, json.dumps(item_data))
    
    async def increment_attempt(self, user_id: str, quiz_id: str) -> int:
        """Increment user's quiz attempt count."""
        key = f"quiz:attempts:{user_id}:{quiz_id}"
        return await self.client.incr(key)
    
    async def get_attempts(self, user_id: str, quiz_id: str) -> int:
        """Get user's quiz attempt count."""
        key = f"quiz:attempts:{user_id}:{quiz_id}"
        count = await self.client.get(key)
        return int(count) if count else 0
    
    async def reset_attempts(self, user_id: str, quiz_id: str) -> None:
        """Reset user's quiz attempts."""
        key = f"quiz:attempts:{user_id}:{quiz_id}"
        await self.client.delete(key)
