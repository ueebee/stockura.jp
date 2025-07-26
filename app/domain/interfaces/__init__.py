"""
ドメイン層インターフェース

ビジネスロジックとインフラストラクチャを分離するためのインターフェース定義
"""

from .api_client import IAPIClient
from .authentication import IAuthenticationService
from .rate_limiter import IRateLimiter

__all__ = [
    "IAPIClient",
    "IAuthenticationService",
    "IRateLimiter",
]