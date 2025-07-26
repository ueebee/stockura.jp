"""
レート制限インターフェース

APIアクセスのレート制限を管理するインターフェース
"""

from abc import ABC, abstractmethod
from typing import Optional


class IRateLimiter(ABC):
    """レート制限インターフェース"""
    
    @abstractmethod
    async def check_rate_limit(self) -> bool:
        """
        レート制限をチェック
        
        Returns:
            bool: リクエスト可能な場合True
        """
        pass
    
    @abstractmethod
    async def wait_if_needed(self) -> None:
        """
        必要に応じて待機
        
        レート制限に達している場合、適切な時間待機する
        """
        pass
    
    @abstractmethod
    async def record_request(self) -> None:
        """
        リクエストを記録
        
        レート計算のためにリクエストを記録する
        """
        pass
    
    @abstractmethod
    async def get_remaining_requests(self) -> int:
        """
        残りリクエスト数を取得
        
        Returns:
            int: 残りのリクエスト可能数
        """
        pass
    
    @abstractmethod
    async def get_reset_time(self) -> Optional[float]:
        """
        レート制限リセット時刻を取得
        
        Returns:
            Optional[float]: リセット時刻（Unix timestamp）、制限なしの場合None
        """
        pass