"""Redis クライアントモジュール"""
import asyncio
from typing import Dict, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    """Redis クライアントのラッパークラス"""

    def __init__(self) -> None:
        # Event loop ごとに Redis クライアントを管理
        self._clients: Dict[asyncio.AbstractEventLoop, Redis] = {}

    async def connect(self) -> None:
        """Redis に接続"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop not in self._clients:
            self._clients[loop] = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections,
            )

    async def disconnect(self) -> None:
        """Redis から切断"""
        for loop, client in list(self._clients.items()):
            await client.close()
        self._clients.clear()

    @property
    def client(self) -> Redis:
        """Redis クライアントを取得"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("Redis client is not connected - no event loop running")
            
        if loop not in self._clients:
            raise RuntimeError("Redis client is not connected for current event loop")
        return self._clients[loop]

    async def __aenter__(self) -> "RedisClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()


# グローバルインスタンス
redis_client = RedisClient()


async def get_redis_client() -> Redis:
    """依存性注入用の Redis クライアント取得関数"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop not in redis_client._clients:
        await redis_client.connect()
    return redis_client.client