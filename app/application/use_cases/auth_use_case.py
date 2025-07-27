from typing import Optional

from app.domain.entities.auth import JQuantsCredentials
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    TokenRefreshError,
)
from app.domain.repositories.auth_repository import AuthRepository


class AuthUseCase:
    """J-Quants 認証に関するユースケース"""

    def __init__(self, auth_repository: AuthRepository) -> None:
        self._auth_repository = auth_repository

    async def authenticate(self, email: str, password: str) -> JQuantsCredentials:
        """
        J-Quants アカウントで認証を行い、アクセストークンを取得

        Args:
            email: J-Quants アカウントのメールアドレス
            password: J-Quants アカウントのパスワード

        Returns:
            JQuantsCredentials: 認証済みの認証情報

        Raises:
            AuthenticationError: 認証に失敗した場合
        """
        # 既存の認証情報を確認
        existing_credentials = await self._auth_repository.load_credentials(email)
        if existing_credentials and existing_credentials.has_valid_id_token():
            return existing_credentials

        # リフレッシュトークンを取得
        refresh_token = await self._auth_repository.get_refresh_token(email, password)
        if not refresh_token:
            raise AuthenticationError("認証に失敗しました。メールアドレスまたはパスワードが正しくありません。")

        # ID トークンを取得
        id_token = await self._auth_repository.get_id_token(refresh_token)
        if not id_token:
            raise TokenRefreshError("ID トークンの取得に失敗しました。")

        # 認証情報を作成
        credentials = JQuantsCredentials(
            email=email,
            password=password,
            refresh_token=refresh_token,
            id_token=id_token,
        )

        # 認証情報を保存
        await self._auth_repository.save_credentials(credentials)

        return credentials

    async def refresh_token(self, credentials: JQuantsCredentials) -> JQuantsCredentials:
        """
        ID トークンを更新

        Args:
            credentials: 現在の認証情報

        Returns:
            JQuantsCredentials: 更新された認証情報

        Raises:
            TokenRefreshError: トークンの更新に失敗した場合
            AuthenticationError: リフレッシュトークンが無効な場合
        """
        if not credentials.refresh_token:
            # リフレッシュトークンがない場合は再認証
            return await self.authenticate(credentials.email, credentials.password)

        # ID トークンを再取得
        id_token = await self._auth_repository.get_id_token(credentials.refresh_token)
        if not id_token:
            # リフレッシュトークンが無効な場合は再認証
            return await self.authenticate(credentials.email, credentials.password)

        # 認証情報を更新
        updated_credentials = credentials.update_id_token(id_token)

        # 更新した認証情報を保存
        await self._auth_repository.save_credentials(updated_credentials)

        return updated_credentials

    async def ensure_valid_token(
        self, credentials: JQuantsCredentials
    ) -> JQuantsCredentials:
        """
        有効な ID トークンを確保（必要に応じて更新）

        Args:
            credentials: 現在の認証情報

        Returns:
            JQuantsCredentials: 有効な ID トークンを持つ認証情報

        Raises:
            TokenRefreshError: トークンの更新に失敗した場合
            AuthenticationError: 認証に失敗した場合
        """
        if credentials.needs_refresh():
            return await self.refresh_token(credentials)
        return credentials

    async def get_valid_credentials(self, email: str) -> Optional[JQuantsCredentials]:
        """
        保存された認証情報から有効な認証情報を取得

        Args:
            email: J-Quants アカウントのメールアドレス

        Returns:
            JQuantsCredentials: 有効な認証情報
            None: 有効な認証情報が見つからない場合
        """
        credentials = await self._auth_repository.load_credentials(email)
        if credentials and credentials.has_valid_id_token():
            return credentials
        return None