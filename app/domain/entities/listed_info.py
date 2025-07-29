"""Listed info entity module."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.domain.value_objects.stock_code import StockCode


@dataclass(frozen=True)
class ListedInfo:
    """上場銘柄情報エンティティ"""

    date: date
    code: StockCode
    company_name: str
    company_name_english: Optional[str]
    sector_17_code: Optional[str]
    sector_17_code_name: Optional[str]
    sector_33_code: Optional[str]
    sector_33_code_name: Optional[str]
    scale_category: Optional[str]
    market_code: Optional[str]
    market_code_name: Optional[str]
    margin_code: Optional[str]
    margin_code_name: Optional[str]

    def __post_init__(self) -> None:
        """Post initialization validation."""
        if not self.company_name:
            raise ValueError("会社名は必須です")
        if not isinstance(self.date, date):
            raise ValueError("日付は date 型である必要があります")

    @classmethod
    def from_dict(cls, data: dict) -> ListedInfo:
        """辞書から ListedInfo エンティティを作成

        Args:
            data: J-Quants API のレスポンスデータ

        Returns:
            ListedInfo instance
        """
        from datetime import datetime

        # 日付の解析
        date_str = data["Date"]
        if len(date_str) == 8:  # YYYYMMDD 形式
            listing_date = datetime.strptime(date_str, "%Y%m%d").date()
        else:  # YYYY-MM-DD 形式
            listing_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        return cls(
            date=listing_date,
            code=StockCode(data["Code"]),
            company_name=data["CompanyName"],
            company_name_english=data.get("CompanyNameEnglish"),
            sector_17_code=data.get("Sector17Code"),
            sector_17_code_name=data.get("Sector17CodeName"),
            sector_33_code=data.get("Sector33Code"),
            sector_33_code_name=data.get("Sector33CodeName"),
            scale_category=data.get("ScaleCategory"),
            market_code=data.get("MarketCode"),
            market_code_name=data.get("MarketCodeName"),
            margin_code=data.get("MarginCode"),
            margin_code_name=data.get("MarginCodeName"),
        )

    def is_same_listing(self, other: ListedInfo) -> bool:
        """同じ上場情報かどうかを判定

        Args:
            other: 比較対象の ListedInfo

        Returns:
            同じ上場情報の場合 True
        """
        return self.date == other.date and self.code == other.code