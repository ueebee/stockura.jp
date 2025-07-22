"""
APIエンドポイント管理のビューモジュール
"""
from .companies import router as companies_router
from .daily_quotes import router as daily_quotes_router
from .base import (
    get_endpoint_schedule_info,
    get_endpoint_execution_stats,
    create_initial_endpoints
)

__all__ = [
    "companies_router",
    "daily_quotes_router",
    "get_endpoint_schedule_info",
    "get_endpoint_execution_stats",
    "create_initial_endpoints"
]