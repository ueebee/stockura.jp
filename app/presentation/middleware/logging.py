"""
リクエスト/レスポンスロギングミドルウェア
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    リクエストとレスポンスのロギングを行うミドルウェア
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # リクエスト ID を生成
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 開始時刻を記録
        start_time = time.time()
        
        # リクエストログ
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )
        
        # リクエストボディのログ（デバッグレベル）
        # 注意: 本番環境では機密情報を含む可能性があるため注意が必要
        if logger.isEnabledFor(logging.DEBUG):
            try:
                # リクエストボディは一度しか読めないため、慎重に扱う
                logger.debug(
                    f"Request body logged",
                    extra={
                        "request_id": request_id,
                        "headers": dict(request.headers),
                    }
                )
            except Exception:
                pass
        
        # リクエストを処理
        response = await call_next(request)
        
        # 処理時間を計算
        process_time = time.time() - start_time
        
        # レスポンスログ
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
            }
        )
        
        # レスポンスヘッダーにリクエスト ID を追加
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    リクエスト ID を管理するミドルウェア
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # クライアントからのリクエスト ID があれば使用、なければ生成
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response