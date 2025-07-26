"""
企業情報DTO

J-Quants APIから取得した企業情報を表現するデータ転送オブジェクト
"""

from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass(frozen=True)
class CompanyInfoDTO:
    """
    企業情報DTO
    
    J-Quants APIのレスポンスをビジネスロジックで扱いやすい形式に変換
    """
    # 必須フィールド
    code: str  # 銘柄コード（4桁）
    company_name: str  # 会社名
    
    # オプションフィールド
    company_name_english: Optional[str] = None  # 会社名（英語）
    sector17_code: Optional[str] = None  # 17業種コード
    sector17_code_name: Optional[str] = None  # 17業種名
    sector33_code: Optional[str] = None  # 33業種コード
    sector33_code_name: Optional[str] = None  # 33業種名
    scale_category: Optional[str] = None  # 規模区分
    market_code: Optional[str] = None  # 市場コード
    market_code_name: Optional[str] = None  # 市場名
    
    # メタデータ
    listing_date: Optional[date] = None  # 上場日
    delisting_date: Optional[date] = None  # 上場廃止日
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "code": self.code,
            "company_name": self.company_name,
            "company_name_english": self.company_name_english,
            "sector17_code": self.sector17_code,
            "sector17_code_name": self.sector17_code_name,
            "sector33_code": self.sector33_code,
            "sector33_code_name": self.sector33_code_name,
            "scale_category": self.scale_category,
            "market_code": self.market_code,
            "market_code_name": self.market_code_name,
            "listing_date": self.listing_date.isoformat() if self.listing_date else None,
            "delisting_date": self.delisting_date.isoformat() if self.delisting_date else None,
        }
    
    @classmethod
    def from_api_response(cls, data: dict) -> "CompanyInfoDTO":
        """
        APIレスポンスからDTOを生成
        
        Args:
            data: J-Quants APIのレスポンスデータ
            
        Returns:
            CompanyInfoDTO: 変換されたDTO
        """
        # 日付フィールドの変換
        listing_date = None
        if data.get("Date"):
            try:
                listing_date = date.fromisoformat(data["Date"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            code=str(data.get("Code", "")),
            company_name=data.get("CompanyName", ""),
            company_name_english=data.get("CompanyNameEnglish"),
            sector17_code=data.get("Sector17Code"),
            sector17_code_name=data.get("Sector17CodeName"),
            sector33_code=data.get("Sector33Code"),
            sector33_code_name=data.get("Sector33CodeName"),
            scale_category=data.get("ScaleCategory"),
            market_code=data.get("MarketCode"),
            market_code_name=data.get("MarketCodeName"),
            listing_date=listing_date,
        )