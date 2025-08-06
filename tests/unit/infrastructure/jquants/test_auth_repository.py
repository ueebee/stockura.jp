import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    NetworkError,
    TokenRefreshError,
)
from app.infrastructure.repositories.external.jquants_auth_repository_impl import JQuantsAuthRepository
from tests.utils.mocks import create_mock_response
from tests.utils.assertions import (
    assert_authentication_error,
    assert_network_error,
    assert_token_refresh_error
)
from tests.utils.mock_helpers import AsyncMockHelpers


@pytest.fixture
def auth_repository():
    """テスト用の認証リポジトリを作成"""
    return JQuantsAuthRepository()


@pytest.fixture
def auth_repository_with_storage():
    """ファイルストレージ付きの認証リポジトリを作成"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        # 空の JSON オブジェクトを書き込んで初期化
        f.write("{}")
        f.flush()
        return JQuantsAuthRepository(storage_path=f.name)


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


def create_mock_session_context(mock_response):
    """aiohttp セッションコンテキストのモックを作成するヘルパー"""
    mock_session = MagicMock()
    mock_post_context = MagicMock()
    mock_post_context.__aenter__.return_value = mock_response
    mock_post_context.__aexit__.return_value = None
    mock_session.post.return_value = mock_post_context
    return mock_session


class TestJQuantsAuthRepository:
    """JQuantsAuthRepository のテスト"""

    @pytest.mark.asyncio
    async def test_get_refresh_token_success(self, auth_repository):
        """リフレッシュトークン取得成功のテスト"""
        # モックレスポンスを作成
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"refreshToken": "test_refresh_token"})
        
        # コンテキストマネージャーのモック
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # セッションのモックを作成
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.close = AsyncMock()
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await auth_repository.get_refresh_token(
                "test@example.com", "password123"
            )

            assert isinstance(result, RefreshToken)
            assert result.value == "test_refresh_token"

    @pytest.mark.asyncio
    async def test_get_refresh_token_invalid_credentials(self, auth_repository):
        """無効な認証情報でのリフレッシュトークン取得のテスト"""
        # モックレスポンスを作成
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={})
        
        # コンテキストマネージャーのモック
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # セッションのモックを作成
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.close = AsyncMock()
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "wrong_password"
                )

            assert_authentication_error(exc_info, "メールアドレスまたはパスワードが正しくありません")

    @pytest.mark.asyncio
    async def test_get_refresh_token_network_error(self, auth_repository):
        """ネットワークエラー時のリフレッシュトークン取得のテスト"""
        # コンテキストマネージャーのモック（エラーを発生させる）
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(side_effect=ClientError("Connection error"))
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # セッションのモックを作成
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.close = AsyncMock()
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(NetworkError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "password123"
                )

            assert_network_error(exc_info, "ネットワークエラーが発生しました")

    @pytest.mark.asyncio
    async def test_get_id_token_success(self, auth_repository, mock_refresh_token):
        """ID トークン取得成功のテスト"""
        # モックレスポンスを作成
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"idToken": "test_id_token"})
        
        # コンテキストマネージャーのモック
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # セッションのモックを作成
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.close = AsyncMock()
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await auth_repository.get_id_token(mock_refresh_token)

            assert isinstance(result, IdToken)
            assert result.value == "test_id_token"
            assert result.expires_at > datetime.now()

    @pytest.mark.asyncio
    async def test_get_id_token_invalid_refresh_token(
        self, auth_repository, mock_refresh_token
    ):
        """無効なリフレッシュトークンでの ID トークン取得のテスト"""
        # モックレスポンスを作成
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={})
        
        # コンテキストマネージャーのモック
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # セッションのモックを作成
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.close = AsyncMock()
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(TokenRefreshError) as exc_info:
                await auth_repository.get_id_token(mock_refresh_token)

            assert_token_refresh_error(exc_info, "リフレッシュトークンが無効です")

    @pytest.mark.asyncio
    async def test_save_credentials_memory_only(
        self, auth_repository, mock_credentials
    ):
        """認証情報のメモリ保存のテスト"""
        await auth_repository.save_credentials(mock_credentials)

        # メモリキャッシュに保存されていることを確認
        assert auth_repository._memory_cache[mock_credentials.email] == mock_credentials

    @pytest.mark.asyncio
    async def test_save_load_credentials_with_storage(
        self, auth_repository_with_storage, mock_credentials
    ):
        """認証情報のファイル保存と読み込みのテスト"""
        # 保存
        await auth_repository_with_storage.save_credentials(mock_credentials)

        # 新しいインスタンスを作成して読み込み
        new_repo = JQuantsAuthRepository(
            storage_path=auth_repository_with_storage._storage_path
        )
        loaded_credentials = await new_repo.load_credentials(mock_credentials.email)

        assert loaded_credentials is not None
        assert loaded_credentials.email == mock_credentials.email
        assert loaded_credentials.password == mock_credentials.password
        assert loaded_credentials.refresh_token.value == mock_credentials.refresh_token.value
        assert loaded_credentials.id_token.value == mock_credentials.id_token.value

    @pytest.mark.asyncio
    async def test_load_credentials_not_found(self, auth_repository):
        """存在しない認証情報の読み込みのテスト"""
        result = await auth_repository.load_credentials("nonexistent@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_credentials_expiration_check(self):
        """認証情報の有効期限チェックのテスト"""
        # 期限切れの ID トークン
        expired_token = IdToken(
            value="expired_token", expires_at=datetime.now() - timedelta(hours=1)
        )
        credentials = JQuantsCredentials(
            email="test@example.com",
            password="password123",
            id_token=expired_token,
        )

        assert not credentials.has_valid_id_token()
        assert credentials.needs_refresh()

        # 有効な ID トークン
        valid_token = IdToken(
            value="valid_token", expires_at=datetime.now() + timedelta(hours=24)
        )
        valid_credentials = credentials.update_id_token(valid_token)

        assert valid_credentials.has_valid_id_token()
        assert not valid_credentials.needs_refresh()

    @pytest.mark.asyncio
    async def test_credentials_update_tokens(
        self, mock_credentials, mock_refresh_token, mock_id_token
    ):
        """認証情報のトークン更新のテスト"""
        new_refresh_token = RefreshToken(value="new_refresh_token")
        new_id_token = IdToken(
            value="new_id_token", expires_at=datetime.now() + timedelta(hours=24)
        )

        updated_credentials = mock_credentials.update_tokens(
            new_refresh_token, new_id_token
        )

        assert updated_credentials.refresh_token.value == "new_refresh_token"
        assert updated_credentials.id_token.value == "new_id_token"
        assert updated_credentials.email == mock_credentials.email
        assert updated_credentials.password == mock_credentials.password