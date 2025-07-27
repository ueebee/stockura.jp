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
from app.infrastructure.jquants.auth_repository_impl import JQuantsAuthRepository


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


class TestGetRefreshToken:
    """get_refresh_token メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_successful_authentication(self, auth_repository):
        """正常な認証のテスト"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"refreshToken": "new_refresh_token"}
        )

        with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response

            result = await auth_repository.get_refresh_token(
                "test@example.com", "password"
            )

            assert result is not None
            assert result.value == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_authentication_failure(self, auth_repository):
        """認証失敗のテスト"""
        mock_response = AsyncMock()
        mock_response.status = 400

        with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "wrong_password"
                )

            assert "メールアドレスまたはパスワードが正しくありません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error(self, auth_repository):
        """ネットワークエラーのテスト"""
        with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.side_effect = ClientError("Connection error")
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            with pytest.raises(NetworkError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "password"
                )

            assert "ネットワークエラーが発生しました" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_response_format(self, auth_repository):
        """不正なレスポンスフォーマットのテスト"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"invalid": "response"})

        with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "password"
                )

            assert "レスポンスの解析に失敗しました" in str(exc_info.value)


class TestGetIdToken:
    """get_id_token メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_successful_token_refresh(self, auth_repository):
        """正常なトークンリフレッシュのテスト"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"idToken": "new_id_token"})

        with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            refresh_token = RefreshToken(value="test_refresh_token")
            result = await auth_repository.get_id_token(refresh_token)

            assert result is not None
            assert result.value == "new_id_token"
            assert result.expires_at > datetime.now()

    @pytest.mark.asyncio
    async def test_invalid_refresh_token(self, auth_repository):
        """無効なリフレッシュトークンのテスト"""
        mock_response = AsyncMock()
        mock_response.status = 400

        with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            refresh_token = RefreshToken(value="invalid_token")

            with pytest.raises(TokenRefreshError) as exc_info:
                await auth_repository.get_id_token(refresh_token)

            assert "リフレッシュトークンが無効です" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_token_refresh_network_error(self, auth_repository):
        """トークンリフレッシュ時のネットワークエラーのテスト"""
        with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.side_effect = ClientError("Connection error")
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            refresh_token = RefreshToken(value="test_refresh_token")

            with pytest.raises(NetworkError) as exc_info:
                await auth_repository.get_id_token(refresh_token)

            assert "ネットワークエラーが発生しました" in str(exc_info.value)


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