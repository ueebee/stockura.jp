"""Listed info entity module."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.domain.value_objects.stock_code import StockCode


@dataclass(frozen=True)
class JQuantsListedInfo:
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

    def is_same_listing(self, other: JQuantsListedInfo) -> bool:
        """同じ上場情報かどうかを判定

        Args:
            other: 比較対象の JQuantsListedInfo

        Returns:
            同じ上場情報の場合 True
        """
        return self.date == other.date and self.code == other.code

    def is_prime_market(self) -> bool:
        """プライム市場銘柄かどうか"""
        return self.market_code == "0111"

    def is_standard_market(self) -> bool:
        """スタンダード市場銘柄かどうか"""
        return self.market_code == "0112"

    def is_growth_market(self) -> bool:
        """グロース市場銘柄かどうか"""
        return self.market_code == "0113"

    def belongs_to_sector_17(self, sector_code: str) -> bool:
        """指定された 17 業種に属するか

        Args:
            sector_code: 17 業種コード

        Returns:
            該当する場合 True
        """
        return self.sector_17_code == sector_code

    def belongs_to_sector_33(self, sector_code: str) -> bool:
        """指定された 33 業種に属するか

        Args:
            sector_code: 33 業種コード

        Returns:
            該当する場合 True
        """
        return self.sector_33_code == sector_code

    def is_marginable(self) -> bool:
        """信用取引が可能かどうか"""
        return self.margin_code == "1"

    def is_large_cap(self) -> bool:
        """大型株かどうか（TOPIX Large70）"""
        return self.scale_category == "TOPIX Large70"

    def is_mid_cap(self) -> bool:
        """中型株かどうか（TOPIX Mid400）"""
        return self.scale_category == "TOPIX Mid400"

    def is_small_cap(self) -> bool:
        """小型株かどうか（TOPIX Small）"""
        return self.scale_category == "TOPIX Small"