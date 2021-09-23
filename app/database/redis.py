# pylint: disable=redefined-builtin

from typing import Any, Optional

from aioredis import Redis, create_redis_pool

from app.config import settings


class AsyncRedisAdapter:
    def __init__(self, pool: Optional[Redis] = None) -> None:
        self.redis: Any = pool

    async def init(self) -> None:
        self.redis = self.redis or await create_redis_pool(settings.redis_url)

    async def exists(self, key: Any) -> bool:
        return await self.redis.exists(key)

    async def get(self, key: Any) -> Any:
        return await self.redis.get(key)

    async def set(self, key: Any, value: Any) -> Any:
        return await self.redis.set(key, value)

    async def zadd(self, key: Any, score: Any, member: Any) -> Any:
        return await self.redis.zadd(key, score, member)

    async def zrangebyscore(
        self, key: Any, min: Any = float('-inf'), max: Any = float('inf')
    ) -> Any:
        return await self.redis.zrangebyscore(key, min, max)

    async def zremrangebyscore(
        self, key: Any, min: Any = float('-inf'), max: Any = float('inf')
    ) -> Any:
        return await self.redis.zremrangebyscore(key, min, max)

    async def close(self) -> None:
        self.redis.close()
        await self.redis.wait_closed()


redis = AsyncRedisAdapter()
