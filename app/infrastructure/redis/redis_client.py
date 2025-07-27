"""Redis クライアントモジュール"""
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    """Redis クライアントのラッパークラス"""

    def __init__(self) -> None:
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Redis に接続"""
        if not self._client:
            self._client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections,
            )

    async def disconnect(self) -> None:
        """Redis から切断"""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> Redis:
        """Redis クライアントを取得"""
        if not self._client:
            raise RuntimeError("Redis client is not connected")
        return self._client

    async def __aenter__(self) -> "RedisClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()


# グローバルインスタンス
redis_client = RedisClient()


async def get_redis_client() -> Redis:
    """依存性注入用の Redis クライアント取得関数"""
    if not redis_client._client:
        await redis_client.connect()
    return redis_client.client