from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


class AuthStrategy(ABC):
    """認証ストラテジーの基本クラス"""

    @abstractmethod
    def get_refresh_token(self, credentials: Dict[str, Any]) -> Tuple[Optional[str], Optional[datetime]]:
        """
        リフレッシュトークンを取得します。

        Args:
            credentials: 認証情報

        Returns:
            Tuple[Optional[str], Optional[datetime]]: (リフレッシュトークン, 有効期限)
        """
        pass

    @abstractmethod
    def get_id_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[datetime]]:
        """
        IDトークンを取得します。

        Args:
            refresh_token: リフレッシュトークン

        Returns:
            Tuple[Optional[str], Optional[datetime]]: (IDトークン, 有効期限)
        """
        pass

    @abstractmethod
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        認証情報が有効かどうかを検証します。

        Args:
            credentials: 認証情報

        Returns:
            bool: 認証情報が有効な場合はTrue
        """
        pass 