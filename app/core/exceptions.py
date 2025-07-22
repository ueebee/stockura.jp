"""
同期処理関連の例外クラス定義
"""
from typing import Optional, Dict, Any


class SyncError(Exception):
    """同期処理の基底例外クラス"""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "SYNC_ERROR"
        self.details = details or {}


class APIError(SyncError):
    """API関連のエラー"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        
        super().__init__(message, code="API_ERROR", details=details)
        self.status_code = status_code
        self.response_body = response_body


class DataValidationError(SyncError):
    """データ検証エラー"""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        
        super().__init__(message, code="DATA_VALIDATION_ERROR", details=details)
        self.field = field
        self.value = value


class RateLimitError(APIError):
    """レート制限エラー"""
    
    def __init__(
        self, 
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """認証エラー"""
    
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=401, details=details)


class DataSourceNotFoundError(SyncError):
    """データソースが見つからないエラー"""
    
    def __init__(
        self, 
        data_source_id: int,
        message: Optional[str] = None
    ):
        message = message or f"Data source with ID {data_source_id} not found"
        super().__init__(
            message, 
            code="DATA_SOURCE_NOT_FOUND",
            details={"data_source_id": data_source_id}
        )
        self.data_source_id = data_source_id


class SyncAlreadyInProgressError(SyncError):
    """同期処理が既に実行中のエラー"""
    
    def __init__(
        self, 
        sync_type: str,
        message: Optional[str] = None
    ):
        message = message or f"{sync_type} sync is already in progress"
        super().__init__(
            message, 
            code="SYNC_ALREADY_IN_PROGRESS",
            details={"sync_type": sync_type}
        )
        self.sync_type = sync_type