"""
J-Quants認証機能の統合テスト
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.models.data_source import DataSource
from app.services.data_source_service import DataSourceService
from app.schemas.data_source import DataSourceCreate


class TestJQuantsIntegration:
    """J-Quants認証機能の統合テスト"""

    @pytest.fixture
    def client(self):
        """テストクライアントを作成"""
        return TestClient(app)

    @pytest.fixture
    def sample_jquants_data_source(self):
        """サンプルのJ-Quantsデータソース情報"""
        return {
            "name": "Test J-Quants API",
            "description": "Test J-Quants API for integration testing",
            "provider_type": "jquants",
            "is_enabled": True,
            "base_url": "https://api.jquants.com",
            "api_version": "v1",
            "rate_limit_per_minute": 60,
            "rate_limit_per_hour": 3600,
            "rate_limit_per_day": 86400,
            "credentials": {
                "mailaddress": "test@example.com",
                "password": "testpassword"
            }
        }

    @patch('app.services.auth.strategies.jquants_strategy.httpx.Client')
    def test_refresh_token_endpoint_success(self, mock_client, client, sample_jquants_data_source):
        """リフレッシュトークン取得エンドポイントの成功テスト"""
        # HTTPレスポンスをモック
        mock_response = Mock()
        mock_response.json.return_value = {"refreshToken": "test_refresh_token"}
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        # データベースのモック
        with patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds, \
             patch('app.services.data_source_service.DataSourceService.create_data_source') as mock_create_ds, \
             patch('app.services.token_manager.get_token_manager') as mock_get_tm:

            # データソースをモック
            mock_data_source = Mock(spec=DataSource)
            mock_data_source.id = 1
            mock_data_source.provider_type = "jquants"
            mock_data_source.base_url = "https://api.jquants.com"
            mock_data_source.get_credentials.return_value = sample_jquants_data_source["credentials"]
            mock_data_source.get_refresh_token.return_value = (True, {
                "refresh_token": "test_refresh_token",
                "expired_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
            })
            
            mock_get_ds.return_value = mock_data_source
            mock_create_ds.return_value = mock_data_source

            # トークンマネージャーをモック
            mock_token_manager = Mock()
            mock_token_manager.get_valid_refresh_token = AsyncMock(return_value=None)
            mock_token_manager.store_refresh_token = AsyncMock()
            mock_get_tm.return_value = mock_token_manager

            # データソース作成
            create_response = client.post("/api/v1/data-sources/", json=sample_jquants_data_source)
            assert create_response.status_code == 200

            # リフレッシュトークン取得
            token_response = client.post("/api/v1/data-sources/1/refresh-token")
            assert token_response.status_code == 200
            
            token_data = token_response.json()
            assert token_data["token"] == "test_refresh_token"
            assert token_data["token_type"] == "refresh_token"
            assert "expired_at" in token_data

    @patch('app.services.auth.strategies.jquants_strategy.httpx.Client')
    def test_id_token_endpoint_success(self, mock_client, client, sample_jquants_data_source):
        """IDトークン取得エンドポイントの成功テスト"""
        # HTTPレスポンスをモック
        mock_response = Mock()
        mock_response.json.return_value = {"idToken": "test_id_token"}
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        # データベースのモック
        with patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds, \
             patch('app.services.token_manager.get_token_manager') as mock_get_tm:

            # データソースをモック
            mock_data_source = Mock(spec=DataSource)
            mock_data_source.id = 1
            mock_data_source.provider_type = "jquants"
            mock_data_source.base_url = "https://api.jquants.com"
            mock_data_source.get_id_token.return_value = (True, {
                "id_token": "test_id_token",
                "expired_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            })
            
            mock_get_ds.return_value = mock_data_source

            # トークンマネージャーをモック
            mock_token_manager = Mock()
            mock_token_manager.get_valid_id_token = AsyncMock(return_value=None)
            mock_token_manager.store_id_token = AsyncMock()
            mock_get_tm.return_value = mock_token_manager

            # IDトークン取得
            token_response = client.post(
                "/api/v1/data-sources/1/id-token",
                json={"refresh_token": "test_refresh_token"}
            )
            assert token_response.status_code == 200
            
            token_data = token_response.json()
            assert token_data["token"] == "test_id_token"
            assert token_data["token_type"] == "id_token"
            assert "expired_at" in token_data

    def test_token_status_endpoint(self, client):
        """トークン状態取得エンドポイントのテスト"""
        with patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds, \
             patch('app.services.token_manager.get_token_manager') as mock_get_tm:

            # データソースをモック
            mock_data_source = Mock(spec=DataSource)
            mock_data_source.id = 1
            mock_get_ds.return_value = mock_data_source

            # トークンマネージャーをモック
            mock_token_manager = Mock()
            mock_token_manager.get_token_status = AsyncMock(return_value={
                "data_source_id": 1,
                "refresh_token": {
                    "exists": True,
                    "expired_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    "is_valid": True
                },
                "id_token": {
                    "exists": False
                }
            })
            mock_get_tm.return_value = mock_token_manager

            # トークン状態取得
            response = client.get("/api/v1/data-sources/1/token-status")
            assert response.status_code == 200
            
            status_data = response.json()
            assert status_data["data_source_id"] == 1
            assert status_data["refresh_token"]["exists"] is True
            assert status_data["refresh_token"]["is_valid"] is True
            assert status_data["id_token"]["exists"] is False

    def test_clear_tokens_endpoint(self, client):
        """トークンクリアエンドポイントのテスト"""
        with patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds, \
             patch('app.services.token_manager.get_token_manager') as mock_get_tm:

            # データソースをモック
            mock_data_source = Mock(spec=DataSource)
            mock_data_source.id = 1
            mock_get_ds.return_value = mock_data_source

            # トークンマネージャーをモック
            mock_token_manager = Mock()
            mock_token_manager.clear_tokens = AsyncMock()
            mock_get_tm.return_value = mock_token_manager

            # トークンクリア
            response = client.post("/api/v1/data-sources/1/clear-tokens")
            assert response.status_code == 200
            
            response_data = response.json()
            assert response_data["message"] == "Tokens cleared successfully"
            
            # clear_tokensが呼ばれたことを確認
            mock_token_manager.clear_tokens.assert_called_once_with(1)

    def test_api_token_endpoint(self, client):
        """APIトークン取得エンドポイントのテスト"""
        with patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds, \
             patch('app.services.data_source_service.DataSourceService.get_valid_api_token') as mock_get_token:

            # データソースをモック
            mock_data_source = Mock(spec=DataSource)
            mock_data_source.id = 1
            mock_get_ds.return_value = mock_data_source

            # APIトークンをモック
            mock_get_token.return_value = "valid_api_token"

            # APIトークン取得
            response = client.get("/api/v1/data-sources/1/api-token")
            assert response.status_code == 200
            
            response_data = response.json()
            assert response_data["token"] == "valid_api_token"
            assert response_data["token_type"] == "id_token"

    def test_refresh_token_endpoint_not_found(self, client):
        """存在しないデータソースでのリフレッシュトークン取得テスト"""
        with patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds:
            mock_get_ds.return_value = None

            # 存在しないデータソースでリフレッシュトークン取得
            response = client.post("/api/v1/data-sources/999/refresh-token")
            assert response.status_code == 404
            assert "Data source not found" in response.json()["detail"]

    def test_id_token_endpoint_missing_refresh_token(self, client):
        """リフレッシュトークンが不足している場合のIDトークン取得テスト"""
        # リフレッシュトークンなしでIDトークン取得
        response = client.post("/api/v1/data-sources/1/id-token", json={})
        assert response.status_code == 400
        assert "refresh_token is required" in response.json()["detail"]

    @patch('app.services.auth.strategies.jquants_strategy.httpx.Client')
    def test_authentication_failure(self, mock_client, client, sample_jquants_data_source):
        """認証失敗のテスト"""
        # HTTPエラーをモック
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Authentication failed")
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        with patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds, \
             patch('app.services.token_manager.get_token_manager') as mock_get_tm:

            # データソースをモック
            mock_data_source = Mock(spec=DataSource)
            mock_data_source.id = 1
            mock_data_source.provider_type = "jquants"
            mock_data_source.base_url = "https://api.jquants.com"
            mock_data_source.get_credentials.return_value = sample_jquants_data_source["credentials"]
            mock_data_source.get_refresh_token.return_value = (False, {"error": "Authentication failed"})
            
            mock_get_ds.return_value = mock_data_source

            # トークンマネージャーをモック
            mock_token_manager = Mock()
            mock_token_manager.get_valid_refresh_token = AsyncMock(return_value=None)
            mock_get_tm.return_value = mock_token_manager

            # リフレッシュトークン取得（失敗）
            response = client.post("/api/v1/data-sources/1/refresh-token")
            assert response.status_code == 404
            assert "token retrieval failed" in response.json()["detail"]

    def test_complete_authentication_flow(self, client, sample_jquants_data_source):
        """完全な認証フローのテスト"""
        with patch('app.services.auth.strategies.jquants_strategy.httpx.Client') as mock_client, \
             patch('app.services.data_source_service.DataSourceService.get_data_source') as mock_get_ds, \
             patch('app.services.data_source_service.DataSourceService.create_data_source') as mock_create_ds, \
             patch('app.services.token_manager.get_token_manager') as mock_get_tm:

            # HTTPレスポンスをモック（リフレッシュトークン）
            refresh_response = Mock()
            refresh_response.json.return_value = {"refreshToken": "test_refresh_token"}
            refresh_response.raise_for_status.return_value = None
            
            # HTTPレスポンスをモック（IDトークン）
            id_response = Mock()
            id_response.json.return_value = {"idToken": "test_id_token"}
            id_response.raise_for_status.return_value = None
            
            mock_client.return_value.__enter__.return_value.post.side_effect = [refresh_response, id_response]

            # データソースをモック
            mock_data_source = Mock(spec=DataSource)
            mock_data_source.id = 1
            mock_data_source.provider_type = "jquants"
            mock_data_source.base_url = "https://api.jquants.com"
            mock_data_source.get_credentials.return_value = sample_jquants_data_source["credentials"]
            
            refresh_expired_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
            id_expired_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            
            mock_data_source.get_refresh_token.return_value = (True, {
                "refresh_token": "test_refresh_token",
                "expired_at": refresh_expired_at
            })
            mock_data_source.get_id_token.return_value = (True, {
                "id_token": "test_id_token",
                "expired_at": id_expired_at
            })
            
            mock_get_ds.return_value = mock_data_source
            mock_create_ds.return_value = mock_data_source

            # トークンマネージャーをモック
            mock_token_manager = Mock()
            mock_token_manager.get_valid_refresh_token = AsyncMock(return_value=None)
            mock_token_manager.get_valid_id_token = AsyncMock(return_value=None)
            mock_token_manager.store_refresh_token = AsyncMock()
            mock_token_manager.store_id_token = AsyncMock()
            mock_get_tm.return_value = mock_token_manager

            # 1. データソース作成
            create_response = client.post("/api/v1/data-sources/", json=sample_jquants_data_source)
            assert create_response.status_code == 200

            # 2. リフレッシュトークン取得
            refresh_response = client.post("/api/v1/data-sources/1/refresh-token")
            assert refresh_response.status_code == 200
            refresh_data = refresh_response.json()
            assert refresh_data["token"] == "test_refresh_token"

            # 3. IDトークン取得
            id_response = client.post(
                "/api/v1/data-sources/1/id-token",
                json={"refresh_token": "test_refresh_token"}
            )
            assert id_response.status_code == 200
            id_data = id_response.json()
            assert id_data["token"] == "test_id_token"

            # トークンが適切に保存されたことを確認
            mock_token_manager.store_refresh_token.assert_called_once()
            mock_token_manager.store_id_token.assert_called_once()