"""
データ転送オブジェクト (DTO)

APIレスポンスとビジネスロジック間でデータを転送するためのオブジェクト
"""

from .company import CompanyInfoDTO
from .daily_quote import DailyQuoteDTO

__all__ = [
    "CompanyInfoDTO",
    "DailyQuoteDTO",
]