"""
テスト用 HTTP クライアントフィクスチャ

FastAPI アプリケーションのテスト用に、様々な認証状態の
HTTP クライアントを提供します。
"""

import logging
from typing import Any, Dict, Optional

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import FastAPI

from app.main import app as fastapi_app
from app.core.security import create_access_token
from tests.settings.test_config import test_settings

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncClient:
    """
    基本的なテストクライアント
    
    認証なしで API エンドポイントにアクセスするために使用します。
    """
    async with AsyncClient(
        app=fastapi_app,
        base_url="http://testserver",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function") 
async def auth_client(test_client: AsyncClient) -> AsyncClient:
    """
    認証済みテストクライアント
    
    JWT トークンを含む Authorization ヘッダーが設定されています。
    """
    # テスト用のユーザー情報
    test_user_data = {
        "sub": "test@example.com",
        "user_id": "test_user_123",
        "scopes": ["read", "write"],
    }
    
    # アクセストークン生成
    access_token = create_access_token(data=test_user_data)
    
    # Authorization ヘッダーを設定
    test_client.headers["Authorization"] = f"Bearer {access_token}"
    
    return test_client


@pytest_asyncio.fixture(scope="function")
async def admin_client(test_client: AsyncClient) -> AsyncClient:
    """
    管理者権限付きテストクライアント
    
    管理者権限が必要なエンドポイントのテスト用。
    """
    # 管理者用のユーザー情報
    admin_user_data = {
        "sub": "admin@example.com",
        "user_id": "admin_user_123",
        "scopes": ["read", "write", "admin"],
        "is_admin": True,
    }
    
    # アクセストークン生成
    access_token = create_access_token(data=admin_user_data)
    
    # Authorization ヘッダーを設定
    test_client.headers["Authorization"] = f"Bearer {access_token}"
    
    return test_client


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
        
        access_token = create_access_token(data=token_data)
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