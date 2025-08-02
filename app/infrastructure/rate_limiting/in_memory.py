"""
In-memory rate limiter implementation for development and testing
"""

import asyncio
import time
from typing import Optional

from app.domain.interfaces.rate_limiter import IRateLimiter


class InMemoryRateLimiter(IRateLimiter):
    """
    インメモリ実装のレート制限
    
    開発・テスト環境用の簡易実装
    本番環境では使用しないこと（プロセス間で状態を共有できない）
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: バケットの最大容量
            refill_rate: 秒あたりのトークン補充数
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self) -> bool:
        """
        レート制限をチェック
        
        Returns:
            bool: リクエスト可能な場合 True
        """
        async with self._lock:
            self._refill_tokens()
            return self.tokens >= 1
    
    async def wait_if_needed(self) -> None:
        """
        必要に応じて待機
        
        レート制限に達している場合、適切な時間待機する
        """
        while True:
            async with self._lock:
                self._refill_tokens()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                
                # 待機時間を計算
                tokens_needed = 1 - self.tokens
                wait_time = tokens_needed / self.refill_rate
            
            # ロックを解放してから待機
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
        async with self._lock:
            self._refill_tokens()
            return int(self.tokens)
    
    async def get_reset_time(self) -> Optional[float]:
        """
        レート制限リセット時刻を取得
        
        Returns:
            Optional[float]: バケットが満タンになる予想時刻（Unix timestamp）
        """
        async with self._lock:
            self._refill_tokens()
            
            if self.tokens >= self.capacity:
                return None
            
            # 満タンまでの時間を計算
            tokens_needed = self.capacity - self.tokens
            time_to_full = tokens_needed / self.refill_rate
            
            return time.time() + time_to_full
    
    def _refill_tokens(self) -> None:
        """
        トークンを補充する（内部メソッド）
        """
        now = time.time()
        elapsed = now - self.last_refill
        
        # トークンを補充
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now