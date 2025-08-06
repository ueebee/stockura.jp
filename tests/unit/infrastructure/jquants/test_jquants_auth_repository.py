import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from aiohttp import ClientError

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    NetworkError,
    StorageError,
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
    """認証リポジトリのフィクスチャ"""
    return JQuantsAuthRepository(storage_path=".test_credentials.json")


@pytest.fixture
def mock_credentials():
    """テスト用の認証情報"""
    return JQuantsCredentials(
        email="test@example.com",
        password="testpassword",
        refresh_token=RefreshToken(value="test_refresh_token"),
        id_token=IdToken(
            value="test_id_token",
            expires_at=datetime.now() + timedelta(hours=24)
        )
    )


def create_mock_session_context(mock_response):
    """aiohttp セッションコンテキストのモックを作成するヘルパー"""
    mock_session = MagicMock()
    mock_post_context = MagicMock()
    mock_post_context.__aenter__.return_value = mock_response
    mock_post_context.__aexit__.return_value = None
    mock_session.post.return_value = mock_post_context
    return mock_session


class TestGetRefreshToken:
    """get_refresh_token メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_successful_authentication(self, auth_repository):
        """正常な認証のテスト"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            AsyncMockHelpers.setup_aiohttp_session_mock(
                mock_session_class,
                status_code=200,
                json_data={"refreshToken": "new_refresh_token"}
            )

            result = await auth_repository.get_refresh_token(
                "test@example.com", "password"
            )

            assert result is not None
            assert result.value == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_authentication_failure(self, auth_repository):
        """認証失敗のテスト"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            AsyncMockHelpers.setup_aiohttp_session_mock(
                mock_session_class,
                status_code=400,
                json_data={}
            )

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "wrong_password"
                )

            assert_authentication_error(exc_info, "メールアドレスまたはパスワードが正しくありません")

    @pytest.mark.asyncio
    async def test_network_error(self, auth_repository):
        """ネットワークエラーのテスト"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # コンテキストマネージャーのモック（エラーを発生させる）
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(side_effect=ClientError("Connection error"))
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            # セッションのモックを作成
            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_context)
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session

            with pytest.raises(NetworkError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "password"
                )

            assert_network_error(exc_info, "ネットワークエラーが発生しました")

    @pytest.mark.asyncio
    async def test_invalid_response_format(self, auth_repository):
        """不正なレスポンスフォーマットのテスト"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            AsyncMockHelpers.setup_aiohttp_session_mock(
                mock_session_class,
                status_code=200,
                json_data={"invalid": "response"}
            )

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "password"
                )

            assert_authentication_error(exc_info, "レスポンスの解析に失敗しました")


class TestGetIdToken:
    """get_id_token メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_successful_token_refresh(self, auth_repository):
        """正常なトークンリフレッシュのテスト"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            AsyncMockHelpers.setup_aiohttp_session_mock(
                mock_session_class,
                status_code=200,
                json_data={"idToken": "new_id_token"}
            )

            refresh_token = RefreshToken(value="test_refresh_token")
            result = await auth_repository.get_id_token(refresh_token)

            assert result is not None
            assert result.value == "new_id_token"
            assert result.expires_at > datetime.now()

    @pytest.mark.asyncio
    async def test_invalid_refresh_token(self, auth_repository):
        """無効なリフレッシュトークンのテスト"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            AsyncMockHelpers.setup_aiohttp_session_mock(
                mock_session_class,
                status_code=400,
                json_data={}
            )

            refresh_token = RefreshToken(value="invalid_token")

            with pytest.raises(TokenRefreshError) as exc_info:
                await auth_repository.get_id_token(refresh_token)

            assert_token_refresh_error(exc_info, "リフレッシュトークンが無効です")

    @pytest.mark.asyncio
    async def test_token_refresh_network_error(self, auth_repository):
        """トークンリフレッシュ時のネットワークエラーのテスト"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # コンテキストマネージャーのモック（エラーを発生させる）
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(side_effect=ClientError("Connection error"))
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            # セッションのモックを作成
            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_context)
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session

            refresh_token = RefreshToken(value="test_refresh_token")

            with pytest.raises(NetworkError) as exc_info:
                await auth_repository.get_id_token(refresh_token)

            assert_network_error(exc_info, "ネットワークエラーが発生しました")


class TestCredentialsPersistence:
    """認証情報の永続化関連のテスト"""

    @pytest.mark.asyncio
    async def test_save_credentials_to_memory(self, auth_repository, mock_credentials):
        """メモリへの認証情報保存のテスト"""
        await auth_repository.save_credentials(mock_credentials)

        assert auth_repository._memory_cache[mock_credentials.email] == mock_credentials

    @pytest.mark.asyncio
    async def test_save_credentials_to_file(self, mock_credentials):
        """ファイルへの認証情報保存のテスト"""
        auth_repository = JQuantsAuthRepository(storage_path=".test_credentials.json")

        mock_file = mock_open(read_data='{}')
        with patch("builtins.open", mock_file):
            await auth_repository.save_credentials(mock_credentials)

        handle = mock_file()
        written_content = ""
        for call in handle.write.call_args_list:
            written_content += call[0][0]
        
        parsed_data = json.loads(written_content)

        assert mock_credentials.email in parsed_data
        assert parsed_data[mock_credentials.email]["email"] == mock_credentials.email

    @pytest.mark.asyncio
    async def test_save_credentials_file_error(self, mock_credentials):
        """ファイル保存エラーのテスト"""
        auth_repository = JQuantsAuthRepository(storage_path="/invalid/path/test.json")

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(StorageError) as exc_info:
                await auth_repository.save_credentials(mock_credentials)

            assert "認証情報の保存に失敗しました" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_credentials_from_memory(
        self, auth_repository, mock_credentials
    ):
        """メモリからの認証情報読み込みのテスト"""
        auth_repository._memory_cache[mock_credentials.email] = mock_credentials

        result = await auth_repository.load_credentials(mock_credentials.email)

        assert result == mock_credentials

    @pytest.mark.asyncio
    async def test_load_credentials_from_file(self, mock_credentials):
        """ファイルからの認証情報読み込みのテスト"""
        auth_repository = JQuantsAuthRepository(storage_path=".test_credentials.json")

        file_data = {
            mock_credentials.email: {
                "email": mock_credentials.email,
                "password": mock_credentials.password,
                "refresh_token": mock_credentials.refresh_token.value,
                "id_token": mock_credentials.id_token.value,
                "id_token_expires_at": mock_credentials.id_token.expires_at.isoformat(),
            }
        }

        mock_file = mock_open(read_data=json.dumps(file_data))
        with patch("builtins.open", mock_file):
            result = await auth_repository.load_credentials(mock_credentials.email)

        assert result is not None
        assert result.email == mock_credentials.email
        assert result.refresh_token.value == mock_credentials.refresh_token.value

    @pytest.mark.asyncio
    async def test_load_credentials_not_found(self, auth_repository):
        """存在しない認証情報の読み込みテスト"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = await auth_repository.load_credentials("notfound@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_credentials_file_error(self):
        """ファイル読み込みエラーのテスト"""
        auth_repository = JQuantsAuthRepository(storage_path=".test_credentials.json")

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(StorageError) as exc_info:
                await auth_repository.load_credentials("test@example.com")

            assert "認証情報の読み込みに失敗しました" in str(exc_info.value)