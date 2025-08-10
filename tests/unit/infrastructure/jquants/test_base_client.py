import asyncio
import gzip
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    NetworkError,
    RateLimitError,
    ValidationError,
)
from app.infrastructure.external_services.jquants.base_client import JQuantsBaseClient


@pytest.fixture
def mock_credentials():
    """テスト用の認証情報"""
    return JQuantsCredentials(
        email="test@example.com",
        password="password123",
        refresh_token=RefreshToken(value="test_refresh_token"),
        id_token=IdToken(
            value="test_id_token", expires_at=datetime.now() + timedelta(hours=24)
        ),
    )


@pytest.fixture
async def client():
    """テスト用のクライアント"""
    client = JQuantsBaseClient()
    yield client
    await client.close()


@pytest.fixture
async def auth_client(mock_credentials):
    """認証情報付きのテスト用クライアント"""
    client = JQuantsBaseClient(credentials=mock_credentials)
    yield client
    await client.close()


class TestJQuantsBaseClient:
    """JQuantsBaseClient のテスト"""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """コンテキストマネージャーのテスト"""
        async with JQuantsBaseClient() as client:
            assert client._session is not None
            assert not client._session.closed

    @pytest.mark.asyncio
    async def test_headers_without_auth(self, client):
        """認証情報なしのヘッダー生成テスト"""
        headers = client._get_headers()
        assert headers["Accept"] == "application/json"
        assert headers["Accept-Encoding"] == "gzip"
        assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_headers_with_auth(self, auth_client):
        """認証情報ありのヘッダー生成テスト"""
        headers = auth_client._get_headers()
        assert headers["Authorization"] == "Bearer test_id_token"

    @pytest.mark.asyncio
    async def test_get_request_success(self, client):
        """GET リクエスト成功のテスト"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(
            return_value=json.dumps({"data": "test_data"})
        )

        with patch.object(client, "_ensure_session", AsyncMock()):
            client._session = MagicMock()
            client._session.request.return_value.__aenter__.return_value = mock_response

            result = await client.get("/test")
            assert result == {"data": "test_data"}

    @pytest.mark.asyncio
    async def test_post_request_success(self, client):
        """POST リクエスト成功のテスト"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(
            return_value=json.dumps({"success": True})
        )

        with patch.object(client, "_ensure_session", AsyncMock()):
            client._session = MagicMock()
            client._session.request.return_value.__aenter__.return_value = mock_response

            result = await client.post("/test", json_data={"key": "value"})
            assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_gzip_response_handling(self, client):
        """Gzip 圧縮レスポンスの処理テスト"""
        test_data = {"data": "compressed_data"}
        compressed_data = gzip.compress(json.dumps(test_data).encode())

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Encoding": "gzip"}
        mock_response.text = AsyncMock(return_value=json.dumps(test_data))

        result = await client._handle_response(mock_response)
        assert result == test_data

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, client):
        """レート制限エラーのテスト"""
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value=json.dumps({}))

        with pytest.raises(RateLimitError) as exc_info:
            await client._handle_response(mock_response)
        assert "レート制限に達しました" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error(self, client):
        """ネットワークエラーのテスト"""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.headers = {}
        mock_response.text = AsyncMock(
            return_value=json.dumps({"message": "Internal Server Error"})
        )

        with pytest.raises(NetworkError) as exc_info:
            await client._handle_response(mock_response)
        assert "Internal Server Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_json_parse_error(self, client):
        """JSON パースエラーのテスト"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="invalid json")

        with pytest.raises(ValidationError) as exc_info:
            await client._handle_response(mock_response)
        assert "JSON パースエラー" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, client):
        """ネットワークエラー時のリトライテスト"""
        # 最初の 2 回は失敗、 3 回目で成功
        side_effects = [
            ClientError("Connection error"),
            ClientError("Connection error"),
            MagicMock(
                status=200,
                headers={},
                text=AsyncMock(
                    return_value=json.dumps({"data": "success"})
                ),
            ),
        ]

        with patch.object(client, "_ensure_session", AsyncMock()):
            client._session = MagicMock()
            mock_request = MagicMock()
            mock_request.__aenter__.side_effect = side_effects
            client._session.request.return_value = mock_request

            # リトライ遅延をモック
            with patch("asyncio.sleep", AsyncMock()):
                result = await client.get("/test")
                assert result == {"data": "success"}
                assert client._session.request.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client):
        """最大リトライ回数超過のテスト"""
        with patch.object(client, "_ensure_session", AsyncMock()):
            client._session = MagicMock()
            client._session.request.side_effect = ClientError("Connection error")

            with patch("asyncio.sleep", AsyncMock()):
                with pytest.raises(NetworkError) as exc_info:
                    await client.get("/test")
                assert "ネットワークエラー" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_pagination_single_page(self, client):
        """単一ページのページネーションテスト"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.read = AsyncMock(
            return_value=json.dumps({"data": [{"id": 1}, {"id": 2}]}).encode()
        )

        with patch.object(client, "get", AsyncMock()) as mock_get:
            mock_get.return_value = {"data": [{"id": 1}, {"id": 2}]}

            result = await client.get_paginated("/test")
            assert result == [{"id": 1}, {"id": 2}]
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_pagination_multiple_pages(self, client):
        """複数ページのページネーションテスト"""
        # モックレスポンス
        page1 = {"data": [{"id": 1}], "pagination_key": "key1"}
        page2 = {"data": [{"id": 2}], "pagination_key": "key2"}
        page3 = {"data": [{"id": 3}]}  # 最後のページ

        # get メソッドをより詳細にモック
        call_count = 0
        async def mock_get_side_effect(endpoint, params=None, headers=None):
            nonlocal call_count
            # パラメータに基づいて適切なページを返す
            if params and "pagination_key" in params:
                if params["pagination_key"] == "key1":
                    result = page2
                elif params["pagination_key"] == "key2":
                    result = page3
                else:
                    result = page1
            else:
                result = page1
            call_count += 1
            return result

        with patch.object(client, "get", AsyncMock(side_effect=mock_get_side_effect)) as mock_get:
            result = await client.get_paginated("/test")
            assert result == [{"id": 1}, {"id": 2}, {"id": 3}]
            assert mock_get.call_count == 3


    @pytest.mark.asyncio
    async def test_pagination_with_max_pages(self, client):
        """最大ページ数制限付きページネーションテスト"""
        # モックレスポンス
        pages = [
            {"data": [{"id": i}], "pagination_key": f"key{i}"}
            for i in range(1, 10)
        ]

        with patch.object(client, "get", AsyncMock()) as mock_get:
            mock_get.side_effect = pages

            result = await client.get_paginated("/test", max_pages=3)
            assert len(result) == 3
            assert result == [{"id": 1}, {"id": 2}, {"id": 3}]
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_session_reuse(self, client):
        """セッションの再利用テスト"""
        await client._ensure_session()
        session1 = client._session

        await client._ensure_session()
        session2 = client._session

        assert session1 is session2

    @pytest.mark.asyncio
    async def test_session_recreation_after_close(self, client):
        """セッションクローズ後の再作成テスト"""
        await client._ensure_session()
        session1 = client._session

        await client.close()
        await client._ensure_session()
        session2 = client._session

        assert session1 is not session2