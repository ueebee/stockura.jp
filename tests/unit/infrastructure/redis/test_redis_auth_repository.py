import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError
from redis.asyncio import Redis

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    NetworkError,
    StorageError,
    TokenRefreshError,
)
from app.infrastructure.redis.auth_repository_impl import RedisAuthRepository


@pytest.fixture
def mock_redis():
    """Redis クライアントのモック"""
    mock = AsyncMock(spec=Redis)
    # Redis メソッドを AsyncMock として設定
    mock.setex = AsyncMock()
    mock.get = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def auth_repository(mock_redis):
    """認証リポジトリのフィクスチャ"""
    return RedisAuthRepository(mock_redis)


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

        with patch("app.infrastructure.redis.auth_repository_impl.ClientSession") as mock_session_class:
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

        with patch("app.infrastructure.redis.auth_repository_impl.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(AuthenticationError) as exc_info:
                await auth_repository.get_refresh_token(
                    "test@example.com", "wrong_password"
                )

            assert "メールアドレスまたはパスワードが正しくありません" in str(exc_info.value)


class TestRedisOperations:
    """Redis 操作関連のテスト"""

    @pytest.mark.asyncio
    async def test_save_credentials(self, auth_repository, mock_redis, mock_credentials):
        """認証情報の保存テスト"""
        await auth_repository.save_credentials(mock_credentials)

        # setex が適切に呼ばれたことを確認
        expected_calls = [
            (
                f"jquants:refresh_token:{mock_credentials.email}",
                7 * 24 * 60 * 60,
                mock_credentials.refresh_token.value
            ),
            (
                f"jquants:id_token:{mock_credentials.email}",
                24 * 60 * 60,
                mock_credentials.id_token.value
            ),
            (
                f"jquants:id_token:{mock_credentials.email}:expires_at",
                24 * 60 * 60,
                mock_credentials.id_token.expires_at.isoformat()
            )
        ]

        assert mock_redis.setex.call_count >= 3
        for expected_call in expected_calls:
            mock_redis.setex.assert_any_call(*expected_call)

    @pytest.mark.asyncio
    async def test_load_credentials_found(self, auth_repository, mock_redis, mock_credentials):
        """認証情報の読み込み（存在する場合）のテスト"""
        # Redis からの返却値を設定
        mock_redis.get.side_effect = [
            json.dumps({"email": mock_credentials.email, "last_updated": datetime.now().isoformat()}),
            mock_credentials.refresh_token.value,
            mock_credentials.id_token.value,
            mock_credentials.id_token.expires_at.isoformat()
        ]

        result = await auth_repository.load_credentials(mock_credentials.email)

        assert result is not None
        assert result.email == mock_credentials.email
        assert result.refresh_token.value == mock_credentials.refresh_token.value
        assert result.id_token.value == mock_credentials.id_token.value

    @pytest.mark.asyncio
    async def test_load_credentials_not_found(self, auth_repository, mock_redis):
        """認証情報の読み込み（存在しない場合）のテスト"""
        mock_redis.get.return_value = None

        result = await auth_repository.load_credentials("notfound@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_credentials(self, auth_repository, mock_redis):
        """認証情報の削除テスト"""
        email = "test@example.com"
        await auth_repository.delete_credentials(email)

        expected_keys = [
            f"jquants:refresh_token:{email}",
            f"jquants:id_token:{email}",
            f"jquants:id_token:{email}:expires_at",
            f"jquants:credentials:{email}",
        ]

        for key in expected_keys:
            mock_redis.delete.assert_any_call(key)

    @pytest.mark.asyncio
    async def test_save_credentials_error(self, auth_repository, mock_redis, mock_credentials):
        """認証情報保存時のエラーテスト"""
        mock_redis.setex.side_effect = Exception("Redis error")

        with pytest.raises(StorageError) as exc_info:
            await auth_repository.save_credentials(mock_credentials)

        assert "認証情報の保存に失敗しました" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_credentials_error(self, auth_repository, mock_redis):
        """認証情報読み込み時のエラーテスト"""
        mock_redis.get.side_effect = Exception("Redis error")

        with pytest.raises(StorageError) as exc_info:
            await auth_repository.load_credentials("test@example.com")

        assert "認証情報の読み込みに失敗しました" in str(exc_info.value)