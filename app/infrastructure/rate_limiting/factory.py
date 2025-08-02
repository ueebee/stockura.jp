"""
Rate limiter factory
"""

import os
from typing import Optional

from redis import asyncio as aioredis

from app.config import settings
from app.domain.interfaces.rate_limiter import IRateLimiter
from app.models.data_source import DataSource
from app.utils.rate_limit import RateLimitManager

from .in_memory import InMemoryRateLimiter
from .token_bucket import TokenBucketRateLimiter


class RateLimiterFactory:
    """レートリミッターのファクトリークラス"""
    
    _redis_client: Optional[aioredis.Redis] = None
    
    @classmethod
    async def create_for_data_source(
        cls,
        data_source: DataSource,
        use_redis: bool = True
    ) -> IRateLimiter:
        """
        データソース用のレートリミッターを作成
        
        Args:
            data_source: データソース
            use_redis: Redis を使用するかどうか
            
        Returns:
            IRateLimiter: レートリミッター実装
        """
        # レート制限設定を取得
        rate_limit_per_minute = data_source.rate_limit_per_minute
        
        # 秒あたりのレートに変換
        refill_rate = rate_limit_per_minute / 60.0
        
        # 容量はレート制限の 2 倍に設定（バースト対応）
        capacity = rate_limit_per_minute * 2
        
        if use_redis and cls._should_use_redis():
            redis_client = await cls._get_redis_client()
            key_prefix = f"rate_limit:{data_source.provider_type}:{data_source.id}"
            
            return TokenBucketRateLimiter(
                redis_client=redis_client,
                key_prefix=key_prefix,
                capacity=capacity,
                refill_rate=refill_rate
            )
        else:
            return InMemoryRateLimiter(
                capacity=capacity,
                refill_rate=refill_rate
            )
    
    @classmethod
    async def create_for_provider(
        cls,
        provider_type: str,
        use_redis: bool = True
    ) -> IRateLimiter:
        """
        プロバイダータイプ用のレートリミッターを作成
        
        Args:
            provider_type: プロバイダータイプ（"jquants", "yfinance"など）
            use_redis: Redis を使用するかどうか
            
        Returns:
            IRateLimiter: レートリミッター実装
        """
        # デフォルトのレート制限を取得
        rate_limit_str = RateLimitManager.get_rate_limit_for_provider(provider_type)
        
        # "10/m" 形式から数値を抽出
        rate_limit_per_minute = int(rate_limit_str.split("/")[0])
        
        # 秒あたりのレートに変換
        refill_rate = rate_limit_per_minute / 60.0
        
        # 容量はレート制限の 2 倍に設定（バースト対応）
        capacity = rate_limit_per_minute * 2
        
        if use_redis and cls._should_use_redis():
            redis_client = await cls._get_redis_client()
            key_prefix = f"rate_limit:{provider_type}:default"
            
            return TokenBucketRateLimiter(
                redis_client=redis_client,
                key_prefix=key_prefix,
                capacity=capacity,
                refill_rate=refill_rate
            )
        else:
            return InMemoryRateLimiter(
                capacity=capacity,
                refill_rate=refill_rate
            )
    
    @classmethod
    def _should_use_redis(cls) -> bool:
        """
        Redis を使用すべきかどうかを判定
        
        Returns:
            bool: Redis を使用する場合 True
        """
        # 環境変数で Redis の使用を制御
        use_redis = os.getenv("USE_REDIS_RATE_LIMITER", "true").lower() == "true"
        
        # テスト環境では基本的にインメモリを使用
        if os.getenv("TESTING", "false").lower() == "true":
            return False
        
        return use_redis
    
    @classmethod
    async def _get_redis_client(cls) -> aioredis.Redis:
        """
        Redis クライアントを取得（シングルトン）
        
        Returns:
            aioredis.Redis: Redis クライアント
        """
        if cls._redis_client is None:
            # Redis 接続設定を settings から取得
            redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
            
            cls._redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        
        return cls._redis_client
    
    @classmethod
    async def close_redis(cls) -> None:
        """Redis 接続をクローズ"""
        if cls._redis_client:
            await cls._redis_client.close()
            cls._redis_client = None