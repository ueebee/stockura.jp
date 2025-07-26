"""
リトライハンドラー

HTTPリクエストのリトライ機能を提供
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Callable, TypeVar, Any, Optional, Set, Type

from app.domain.exceptions import RetryableError, RateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """リトライ設定"""
    max_retries: int = 3  # 最大リトライ回数
    initial_delay: float = 1.0  # 初回待機時間（秒）
    max_delay: float = 60.0  # 最大待機時間（秒）
    exponential_base: float = 2.0  # 指数バックオフの基数
    jitter: bool = True  # ジッター（ランダム性）を追加するか
    retryable_exceptions: Optional[Set[Type[Exception]]] = None  # リトライ可能な例外


class ExponentialBackoff:
    """
    指数バックオフ戦略
    
    リトライ間隔を指数関数的に増加させる
    """
    
    def __init__(self, config: RetryConfig):
        """
        初期化
        
        Args:
            config: リトライ設定
        """
        self.config = config
    
    def calculate_delay(self, attempt: int) -> float:
        """
        遅延時間を計算
        
        Args:
            attempt: 試行回数（0から開始）
            
        Returns:
            float: 待機時間（秒）
        """
        # 基本的な指数バックオフ計算
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        # ジッターを追加（衝突回避のため）
        if self.config.jitter:
            delay *= random.uniform(0.5, 1.5)
        
        return delay


class RetryHandler:
    """
    リトライハンドラー
    
    失敗した操作を自動的にリトライする
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        初期化
        
        Args:
            config: リトライ設定
        """
        self.config = config or RetryConfig()
        self.backoff = ExponentialBackoff(self.config)
        
        # デフォルトのリトライ可能な例外
        self.retryable_exceptions = self.config.retryable_exceptions or {
            RetryableError,
            RateLimitError,
            asyncio.TimeoutError,
            ConnectionError,
        }
    
    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        リトライ機能付きで関数を実行
        
        Args:
            func: 実行する関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            T: 関数の戻り値
            
        Raises:
            Exception: 最大リトライ回数を超えた場合、最後の例外を再発生
        """
        last_exception: Optional[Exception] = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # 関数を実行
                logger.debug(f"Attempt {attempt + 1}/{self.config.max_retries + 1}")
                result = await func(*args, **kwargs)
                
                # 成功した場合
                if attempt > 0:
                    logger.info(f"Retry successful after {attempt} attempts")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # 最後の試行の場合はリトライしない
                if attempt >= self.config.max_retries:
                    logger.error(
                        f"Max retries ({self.config.max_retries}) exceeded. "
                        f"Last error: {e}"
                    )
                    raise
                
                # リトライ可能かチェック
                if not self._is_retryable(e):
                    logger.debug(f"Non-retryable error: {type(e).__name__}")
                    raise
                
                # レート制限エラーの特別処理
                if isinstance(e, RateLimitError) and e.retry_after:
                    delay = e.retry_after
                    logger.info(
                        f"Rate limit hit. Waiting {delay} seconds before retry..."
                    )
                else:
                    # 通常の指数バックオフ
                    delay = self.backoff.calculate_delay(attempt)
                    logger.warning(
                        f"Retryable error: {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                
                # 待機
                await asyncio.sleep(delay)
        
        # ここには到達しないはずだが、念のため
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Unexpected error in retry handler")
    
    def _is_retryable(self, error: Exception) -> bool:
        """
        エラーがリトライ可能かどうかを判定
        
        Args:
            error: 判定対象のエラー
            
        Returns:
            bool: リトライ可能な場合True
        """
        # RetryableErrorクラスの判定メソッドを使用
        if hasattr(RetryableError, "is_retryable"):
            if RetryableError.is_retryable(error):
                return True
        
        # 設定されたリトライ可能な例外をチェック
        for exc_type in self.retryable_exceptions:
            if isinstance(error, exc_type):
                return True
        
        return False
    
    def add_retryable_exception(self, exception_type: Type[Exception]) -> None:
        """
        リトライ可能な例外を追加
        
        Args:
            exception_type: 追加する例外の型
        """
        self.retryable_exceptions.add(exception_type)
    
    def remove_retryable_exception(self, exception_type: Type[Exception]) -> None:
        """
        リトライ可能な例外を削除
        
        Args:
            exception_type: 削除する例外の型
        """
        self.retryable_exceptions.discard(exception_type)