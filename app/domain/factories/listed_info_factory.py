"""Listed info factory for creating entities from external data."""
from datetime import datetime
from typing import List

from app.domain.entities.listed_info import JQuantsListedInfo
from app.domain.value_objects.stock_code import StockCode


class ListedInfoFactory:
    """J-Quants API レスポンスから JQuantsListedInfo エンティティを生成"""

    @staticmethod
    def from_jquants_response(data: dict) -> JQuantsListedInfo:
        """J-Quants API のレスポンスから JQuantsListedInfo を生成

        Args:
            data: J-Quants API のレスポンスデータ

        Returns:
            JQuantsListedInfo エンティティ
        """
        # 日付の解析
        date_str = data["Date"]
        if len(date_str) == 8:  # YYYYMMDD 形式
            listing_date = datetime.strptime(date_str, "%Y%m%d").date()
        else:  # YYYY-MM-DD 形式
            listing_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        return JQuantsListedInfo(
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

    @staticmethod
    def create_multiple(data_list: List[dict]) -> List[JQuantsListedInfo]:
        """複数の J-Quants API レスポンスから JQuantsListedInfo リストを生成"""
        return [
            ListedInfoFactory.from_jquants_response(data)
            for data in data_list
        ]