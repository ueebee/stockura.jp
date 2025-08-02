"""
Token Bucket rate limiter implementation using Redis
"""

import asyncio
import time
from typing import Optional

from redis import asyncio as aioredis

from app.domain.interfaces.rate_limiter import IRateLimiter


class TokenBucketRateLimiter(IRateLimiter):
    """
    Redis ベースのトークンバケットアルゴリズムによるレート制限実装
    
    トークンバケットアルゴリズム:
    - 固定サイズのバケットにトークンを一定速度で追加
    - リクエストごとにトークンを消費
    - トークンが不足している場合は待機
    """
    
    def __init__(
        self,
        redis_client: aioredis.Redis,
        key_prefix: str,
        capacity: int,
        refill_rate: float,
        ttl: int = 3600
    ):
        """
        Args:
            redis_client: Redis クライアント
            key_prefix: Redis キーのプレフィックス
            capacity: バケットの最大容量
            refill_rate: 秒あたりのトークン補充数
            ttl: Redis キーの TTL（秒）
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.ttl = ttl
        
        # Lua スクリプトを事前に定義
        self._lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local tokens_requested = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        local ttl = tonumber(ARGV[5])
        
        -- 現在のバケット状態を取得
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now
        
        -- トークンを補充
        local elapsed = now - last_refill
        local tokens_to_add = elapsed * refill_rate
        tokens = math.min(capacity, tokens + tokens_to_add)
        
        -- リクエストを処理できるか判定
        if tokens >= tokens_requested then
            tokens = tokens - tokens_requested
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, ttl)
            return {1, tokens, 0}  -- {allowed, remaining_tokens, wait_time}
        else
            -- 待機時間を計算
            local tokens_needed = tokens_requested - tokens
            local wait_time = tokens_needed / refill_rate
            
            -- 現在のトークン数を更新（補充分のみ）
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, ttl)
            return {0, tokens, wait_time}
        end
        """
    
    async def check_rate_limit(self) -> bool:
        """
        レート制限をチェック
        
        Returns:
            bool: リクエスト可能な場合 True
        """
        result = await self._execute_lua_script(tokens_requested=1, consume=False)
        return bool(result[0])
    
    async def wait_if_needed(self) -> None:
        """
        必要に応じて待機
        
        レート制限に達している場合、適切な時間待機する
        """
        while True:
            result = await self._execute_lua_script(tokens_requested=1, consume=True)
            allowed, remaining_tokens, wait_time = result
            
            if allowed:
                return
            
            # 待機時間に少しマージンを追加
            await asyncio.sleep(wait_time + 0.01)
    
    async def record_request(self) -> None:
        """
        リクエストを記録
        
        レート計算のためにリクエストを記録する
        """
        # wait_if_needed でトークンが消費されるため、ここでは何もしない
        pass
    
    async def get_remaining_requests(self) -> int:
        """
        残りリクエスト数を取得
        
        Returns:
            int: 残りのリクエスト可能数
        """
        result = await self._execute_lua_script(tokens_requested=0, consume=False)
        _, remaining_tokens, _ = result
        return int(remaining_tokens)
    
    async def get_reset_time(self) -> Optional[float]:
        """
        レート制限リセット時刻を取得
        
        Returns:
            Optional[float]: バケットが満タンになる予想時刻（Unix timestamp）
        """
        result = await self._execute_lua_script(tokens_requested=0, consume=False)
        _, remaining_tokens, _ = result
        
        if remaining_tokens >= self.capacity:
            return None
        
        # 満タンまでの時間を計算
        tokens_needed = self.capacity - remaining_tokens
        time_to_full = tokens_needed / self.refill_rate
        
        return time.time() + time_to_full
    
    async def _execute_lua_script(
        self,
        tokens_requested: int,
        consume: bool
    ) -> tuple[int, float, float]:
        """
        Lua スクリプトを実行
        
        Args:
            tokens_requested: 要求するトークン数
            consume: トークンを実際に消費するかどうか
            
        Returns:
            tuple: (allowed, remaining_tokens, wait_time)
        """
        key = f"{self.key_prefix}:bucket"
        
        # consume が False の場合は、トークンを消費しないようにする
        if not consume:
            # 状態確認用の別スクリプトを使用
            check_script = """
            local key = KEYS[1]
            local capacity = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1]) or capacity
            local last_refill = tonumber(bucket[2]) or now
            
            -- トークンを補充（表示用）
            local elapsed = now - last_refill
            local tokens_to_add = elapsed * refill_rate
            tokens = math.min(capacity, tokens + tokens_to_add)
            
            return {tokens >= 1 and 1 or 0, tokens, 0}
            """
            
            result = await self.redis.eval(
                check_script,
                1,
                key,
                self.capacity,
                self.refill_rate,
                time.time()
            )
        else:
            result = await self.redis.eval(
                self._lua_script,
                1,
                key,
                self.capacity,
                self.refill_rate,
                tokens_requested,
                time.time(),
                self.ttl
            )
        
        return tuple(result)