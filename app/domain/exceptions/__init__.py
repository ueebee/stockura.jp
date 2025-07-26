"""
ドメイン層例外クラス

J-Quantsクライアントで発生する可能性のある例外を定義
"""

from .jquants_exceptions import (
    JQuantsAPIException,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    DataValidationError,
    ConfigurationError,
    RetryableError,
)

__all__ = [
    "JQuantsAPIException",
    "AuthenticationError",
    "RateLimitError",
    "NetworkError",
    "DataValidationError",
    "ConfigurationError",
    "RetryableError",
]