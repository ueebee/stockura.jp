"""
テスト用 HTTP クライアントフィクスチャ

FastAPI アプリケーションのテスト用に、様々な認証状態の
HTTP クライアントを提供します。
"""

import logging
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app as fastapi_app
from tests.settings.test_config import test_settings
from tests.utils.mocks import create_mock_aiohttp_session, create_mock_redis_client

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def test_client() -> TestClient:
    """
    基本的なテストクライアント（同期版）
    
    認証なしで API エンドポイントにアクセスするために使用します。
    FastAPI の TestClient を使用します。
    """
    client = TestClient(fastapi_app)
    client.headers["Content-Type"] = "application/json"
    return client


@pytest.fixture(scope="function")
def auth_client() -> TestClient:
    """
    認証済みテストクライアント
    
    JWT トークンを含む Authorization ヘッダーが設定されています。
    """
    client = TestClient(fastapi_app)
    client.headers["Content-Type"] = "application/json"
    
    # テスト用の固定トークン
    access_token = "test_access_token_123"
    
    # Authorization ヘッダーを設定
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    return client


@pytest.fixture(scope="function")
def admin_client() -> TestClient:
    """
    管理者権限付きテストクライアント
    
    管理者権限が必要なエンドポイントのテスト用。
    """
    client = TestClient(fastapi_app)
    client.headers["Content-Type"] = "application/json"
    
    # 管理者用の固定トークン
    access_token = "admin_access_token_123"
    
    # Authorization ヘッダーを設定
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    return client


@pytest.fixture
def make_auth_headers():
    """
    カスタム認証ヘッダーを生成するファクトリー
    
    使用例:
        headers = make_auth_headers(user_id="custom_user", scopes=["read"])
    """
    def _make_headers(
        user_id: str = "test_user",
        email: str = "test@example.com",
        scopes: list = None,
        **kwargs
    ) -> Dict[str, str]:
        if scopes is None:
            scopes = ["read", "write"]
        
        token_data = {
            "sub": email,
            "user_id": user_id,
            "scopes": scopes,
            **kwargs
        }
        
        # テスト用の固定トークン生成
        access_token = f"test_token_{user_id}_{email}"
        return {"Authorization": f"Bearer {access_token}"}
    
    return _make_headers


class TestClientWrapper:
    """
    テストクライアントのラッパークラス
    
    便利なヘルパーメソッドを提供します。
    """
    
    def __init__(self, client: AsyncClient):
        self.client = client
    
    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """JSON レスポンスを取得"""
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def post_json(self, url: str, json: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """JSON データを POST"""
        response = await self.client.post(url, json=json, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def put_json(self, url: str, json: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """JSON データを PUT"""
        response = await self.client.put(url, json=json, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def delete(self, url: str, **kwargs) -> None:
        """リソースを削除"""
        response = await self.client.delete(url, **kwargs)
        response.raise_for_status()
    
    async def assert_status(self, url: str, expected_status: int, method: str = "GET", **kwargs) -> None:
        """ステータスコードをアサート"""
        request_method = getattr(self.client, method.lower())
        response = await request_method(url, **kwargs)
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"


@pytest_asyncio.fixture
async def client_wrapper(test_client: AsyncClient) -> TestClientWrapper:
    """テストクライアントラッパー"""
    return TestClientWrapper(test_client)


@pytest_asyncio.fixture
async def auth_client_wrapper(auth_client: AsyncClient) -> TestClientWrapper:
    """認証済みテストクライアントラッパー"""
    return TestClientWrapper(auth_client)


# API レスポンスのモックヘルパー
@pytest.fixture
def mock_api_response(mocker):
    """
    外部 API レスポンスをモックするヘルパー
    
    使用例:
        mock_api_response("app.infrastructure.jquants.client", {"data": "mocked"})
    """
    def _mock_response(module_path: str, response_data: Any, status_code: int = 200):
        mock = mocker.patch(f"{module_path}.get")
        mock.return_value.status_code = status_code
        mock.return_value.json.return_value = response_data
        return mock
    
    return _mock_response


# 共通モックフィクスチャ
@pytest.fixture
def mock_aiohttp_session():
    """aiohttp Session のモック"""
    with patch("aiohttp.ClientSession") as mock:
        session = create_mock_aiohttp_session()
        mock.return_value.__aenter__.return_value = session
        yield session


@pytest.fixture
def mock_redis_client():
    """Redis クライアントのモック"""
    return create_mock_redis_client()


# テスト用のリクエストコンテキスト
@pytest.fixture
def request_context():
    """
    リクエストコンテキスト情報を提供
    
    テスト中のリクエストに関する情報を保持します。
    """
    return {
        "client_ip": "127.0.0.1",
        "user_agent": "TestClient/1.0",
        "request_id": "test-request-123",
    }