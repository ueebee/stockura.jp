"""トークンバケットアルゴリズムの実装"""
import asyncio
import time
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """トークンバケットアルゴリズムによるレート制限実装
    
    一定期間ごとにトークンが補充され、リクエスト時にトークンを消費する。
    トークンがない場合は、次のトークンが利用可能になるまで待機する。
    """
    
    def __init__(self, capacity: int, refill_period: float):
        """
        Args:
            capacity: バケットの容量（最大トークン数）
            refill_period: トークン補充期間（秒）
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        if refill_period <= 0:
            raise ValueError("Refill period must be positive")
            
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_period = refill_period
        self.refill_rate = capacity / refill_period
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
        
        logger.debug(
            f"TokenBucket initialized: capacity={capacity}, "
            f"refill_period={refill_period}s, refill_rate={self.refill_rate:.2f} tokens/s"
        )
    
    def _refill(self) -> None:
        """経過時間に基づいてトークンを補充する（内部メソッド）"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            # 経過時間に応じてトークンを補充
            refilled = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + refilled)
            self.last_refill = now
            
            if refilled > 0:
                logger.debug(
                    f"Refilled {refilled:.2f} tokens. "
                    f"Current tokens: {self.tokens:.2f}/{self.capacity}"
                )
    
    async def acquire(self, tokens: int = 1) -> None:
        """指定数のトークンを取得する（必要に応じて待機）
        
        Args:
            tokens: 取得するトークン数（デフォルト: 1）
            
        Raises:
            ValueError: 要求トークン数が容量を超える場合
        """
        if tokens > self.capacity:
            raise ValueError(f"Cannot acquire {tokens} tokens from bucket with capacity {self.capacity}")
        
        async with self._lock:
            while True:
                self._refill()
                
                if self.tokens >= tokens:
                    # トークンを消費
                    self.tokens -= tokens
                    logger.debug(f"Acquired {tokens} tokens. Remaining: {self.tokens:.2f}/{self.capacity}")
                    return
                
                # 必要なトークンが貯まるまでの待機時間を計算
                needed = tokens - self.tokens
                wait_time = needed / self.refill_rate
                
                logger.warning(
                    f"Rate limit reached. Need {needed:.2f} more tokens. "
                    f"Waiting {wait_time:.2f} seconds..."
                )
                
                # 待機
                await asyncio.sleep(wait_time)
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """指定数のトークンの取得を試みる（待機なし）
        
        Args:
            tokens: 取得を試みるトークン数（デフォルト: 1）
            
        Returns:
            トークンが取得できた場合 True 、できなかった場合 False
        """
        if tokens > self.capacity:
            return False
        
        # 非同期ロックは使用しない（try_acquire は同期的に即座に結果を返す）
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            logger.debug(f"Acquired {tokens} tokens (try). Remaining: {self.tokens:.2f}/{self.capacity}")
            return True
        
        logger.debug(f"Failed to acquire {tokens} tokens. Available: {self.tokens:.2f}/{self.capacity}")
        return False
    
    def get_wait_time(self, tokens: int = 1) -> Optional[float]:
        """指定数のトークンが利用可能になるまでの待機時間を取得
        
        Args:
            tokens: 必要なトークン数（デフォルト: 1）
            
        Returns:
            待機時間（秒）。即座に取得可能な場合は 0 、容量超過の場合は None
        """
        if tokens > self.capacity:
            return None
        
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        needed = tokens - self.tokens
        return needed / self.refill_rate
    
    @property
    def available_tokens(self) -> float:
        """現在利用可能なトークン数を取得"""
        self._refill()
        return self.tokens