import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import AuthenticationError, TokenRefreshError
from app.main import app


@pytest.fixture
def client():
    """FastAPI テストクライアント"""
    return TestClient(app)


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


class TestLoginEndpoint:
    """ログインエンドポイントのテスト"""

    def test_successful_login(self, client, mock_credentials):
        """正常なログインのテスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.authenticate",
            new_callable=AsyncMock
        ) as mock_authenticate:
            mock_authenticate.return_value = mock_credentials

            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "testpassword"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["has_valid_token"] is True
            assert data["message"] == "ログインに成功しました"

    def test_login_invalid_credentials(self, client):
        """無効な認証情報でのログインテスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.authenticate",
            new_callable=AsyncMock
        ) as mock_authenticate:
            mock_authenticate.side_effect = AuthenticationError(
                "認証に失敗しました。メールアドレスまたはパスワードが正しくありません。"
            )

            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"}
            )

            assert response.status_code == 401
            assert "認証に失敗しました" in response.json()["detail"]

    def test_login_invalid_email_format(self, client):
        """無効なメールフォーマットのテスト"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "invalid-email", "password": "password"}
        )

        assert response.status_code == 422
        assert "validation error" in response.json()["detail"][0]["msg"]

    def test_login_missing_fields(self, client):
        """必須フィールド不足のテスト"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 422
        assert "field required" in response.json()["detail"][0]["msg"]

    def test_login_server_error(self, client):
        """サーバーエラーのテスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.authenticate",
            new_callable=AsyncMock
        ) as mock_authenticate:
            mock_authenticate.side_effect = Exception("Unexpected error")

            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password"}
            )

            assert response.status_code == 500
            assert "ログイン処理中にエラーが発生しました" in response.json()["detail"]


class TestRefreshTokenEndpoint:
    """トークンリフレッシュエンドポイントのテスト"""

    def test_successful_token_refresh(self, client, mock_credentials):
        """正常なトークンリフレッシュのテスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.get_valid_credentials",
            new_callable=AsyncMock
        ) as mock_get_credentials:
            mock_get_credentials.return_value = mock_credentials

            with patch(
                "app.presentation.api.v1.endpoints.auth.AuthUseCase.ensure_valid_token",
                new_callable=AsyncMock
            ) as mock_ensure_token:
                mock_ensure_token.return_value = mock_credentials

                response = client.post(
                    "/api/v1/auth/refresh",
                    json={"email": "test@example.com"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["email"] == "test@example.com"
                assert data["has_valid_token"] is True
                assert data["message"] == "トークンの更新に成功しました"

    def test_refresh_token_not_found(self, client):
        """認証情報が見つからない場合のテスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.get_valid_credentials",
            new_callable=AsyncMock
        ) as mock_get_credentials:
            mock_get_credentials.return_value = None

            response = client.post(
                "/api/v1/auth/refresh",
                json={"email": "notfound@example.com"}
            )

            assert response.status_code == 401
            assert "認証情報が見つかりません" in response.json()["detail"]

    def test_refresh_token_error(self, client, mock_credentials):
        """トークンリフレッシュエラーのテスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.get_valid_credentials",
            new_callable=AsyncMock
        ) as mock_get_credentials:
            mock_get_credentials.return_value = mock_credentials

            with patch(
                "app.presentation.api.v1.endpoints.auth.AuthUseCase.ensure_valid_token",
                new_callable=AsyncMock
            ) as mock_ensure_token:
                mock_ensure_token.side_effect = TokenRefreshError(
                    "リフレッシュトークンが無効です"
                )

                response = client.post(
                    "/api/v1/auth/refresh",
                    json={"email": "test@example.com"}
                )

                assert response.status_code == 401
                assert "リフレッシュトークンが無効です" in response.json()["detail"]


class TestAuthStatusEndpoint:
    """認証状態確認エンドポイントのテスト"""

    def test_check_auth_status_authenticated(self, client, mock_credentials):
        """認証済み状態の確認テスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.get_valid_credentials",
            new_callable=AsyncMock
        ) as mock_get_credentials:
            mock_get_credentials.return_value = mock_credentials

            response = client.get("/api/v1/auth/status/test@example.com")

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["authenticated"] is True
            assert data["has_valid_token"] is True
            assert data["needs_refresh"] is False

    def test_check_auth_status_not_authenticated(self, client):
        """未認証状態の確認テスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.get_valid_credentials",
            new_callable=AsyncMock
        ) as mock_get_credentials:
            mock_get_credentials.return_value = None

            response = client.get("/api/v1/auth/status/notfound@example.com")

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "notfound@example.com"
            assert data["authenticated"] is False
            assert data["has_valid_token"] is False
            assert data["needs_refresh"] is True

    def test_check_auth_status_expired_token(self, client):
        """期限切れトークンの状態確認テスト"""
        expired_credentials = JQuantsCredentials(
            email="test@example.com",
            password="testpassword",
            refresh_token=RefreshToken(value="test_refresh_token"),
            id_token=IdToken(
                value="test_id_token",
                expires_at=datetime.now() - timedelta(hours=1)  # 期限切れ
            )
        )

        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.get_valid_credentials",
            new_callable=AsyncMock
        ) as mock_get_credentials:
            mock_get_credentials.return_value = expired_credentials

            response = client.get("/api/v1/auth/status/test@example.com")

            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert data["has_valid_token"] is False
            assert data["needs_refresh"] is True

    def test_check_auth_status_server_error(self, client):
        """サーバーエラーのテスト"""
        with patch(
            "app.presentation.api.v1.endpoints.auth.AuthUseCase.get_valid_credentials",
            new_callable=AsyncMock
        ) as mock_get_credentials:
            mock_get_credentials.side_effect = Exception("Unexpected error")

            response = client.get("/api/v1/auth/status/test@example.com")

            assert response.status_code == 500
            assert "認証状態の確認中にエラーが発生しました" in response.json()["detail"]