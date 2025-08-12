"""汎用レートリミッター実装"""
import asyncio
import functools
from typing import Callable, TypeVar, Any
from functools import wraps

from app.core.logger import get_logger
from app.infrastructure.rate_limiter.token_bucket import TokenBucket

logger = get_logger(__name__)

T = TypeVar('T')


class RateLimiter:
    """API 横断で使用可能な汎用レートリミッター
    
    トークンバケットアルゴリズムを使用してリクエストレートを制限する。
    """
    
    def __init__(self, max_requests: int, window_seconds: float, name: str = "RateLimiter"):
        """
        Args:
            max_requests: 時間窓内の最大リクエスト数
            window_seconds: 時間窓の長さ（秒）
            name: レートリミッターの名前（ログ出力用）
        """
        self.name = name
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._token_bucket = TokenBucket(max_requests, window_seconds)
        
        logger.info(
            f"{name} initialized: max_requests={max_requests}, "
            f"window={window_seconds}s ({max_requests}/{window_seconds}s = "
            f"{max_requests/window_seconds:.2f} req/s)"
        )
    
    async def acquire(self, tokens: int = 1) -> None:
        """トークンを取得（必要に応じて待機）
        
        Args:
            tokens: 取得するトークン数（デフォルト: 1）
        """
        wait_time = self._token_bucket.get_wait_time(tokens)
        if wait_time is None:
            raise ValueError(f"Cannot acquire {tokens} tokens: exceeds capacity")
        
        if wait_time > 0:
            logger.info(
                f"{self.name}: Rate limit approaching. "
                f"Waiting {wait_time:.2f}s for {tokens} token(s). "
                f"Current: {self._token_bucket.available_tokens:.1f}/{self.max_requests}"
            )
        
        await self._token_bucket.acquire(tokens)
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """トークンの取得を試みる（待機なし）
        
        Args:
            tokens: 取得を試みるトークン数（デフォルト: 1）
            
        Returns:
            トークンが取得できた場合 True 、できなかった場合 False
        """
        return self._token_bucket.try_acquire(tokens)
    
    @property
    def available_tokens(self) -> float:
        """現在利用可能なトークン数"""
        return self._token_bucket.available_tokens
    
    def get_status(self) -> dict:
        """レートリミッターの現在の状態を取得
        
        Returns:
            状態情報を含む辞書
        """
        return {
            "name": self.name,
            "available_tokens": self.available_tokens,
            "max_tokens": self.max_requests,
            "window_seconds": self.window_seconds,
            "requests_per_second": self.max_requests / self.window_seconds
        }


def with_rate_limit(limiter_getter: Callable[[Any], RateLimiter]):
    """レート制限を適用するデコレーター
    
    Args:
        limiter_getter: self から RateLimiter インスタンスを取得する関数
    
    Example:
        @with_rate_limit(lambda self: self._rate_limiter)
        async def api_call(self):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            rate_limiter = limiter_getter(self)
            await rate_limiter.acquire()
            return await func(self, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # 同期メソッド用（yfinance など）
            rate_limiter = limiter_getter(self)
            # 同期的な try_acquire を使用し、失敗した場合は警告のみ
            if not rate_limiter.try_acquire():
                logger.warning(
                    f"{rate_limiter.name}: Rate limit exceeded for sync method. "
                    f"Proceeding anyway (consider using async methods for proper rate limiting)"
                )
            return func(self, *args, **kwargs)
        
        # 関数が非同期かどうかを判定
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 簡易的な使用例
def create_rate_limiter(max_requests: int, window_seconds: float, name: str = "API") -> RateLimiter:
    """レートリミッターを作成するヘルパー関数
    
    Args:
        max_requests: 時間窓内の最大リクエスト数
        window_seconds: 時間窓の長さ（秒）
        name: レートリミッターの名前
        
    Returns:
        設定されたレートリミッター
    """
    return RateLimiter(max_requests, window_seconds, name)