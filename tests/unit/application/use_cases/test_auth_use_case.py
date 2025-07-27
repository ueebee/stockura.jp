from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.auth_use_case import AuthUseCase
from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    TokenRefreshError,
)


@pytest.fixture
def mock_auth_repository():
    """モックの認証リポジトリ"""
    return MagicMock()


@pytest.fixture
def auth_use_case(mock_auth_repository):
    """テスト用の認証ユースケース"""
    return AuthUseCase(mock_auth_repository)


@pytest.fixture
def mock_refresh_token():
    """テスト用のリフレッシュトークン"""
    return RefreshToken(value="test_refresh_token")


@pytest.fixture
def mock_id_token():
    """テスト用の ID トークン"""
    return IdToken(
        value="test_id_token", expires_at=datetime.now() + timedelta(hours=24)
    )


@pytest.fixture
def mock_credentials(mock_refresh_token, mock_id_token):
    """テスト用の認証情報"""
    return JQuantsCredentials(
        email="test@example.com",
        password="password123",
        refresh_token=mock_refresh_token,
        id_token=mock_id_token,
    )


class TestAuthUseCase:
    """AuthUseCase のテスト"""

    @pytest.mark.asyncio
    async def test_authenticate_with_existing_valid_credentials(
        self, auth_use_case, mock_auth_repository, mock_credentials
    ):
        """既存の有効な認証情報がある場合の認証テスト"""
        # 既存の有効な認証情報を返すようにモックを設定
        mock_auth_repository.load_credentials = AsyncMock(
            return_value=mock_credentials
        )

        result = await auth_use_case.authenticate("test@example.com", "password123")

        # 既存の認証情報が返されることを確認
        assert result == mock_credentials
        # 新たなトークン取得が行われないことを確認
        mock_auth_repository.get_refresh_token.assert_not_called()
        mock_auth_repository.get_id_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_authenticate_new_user(
        self,
        auth_use_case,
        mock_auth_repository,
        mock_refresh_token,
        mock_id_token,
    ):
        """新規ユーザーの認証テスト"""
        # 既存の認証情報がない
        mock_auth_repository.load_credentials = AsyncMock(return_value=None)
        # 新しいトークンを取得
        mock_auth_repository.get_refresh_token = AsyncMock(
            return_value=mock_refresh_token
        )
        mock_auth_repository.get_id_token = AsyncMock(return_value=mock_id_token)
        mock_auth_repository.save_credentials = AsyncMock()

        result = await auth_use_case.authenticate("test@example.com", "password123")

        # 正しい認証情報が作成されることを確認
        assert result.email == "test@example.com"
        assert result.password == "password123"
        assert result.refresh_token == mock_refresh_token
        assert result.id_token == mock_id_token

        # 保存が呼ばれることを確認
        mock_auth_repository.save_credentials.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_failed_login(
        self, auth_use_case, mock_auth_repository
    ):
        """ログイン失敗時の認証テスト"""
        mock_auth_repository.load_credentials = AsyncMock(return_value=None)
        mock_auth_repository.get_refresh_token = AsyncMock(return_value=None)

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_use_case.authenticate("test@example.com", "wrong_password")

        assert "認証に失敗しました" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_id_token_fetch_failed(
        self, auth_use_case, mock_auth_repository, mock_refresh_token
    ):
        """ID トークン取得失敗時の認証テスト"""
        mock_auth_repository.load_credentials = AsyncMock(return_value=None)
        mock_auth_repository.get_refresh_token = AsyncMock(
            return_value=mock_refresh_token
        )
        mock_auth_repository.get_id_token = AsyncMock(return_value=None)

        with pytest.raises(TokenRefreshError) as exc_info:
            await auth_use_case.authenticate("test@example.com", "password123")

        assert "ID トークンの取得に失敗しました" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        auth_use_case,
        mock_auth_repository,
        mock_credentials,
        mock_id_token,
    ):
        """トークンリフレッシュ成功のテスト"""
        new_id_token = IdToken(
            value="new_id_token", expires_at=datetime.now() + timedelta(hours=24)
        )
        mock_auth_repository.get_id_token = AsyncMock(return_value=new_id_token)
        mock_auth_repository.save_credentials = AsyncMock()

        result = await auth_use_case.refresh_token(mock_credentials)

        # ID トークンが更新されることを確認
        assert result.id_token == new_id_token
        # 他の情報は変わらないことを確認
        assert result.email == mock_credentials.email
        assert result.password == mock_credentials.password
        assert result.refresh_token == mock_credentials.refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_without_refresh_token(
        self, auth_use_case, mock_auth_repository, mock_refresh_token, mock_id_token
    ):
        """リフレッシュトークンがない場合の再認証テスト"""
        # リフレッシュトークンがない認証情報
        credentials = JQuantsCredentials(
            email="test@example.com",
            password="password123",
            refresh_token=None,
            id_token=None,
        )

        # 再認証用のモック設定
        mock_auth_repository.load_credentials = AsyncMock(return_value=None)
        mock_auth_repository.get_refresh_token = AsyncMock(
            return_value=mock_refresh_token
        )
        mock_auth_repository.get_id_token = AsyncMock(return_value=mock_id_token)
        mock_auth_repository.save_credentials = AsyncMock()

        result = await auth_use_case.refresh_token(credentials)

        # 再認証が行われることを確認
        mock_auth_repository.get_refresh_token.assert_called_once_with(
            "test@example.com", "password123"
        )

    @pytest.mark.asyncio
    async def test_ensure_valid_token_when_needs_refresh(
        self, auth_use_case, mock_auth_repository, mock_refresh_token
    ):
        """トークン更新が必要な場合の ensure_valid_token テスト"""
        # 期限切れのトークンを持つ認証情報
        expired_token = IdToken(
            value="expired_token", expires_at=datetime.now() - timedelta(hours=1)
        )
        credentials = JQuantsCredentials(
            email="test@example.com",
            password="password123",
            id_token=expired_token,
            refresh_token=mock_refresh_token,  # リフレッシュトークンを追加
        )

        # 新しいトークン
        new_id_token = IdToken(
            value="new_id_token", expires_at=datetime.now() + timedelta(hours=24)
        )
        mock_auth_repository.get_id_token = AsyncMock(return_value=new_id_token)
        mock_auth_repository.save_credentials = AsyncMock()

        result = await auth_use_case.ensure_valid_token(credentials)

        # トークンが更新されることを確認
        assert result.id_token == new_id_token

    @pytest.mark.asyncio
    async def test_ensure_valid_token_when_valid(
        self, auth_use_case, mock_credentials
    ):
        """有効なトークンの場合の ensure_valid_token テスト"""
        result = await auth_use_case.ensure_valid_token(mock_credentials)

        # 同じ認証情報が返されることを確認
        assert result == mock_credentials

    @pytest.mark.asyncio
    async def test_get_valid_credentials_found(
        self, auth_use_case, mock_auth_repository, mock_credentials
    ):
        """有効な認証情報が見つかる場合のテスト"""
        mock_auth_repository.load_credentials = AsyncMock(
            return_value=mock_credentials
        )

        result = await auth_use_case.get_valid_credentials("test@example.com")

        assert result == mock_credentials

    @pytest.mark.asyncio
    async def test_get_valid_credentials_not_found(
        self, auth_use_case, mock_auth_repository
    ):
        """有効な認証情報が見つからない場合のテスト"""
        mock_auth_repository.load_credentials = AsyncMock(return_value=None)

        result = await auth_use_case.get_valid_credentials("test@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_valid_credentials_expired(
        self, auth_use_case, mock_auth_repository
    ):
        """期限切れの認証情報の場合のテスト"""
        # 期限切れのトークンを持つ認証情報
        expired_token = IdToken(
            value="expired_token", expires_at=datetime.now() - timedelta(hours=1)
        )
        expired_credentials = JQuantsCredentials(
            email="test@example.com",
            password="password123",
            id_token=expired_token,
        )
        mock_auth_repository.load_credentials = AsyncMock(
            return_value=expired_credentials
        )

        result = await auth_use_case.get_valid_credentials("test@example.com")

        assert result is None