import asyncio
import gzip
import json
from typing import Any, Dict, Optional, TypeVar, Union

import aiohttp
from aiohttp import ClientError, ClientResponse, ClientSession

from app.domain.entities.auth import JQuantsCredentials
from app.domain.exceptions.jquants_exceptions import (
    NetworkError,
    RateLimitError,
    ValidationError,
)

T = TypeVar("T")


class JQuantsBaseClient:
    """J-Quants API 用の基底 HTTP クライアント"""

    BASE_URL = "https://api.jquants.com/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # 秒

    def __init__(self, credentials: Optional[JQuantsCredentials] = None) -> None:
        """
        Args:
            credentials: J-Quants 認証情報（認証が必要なエンドポイント用）
        """
        self._credentials = credentials
        self._session: Optional[ClientSession] = None

    async def __aenter__(self) -> "JQuantsBaseClient":
        """非同期コンテキストマネージャーの開始"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """非同期コンテキストマネージャーの終了"""
        await self.close()

    async def _ensure_session(self) -> None:
        """セッションの初期化を確実に行う"""
        if self._session is None or self._session.closed:
            self._session = ClientSession()

    async def close(self) -> None:
        """セッションのクローズ"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """リクエストヘッダーの生成"""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        }

        # 認証情報がある場合は Authorization ヘッダーを追加
        if self._credentials and self._credentials.id_token:
            headers["Authorization"] = f"Bearer {self._credentials.id_token.value}"

        # 追加ヘッダーがある場合はマージ
        if additional_headers:
            headers.update(additional_headers)

        return headers

    async def _handle_response(self, response: ClientResponse) -> Dict[str, Any]:
        """レスポンスの処理とエラーハンドリング"""
        # Gzip 圧縮されたレスポンスの処理
        content = await response.read()
        
        # Content-Encoding ヘッダーを確認
        if response.headers.get("Content-Encoding") == "gzip":
            try:
                content = gzip.decompress(content)
            except Exception as e:
                raise NetworkError(f"Gzip 解凍エラー: {str(e)}")

        # JSON のパース
        try:
            data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON パースエラー: {str(e)}")

        # ステータスコードによるエラーハンドリング
        if response.status == 429:
            raise RateLimitError("レート制限に達しました。しばらく待ってから再試行してください。")
        elif response.status >= 400:
            error_message = data.get("message", f"API エラー: ステータスコード {response.status}")
            raise NetworkError(error_message)

        return data

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """リトライ機能付き HTTP リクエスト"""
        await self._ensure_session()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(headers)

        for attempt in range(self.MAX_RETRIES):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT),
                ) as response:
                    return await self._handle_response(response)

            except RateLimitError:
                # レート制限エラーは即座に再発生
                raise
            except (ClientError, NetworkError) as e:
                # 最後の試行でない場合はリトライ
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                # 最後の試行の場合はエラーを再発生
                if isinstance(e, NetworkError):
                    raise
                raise NetworkError(f"ネットワークエラー: {str(e)}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """GET リクエスト"""
        return await self._request_with_retry("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """POST リクエスト"""
        return await self._request_with_retry(
            "POST", endpoint, params=params, json_data=json_data, headers=headers
        )

    async def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_pages: Optional[int] = None,
    ) -> list[Dict[str, Any]]:
        """ページネーション対応の GET リクエスト"""
        all_data = []
        current_params = params.copy() if params else {}
        page_count = 0

        while True:
            # ページ数制限チェック
            if max_pages and page_count >= max_pages:
                break

            # リクエスト実行
            response = await self.get(endpoint, params=current_params, headers=headers)
            
            # データを追加
            if "data" in response:
                data = response["data"]
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
            else:
                # データフィールドがない場合はレスポンス全体を追加
                all_data.append(response)

            # ページカウントをインクリメント
            page_count += 1
            
            # ページネーションキーの確認
            if "pagination_key" in response:
                current_params["pagination_key"] = response["pagination_key"]
            else:
                # ページネーションキーがない場合は終了
                break

        return all_data