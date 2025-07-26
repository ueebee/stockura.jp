"""
汎用HTTPクライアント

httpxを使用した非同期HTTP通信を提供
"""

import logging
from typing import Optional, Dict, Any, Union
from contextlib import asynccontextmanager

import httpx

from app.domain.exceptions import NetworkError, RetryableError
from .retry_handler import RetryHandler, RetryConfig

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    汎用HTTPクライアント
    
    リトライ機能とエラーハンドリングを備えた非同期HTTPクライアント
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
        default_headers: Optional[Dict[str, str]] = None
    ):
        """
        初期化
        
        Args:
            base_url: APIのベースURL
            timeout: リクエストタイムアウト（秒）
            retry_config: リトライ設定
            default_headers: デフォルトヘッダー
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_handler = RetryHandler(retry_config or RetryConfig())
        self.default_headers = default_headers or {}
        self._client: Optional[httpx.AsyncClient] = None
    
    @asynccontextmanager
    async def _get_client(self):
        """HTTPクライアントを取得（コンテキストマネージャー）"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=self.default_headers,
                follow_redirects=True
            )
        try:
            yield self._client
        except Exception:
            # エラーが発生した場合はクライアントを閉じる
            if self._client:
                await self._client.aclose()
                self._client = None
            raise
    
    async def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        HTTPリクエストを実行（リトライ機能付き）
        
        Args:
            method: HTTPメソッド（GET, POST, PUT, DELETE等）
            endpoint: エンドポイントパス
            headers: リクエストヘッダー
            params: クエリパラメータ
            json: JSONペイロード
            data: フォームデータまたはバイナリデータ
            timeout: リクエストタイムアウト（秒）
            
        Returns:
            httpx.Response: HTTPレスポンス
            
        Raises:
            NetworkError: ネットワークエラー
            RetryableError: リトライ可能なエラー
        """
        url = f"{endpoint}" if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
        
        # ヘッダーをマージ
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        # リトライハンドラーを使用してリクエストを実行
        return await self.retry_handler.execute_with_retry(
            self._make_request,
            method=method,
            url=url,
            headers=request_headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout or self.timeout
        )
    
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        data: Optional[Union[Dict[str, Any], bytes]],
        timeout: float
    ) -> httpx.Response:
        """
        実際のHTTPリクエストを実行
        
        Args:
            method: HTTPメソッド
            url: 完全なURL
            headers: リクエストヘッダー
            params: クエリパラメータ
            json: JSONペイロード
            data: フォームデータまたはバイナリデータ
            timeout: タイムアウト
            
        Returns:
            httpx.Response: HTTPレスポンス
            
        Raises:
            NetworkError: ネットワークエラー
        """
        try:
            async with self._get_client() as client:
                logger.debug(f"Making {method} request to {url}")
                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    data=data,
                    timeout=timeout
                )
                
                # HTTPエラーステータスの場合は例外を発生
                response.raise_for_status()
                
                logger.debug(f"Request successful: {response.status_code}")
                return response
                
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {url}")
            raise NetworkError(
                message=f"Request timeout: {url}",
                error_code="TIMEOUT",
                original_error=e,
                details={"url": url, "timeout": timeout}
            )
        except httpx.NetworkError as e:
            logger.error(f"Network error: {e}")
            raise NetworkError(
                message=f"Network error occurred: {str(e)}",
                error_code="NETWORK_ERROR",
                original_error=e,
                details={"url": url}
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            
            # 5xxエラーはリトライ可能
            if 500 <= e.response.status_code < 600:
                raise RetryableError(
                    message=f"Server error: {e.response.status_code}",
                    error_code=f"HTTP_{e.response.status_code}",
                    details={
                        "url": url,
                        "status_code": e.response.status_code,
                        "response_text": e.response.text
                    }
                )
            # その他のHTTPエラーはNetworkErrorとして扱う
            raise NetworkError(
                message=f"HTTP error: {e.response.status_code}",
                error_code=f"HTTP_{e.response.status_code}",
                original_error=e,
                details={
                    "url": url,
                    "status_code": e.response.status_code,
                    "response_text": e.response.text
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise NetworkError(
                message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR",
                original_error=e,
                details={"url": url}
            )
    
    async def get(
        self,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """GETリクエスト"""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(
        self,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """POSTリクエスト"""
        return await self.request("POST", endpoint, **kwargs)
    
    async def put(
        self,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """PUTリクエスト"""
        return await self.request("PUT", endpoint, **kwargs)
    
    async def delete(
        self,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """DELETEリクエスト"""
        return await self.request("DELETE", endpoint, **kwargs)
    
    async def close(self) -> None:
        """クライアントを閉じる"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリー"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self.close()