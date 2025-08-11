"""
HTTP 例外への変換機能
"""

from fastapi import HTTPException
from app.presentation.exceptions.base import PresentationError


# エラーコードと HTTP ステータスコードのマッピング
ERROR_STATUS_MAPPING = {
    "VALIDATION_ERROR": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "RESOURCE_NOT_FOUND": 404,
    "CONFLICT": 409,
    "INTERNAL_ERROR": 500,
    "PRESENTATION_ERROR": 500,  # デフォルト
}


def presentation_error_to_http_exception(error: PresentationError) -> HTTPException:
    """
    PresentationError を HTTPException に変換
    
    Args:
        error: PresentationError インスタンス
        
    Returns:
        HTTPException: FastAPI の HTTPException
    """
    status_code = ERROR_STATUS_MAPPING.get(error.error_code, 500)
    
    # エラーの詳細情報を構築
    detail = {
        "error_code": error.error_code,
        "message": error.message,
    }
    
    if error.details:
        detail["details"] = error.details
    
    return HTTPException(status_code=status_code, detail=detail)


def get_status_code_for_exception(exception: Exception) -> int:
    """
    例外に対応する HTTP ステータスコードを取得
    
    Args:
        exception: 例外インスタンス
        
    Returns:
        int: HTTP ステータスコード
    """
    if isinstance(exception, PresentationError):
        return ERROR_STATUS_MAPPING.get(exception.error_code, 500)
    return 500