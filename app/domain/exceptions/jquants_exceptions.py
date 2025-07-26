"""
J-Quantsクライアント例外クラス

API通信で発生する可能性のある例外を定義
"""

from typing import Optional, Dict, Any


class JQuantsAPIException(Exception):
    """
    J-Quants API基底例外
    
    全てのJ-Quants関連例外の基底クラス
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            error_code: エラーコード
            details: 詳細情報
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        """文字列表現"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(JQuantsAPIException):
    """
    認証エラー
    
    認証に失敗した場合に発生する例外
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: Optional[str] = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class RateLimitError(JQuantsAPIException):
    """
    レート制限エラー
    
    APIのレート制限に達した場合に発生する例外
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: Optional[str] = "RATE_LIMIT",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.retry_after = retry_after  # 再試行可能になるまでの秒数


class NetworkError(JQuantsAPIException):
    """
    ネットワークエラー
    
    ネットワーク関連のエラーが発生した場合の例外
    """
    
    def __init__(
        self,
        message: str = "Network error occurred",
        error_code: Optional[str] = "NETWORK_ERROR",
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.original_error = original_error


class DataValidationError(JQuantsAPIException):
    """
    データ検証エラー
    
    APIレスポンスのデータが不正な場合に発生する例外
    """
    
    def __init__(
        self,
        message: str = "Data validation failed",
        error_code: Optional[str] = "VALIDATION_ERROR",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.field = field
        self.value = value


class ConfigurationError(JQuantsAPIException):
    """
    設定エラー
    
    クライアントの設定が不正な場合に発生する例外
    """
    
    def __init__(
        self,
        message: str = "Configuration error",
        error_code: Optional[str] = "CONFIG_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class RetryableError(JQuantsAPIException):
    """
    リトライ可能エラー
    
    リトライ可能なエラーを表す基底クラス
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        max_retries: int = 3,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.max_retries = max_retries
    
    @classmethod
    def is_retryable(cls, error: Exception) -> bool:
        """
        エラーがリトライ可能かどうかを判定
        
        Args:
            error: 判定対象のエラー
            
        Returns:
            bool: リトライ可能な場合True
        """
        # RetryableErrorのサブクラスはリトライ可能
        if isinstance(error, cls):
            return True
        
        # ネットワークエラーはリトライ可能
        if isinstance(error, NetworkError):
            return True
        
        # レート制限エラーはリトライ可能
        if isinstance(error, RateLimitError):
            return True
        
        # HTTPステータスコードが5xxの場合はリトライ可能
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            return 500 <= error.response.status_code < 600
        
        return False