"""Listed info Data Transfer Objects."""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.domain.factories.listed_info_factory import ListedInfoFactory
from app.domain.entities.listed_info import ListedInfo
from app.domain.value_objects.stock_code import StockCode


@dataclass(frozen=True)
class ListedInfoDTO:
    """上場銘柄情報の DTO"""

    date: str
    code: str
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

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ListedInfoDTO":
        """API レスポンスから DTO を作成

        Args:
            data: J-Quants API のレスポンスデータ

        Returns:
            ListedInfoDTO instance
        """
        return cls(
            date=data["Date"],
            code=data["Code"],
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

    def to_entity(self) -> ListedInfo:
        """エンティティに変換

        Returns:
            ListedInfo entity
        """
        # ListedInfoFactory を使用してエンティティを作成
        api_data = {
            "Date": self.date,
            "Code": self.code,
            "CompanyName": self.company_name,
            "CompanyNameEnglish": self.company_name_english,
            "Sector17Code": self.sector_17_code,
            "Sector17CodeName": self.sector_17_code_name,
            "Sector33Code": self.sector_33_code,
            "Sector33CodeName": self.sector_33_code_name,
            "ScaleCategory": self.scale_category,
            "MarketCode": self.market_code,
            "MarketCodeName": self.market_code_name,
            "MarginCode": self.margin_code,
            "MarginCodeName": self.margin_code_name,
        }
        return ListedInfoFactory.from_jquants_response(api_data)

    @classmethod
    def from_entity(cls, entity: ListedInfo) -> "ListedInfoDTO":
        """エンティティから DTO を作成

        Args:
            entity: ListedInfo entity

        Returns:
            ListedInfoDTO instance
        """
        return cls(
            date=entity.date.strftime("%Y-%m-%d"),
            code=entity.code.value,
            company_name=entity.company_name,
            company_name_english=entity.company_name_english,
            sector_17_code=entity.sector_17_code,
            sector_17_code_name=entity.sector_17_code_name,
            sector_33_code=entity.sector_33_code,
            sector_33_code_name=entity.sector_33_code_name,
            scale_category=entity.scale_category,
            market_code=entity.market_code,
            market_code_name=entity.market_code_name,
            margin_code=entity.margin_code,
            margin_code_name=entity.margin_code_name,
        )


@dataclass(frozen=True)
class FetchListedInfoResult:
    """上場銘柄情報取得結果の DTO"""

    success: bool
    fetched_count: int
    saved_count: int
    error_message: Optional[str] = None
    target_date: Optional[date] = None
    code: Optional[str] = None


@dataclass(frozen=True)
class ListedInfoSearchCriteria:
    """上場銘柄情報検索条件の DTO"""

    date: Optional[date] = None
    code: Optional[str] = None
    market_code: Optional[str] = None
    sector_17_code: Optional[str] = None
    sector_33_code: Optional[str] = None