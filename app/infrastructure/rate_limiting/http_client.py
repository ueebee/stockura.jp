"""
Rate-limited HTTP client wrapper
"""

from typing import Any, Dict, Optional, Union

import httpx

from app.domain.interfaces.rate_limiter import IRateLimiter
from app.infrastructure.http.client import HTTPClient


class RateLimitedHTTPClient(HTTPClient):
    """
    レート制限機能付き HTTP クライアント
    
    既存の AsyncHTTPClient をラップして、レート制限機能を追加
    """
    
    def __init__(
        self,
        rate_limiter: IRateLimiter,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Args:
            rate_limiter: レート制限実装
            base_url: ベース URL
            timeout: タイムアウト（秒）
            max_retries: 最大リトライ回数
            headers: デフォルトヘッダー
        """
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            headers=headers
        )
        self.rate_limiter = rate_limiter
    
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
        HTTPリクエストを実行（レート制限付き）
        
        Args:
            method: HTTPメソッド
            endpoint: エンドポイントパス
            headers: リクエストヘッダー
            params: クエリパラメータ
            json: JSONペイロード
            data: フォームデータまたはバイナリデータ
            timeout: リクエストタイムアウト（秒）
            
        Returns:
            httpx.Response: レスポンス
        """
        # レート制限チェックと待機
        await self.rate_limiter.wait_if_needed()
        
        try:
            # 実際のリクエストを実行
            response = await super().request(
                method=method,
                endpoint=endpoint,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout
            )
            
            # 成功したリクエストを記録
            await self.rate_limiter.record_request()
            
            return response
        except Exception:
            # エラー時もリクエストとしてカウント
            await self.rate_limiter.record_request()
            raise
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        現在のレート制限状態を取得
        
        Returns:
            dict: レート制限の状態情報
        """
        remaining = await self.rate_limiter.get_remaining_requests()
        reset_time = await self.rate_limiter.get_reset_time()
        
        return {
            "remaining_requests": remaining,
            "reset_time": reset_time,
            "is_limited": remaining == 0
        }