"""Auth API エンドポイントのユニットテスト"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.presentation.api.v1.endpoints.auth import (
    login,
    refresh_token,
    check_auth_status,
    logout,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    get_auth_repository,
    get_auth_use_case
)
from app.domain.entities.auth import JQuantsCredentials, IdToken, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    TokenRefreshError
)


class TestAuthEndpoints:
    """Auth エンドポイントのテストクラス"""

    @pytest.fixture
    def mock_auth_use_case(self):
        """モック AuthUseCase"""
        use_case = MagicMock()
        use_case.authenticate = AsyncMock()
        use_case.get_valid_credentials = AsyncMock()
        use_case.ensure_valid_token = AsyncMock()
        use_case.refresh_token = AsyncMock()
        return use_case

    @pytest.fixture
    def mock_auth_repository(self):
        """モック AuthRepository"""
        repository = MagicMock()
        repository.delete_credentials = AsyncMock()
        return repository

    @pytest.fixture
    def sample_credentials(self):
        """サンプルの認証情報"""
        return JQuantsCredentials(
            email="test@example.com",
            password="password123",
            refresh_token=RefreshToken(value="refresh_token_value"),
            id_token=IdToken(
                value="id_token_value",
                expires_at=datetime.now() + timedelta(hours=24)
            )
        )

    @pytest.mark.asyncio
    async def test_login_success(self, mock_auth_use_case, sample_credentials):
        """ログイン成功のテスト"""
        # Arrange
        request = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        mock_auth_use_case.authenticate.return_value = sample_credentials
        
        # Act
        result = await login(request, mock_auth_use_case)
        
        # Assert
        assert result.email == "test@example.com"
        assert result.has_valid_token is True
        assert result.message == "ログインに成功しました"
        mock_auth_use_case.authenticate.assert_called_once_with(
            email="test@example.com",
            password="password123"
        )

    @pytest.mark.asyncio
    async def test_login_authentication_error(self, mock_auth_use_case):
        """ログイン認証エラーのテスト"""
        # Arrange
        request = LoginRequest(
            email="test@example.com",
            password="wrong_password"
        )
        mock_auth_use_case.authenticate.side_effect = AuthenticationError("認証に失敗しました")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(request, mock_auth_use_case)
        
        assert exc_info.value.status_code == 401
        assert "認証に失敗しました" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_unexpected_error(self, mock_auth_use_case):
        """ログイン予期しないエラーのテスト"""
        # Arrange
        request = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        mock_auth_use_case.authenticate.side_effect = Exception("Unexpected error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(request, mock_auth_use_case)
        
        assert exc_info.value.status_code == 500
        assert "ログイン処理中にエラーが発生しました" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, mock_auth_use_case, sample_credentials):
        """トークン更新成功のテスト"""
        # Arrange
        request = RefreshTokenRequest(email="test@example.com")
        mock_auth_use_case.get_valid_credentials.return_value = sample_credentials
        mock_auth_use_case.ensure_valid_token.return_value = sample_credentials
        
        # Act
        result = await refresh_token(request, mock_auth_use_case)
        
        # Assert
        assert result.email == "test@example.com"
        assert result.has_valid_token is True
        assert result.message == "トークンの更新に成功しました"
        mock_auth_use_case.get_valid_credentials.assert_called_once_with("test@example.com")
        mock_auth_use_case.ensure_valid_token.assert_called_once_with(sample_credentials)

    @pytest.mark.asyncio
    async def test_refresh_token_no_credentials(self, mock_auth_use_case):
        """認証情報なしでトークン更新のテスト"""
        # Arrange
        request = RefreshTokenRequest(email="test@example.com")
        mock_auth_use_case.get_valid_credentials.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, mock_auth_use_case)
        
        # エラーハンドリングで 500 になる実装のようです
        assert exc_info.value.status_code == 500
        assert "認証情報が見つかりません" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_refresh_error(self, mock_auth_use_case, sample_credentials):
        """トークン更新エラーのテスト"""
        # Arrange
        request = RefreshTokenRequest(email="test@example.com")
        mock_auth_use_case.get_valid_credentials.return_value = sample_credentials
        mock_auth_use_case.ensure_valid_token.side_effect = TokenRefreshError("トークンの更新に失敗しました")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, mock_auth_use_case)
        
        assert exc_info.value.status_code == 401
        assert "トークンの更新に失敗しました" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_check_auth_status_authenticated(self, mock_auth_use_case, sample_credentials):
        """認証状態確認（認証済み）のテスト"""
        # Arrange
        email = "test@example.com"
        mock_auth_use_case.get_valid_credentials.return_value = sample_credentials
        
        # Act
        result = await check_auth_status(email, mock_auth_use_case)
        
        # Assert
        assert result["email"] == email
        assert result["authenticated"] is True
        assert result["has_valid_token"] is True
        assert result["needs_refresh"] is False
        mock_auth_use_case.get_valid_credentials.assert_called_once_with(email)

    @pytest.mark.asyncio
    async def test_check_auth_status_not_authenticated(self, mock_auth_use_case):
        """認証状態確認（未認証）のテスト"""
        # Arrange
        email = "test@example.com"
        mock_auth_use_case.get_valid_credentials.return_value = None
        
        # Act
        result = await check_auth_status(email, mock_auth_use_case)
        
        # Assert
        assert result["email"] == email
        assert result["authenticated"] is False
        assert result["has_valid_token"] is False
        assert result["needs_refresh"] is True

    @pytest.mark.asyncio
    async def test_check_auth_status_expired_token(self, mock_auth_use_case):
        """認証状態確認（期限切れトークン）のテスト"""
        # Arrange
        email = "test@example.com"
        expired_credentials = JQuantsCredentials(
            email=email,
            password="password123",
            refresh_token=RefreshToken(value="refresh_token"),
            id_token=IdToken(
                value="expired_token",
                expires_at=datetime.now() - timedelta(hours=1)  # 期限切れ
            )
        )
        mock_auth_use_case.get_valid_credentials.return_value = expired_credentials
        
        # Act
        result = await check_auth_status(email, mock_auth_use_case)
        
        # Assert
        assert result["email"] == email
        assert result["authenticated"] is True
        assert result["has_valid_token"] is False
        assert result["needs_refresh"] is True

    @pytest.mark.asyncio
    async def test_check_auth_status_error(self, mock_auth_use_case):
        """認証状態確認エラーのテスト"""
        # Arrange
        email = "test@example.com"
        mock_auth_use_case.get_valid_credentials.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_auth_status(email, mock_auth_use_case)
        
        assert exc_info.value.status_code == 500
        assert "認証状態の確認中にエラーが発生しました" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_logout_success_with_redis(self, mock_auth_repository):
        """ログアウト成功（Redis）のテスト"""
        # Arrange
        request = LogoutRequest(email="test@example.com")
        mock_auth_repository.delete_credentials = AsyncMock()
        
        # Act
        result = await logout(request, mock_auth_repository)
        
        # Assert
        assert result["email"] == "test@example.com"
        assert result["message"] == "ログアウトしました"
        mock_auth_repository.delete_credentials.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_logout_success_without_delete_method(self):
        """ログアウト成功（delete_credentials メソッドなし）のテスト"""
        # Arrange
        request = LogoutRequest(email="test@example.com")
        mock_repository = AsyncMock()
        # delete_credentials メソッドが存在するため、存在しないようにする
        if hasattr(mock_repository, 'delete_credentials'):
            delattr(mock_repository, 'delete_credentials')
        
        # Act
        result = await logout(request, mock_repository)
        
        # Assert
        assert result["email"] == "test@example.com"
        assert result["message"] == "ログアウトしました"

    @pytest.mark.asyncio
    async def test_logout_error(self, mock_auth_repository):
        """ログアウトエラーのテスト"""
        # Arrange
        request = LogoutRequest(email="test@example.com")
        mock_auth_repository.delete_credentials.side_effect = Exception("Redis connection error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await logout(request, mock_auth_repository)
        
        assert exc_info.value.status_code == 500
        assert "ログアウト処理中にエラーが発生しました" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_auth_repository(self):
        """AuthRepository 取得のテスト"""
        # Arrange
        mock_redis_client = MagicMock()
        
        # Act
        with patch('app.presentation.api.v1.endpoints.auth.get_redis_client') as mock_get_redis:
            with patch('app.presentation.api.v1.endpoints.auth.RedisAuthRepository') as mock_repo_class:
                mock_get_redis.return_value = mock_redis_client
                mock_repo_class.return_value = MagicMock()
                
                repository = await get_auth_repository()
        
        # Assert
        assert repository is not None
        mock_get_redis.assert_called_once()
        mock_repo_class.assert_called_once_with(mock_redis_client)

    @pytest.mark.asyncio
    async def test_get_auth_use_case(self, mock_auth_repository):
        """AuthUseCase 取得のテスト"""
        # Act
        with patch('app.presentation.api.v1.endpoints.auth.AuthUseCase') as mock_use_case_class:
            mock_use_case_class.return_value = MagicMock()
            
            use_case = get_auth_use_case(mock_auth_repository)
        
        # Assert
        assert use_case is not None
        mock_use_case_class.assert_called_once_with(mock_auth_repository)