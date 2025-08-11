"""
エラーハンドリングミドルウェア
"""

import logging
import traceback
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.presentation.exceptions.base import PresentationError
from app.presentation.schemas.responses import ErrorResponse


logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Presentation 層全体のエラーハンドリングを統一的に行うミドルウェア
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except PresentationError as e:
            # Presentation 層の例外をキャッチして統一フォーマットで返す
            logger.warning(
                f"Presentation error occurred: {e.error_code} - {e.message}",
                extra={
                    "error_code": e.error_code,
                    "path": request.url.path,
                    "method": request.method,
                    "details": e.details,
                }
            )
            
            error_response = ErrorResponse.from_error(
                error_code=e.error_code,
                message=e.message,
                details=e.details
            )
            
            # エラーコードに応じた HTTP ステータスコードを設定
            status_code = self._get_status_code(e.error_code)
            
            return JSONResponse(
                status_code=status_code,
                content=error_response.model_dump(exclude_none=True)
            )
            
        except ValueError as e:
            # ValueError は通常、不正な入力を示すので 400 を返す
            logger.warning(
                f"ValueError occurred: {str(e)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                }
            )
            
            error_response = ErrorResponse.from_error(
                error_code="VALIDATION_ERROR",
                message=str(e)
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.model_dump(exclude_none=True)
            )
            
        except Exception as e:
            # 予期しないエラーをキャッチ
            logger.error(
                f"Unexpected error occurred: {str(e)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc(),
                }
            )
            # デバッグ用に詳細なトレースバックを出力
            print(f"=== ERROR TRACEBACK ===")
            print(traceback.format_exc())
            print(f"=== END TRACEBACK ===")
            
            # 本番環境では詳細なエラー情報を隠す
            error_response = ErrorResponse.from_error(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred"
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(exclude_none=True)
            )
    
    def _get_status_code(self, error_code: str) -> int:
        """エラーコードから HTTP ステータスコードを取得"""
        from app.presentation.exceptions.http_exceptions import ERROR_STATUS_MAPPING
        
        return ERROR_STATUS_MAPPING.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)