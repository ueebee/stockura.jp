from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken


class AuthRepository(ABC):
    """J-Quants 認証リポジトリのインターフェース"""

    @abstractmethod
    async def get_refresh_token(
        self, email: str, password: str
    ) -> Optional[RefreshToken]:
        """
        メールアドレスとパスワードからリフレッシュトークンを取得

        Args:
            email: J-Quants アカウントのメールアドレス
            password: J-Quants アカウントのパスワード

        Returns:
            RefreshToken: 取得したリフレッシュトークン
            None: 認証に失敗した場合

        Raises:
            AuthenticationError: 認証エラーが発生した場合
            NetworkError: ネットワークエラーが発生した場合
        """
        pass

    @abstractmethod
    async def get_id_token(self, refresh_token: RefreshToken) -> Optional[IdToken]:
        """
        リフレッシュトークンから ID トークンを取得

        Args:
            refresh_token: 有効なリフレッシュトークン

        Returns:
            IdToken: 取得した ID トークン
            None: トークン取得に失敗した場合

        Raises:
            TokenRefreshError: トークンリフレッシュエラーが発生した場合
            NetworkError: ネットワークエラーが発生した場合
        """
        pass

    @abstractmethod
    async def save_credentials(self, credentials: JQuantsCredentials) -> None:
        """
        認証情報を永続化

        Args:
            credentials: 保存する認証情報

        Raises:
            StorageError: 保存に失敗した場合
        """
        pass

    @abstractmethod
    async def load_credentials(self, email: str) -> Optional[JQuantsCredentials]:
        """
        メールアドレスから認証情報を読み込み

        Args:
            email: J-Quants アカウントのメールアドレス

        Returns:
            JQuantsCredentials: 保存されている認証情報
            None: 認証情報が見つからない場合

        Raises:
            StorageError: 読み込みに失敗した場合
        """
        pass