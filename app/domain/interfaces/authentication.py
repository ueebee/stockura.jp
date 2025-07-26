"""
認証サービスインターフェース

APIアクセスのための認証を管理するインターフェース
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from datetime import datetime


class IAuthenticationService(ABC):
    """認証サービスインターフェース"""
    
    @abstractmethod
    async def get_access_token(self) -> str:
        """
        有効なアクセストークンを取得
        
        必要に応じて自動的にトークンをリフレッシュする
        
        Returns:
            str: 有効なアクセストークン
            
        Raises:
            AuthenticationError: 認証に失敗した場合
        """
        pass
    
    @abstractmethod
    async def refresh_token(self) -> Tuple[str, datetime]:
        """
        トークンをリフレッシュ
        
        Returns:
            Tuple[str, datetime]: (新しいトークン, 有効期限)
            
        Raises:
            AuthenticationError: リフレッシュに失敗した場合
        """
        pass
    
    @abstractmethod
    async def is_token_valid(self) -> bool:
        """
        現在のトークンが有効かチェック
        
        Returns:
            bool: トークンが有効な場合True
        """
        pass
    
    @abstractmethod
    async def clear_tokens(self) -> None:
        """
        保存されているトークンをクリア
        """
        pass