from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class MarketCode(Enum):
    """市場区分コード"""

    PRIME = "0101"  # プライム市場
    STANDARD = "0102"  # スタンダード市場
    GROWTH = "0103"  # グロース市場
    OTHERS = "0104"  # その他
    PRE_PRIME = "0105"  # プライム市場（内国株式以外）
    PRE_STANDARD = "0106"  # スタンダード市場（内国株式以外）
    PRE_GROWTH = "0107"  # グロース市場（内国株式以外）
    PRO_MARKET = "0108"  # PRO Market
    OLD_TSE1 = "0109"  # 東証 1 部（旧）
    OLD_TSE2 = "0110"  # 東証 2 部（旧）
    OLD_MOTHERS = "0111"  # マザーズ（旧）
    OLD_JASDAQ_STANDARD = "0112"  # JASDAQ スタンダード（旧）
    OLD_JASDAQ_GROWTH = "0113"  # JASDAQ グロース（旧）


class SectorCode17(Enum):
    """17 業種コード"""

    FOODS = "1"  # 食品
    ENERGY_RESOURCES = "2"  # エネルギー資源
    CONSTRUCTION_MATERIALS = "3"  # 建設・資材
    MATERIALS_CHEMICALS = "4"  # 素材・化学
    PHARMACEUTICALS = "5"  # 医薬品
    AUTOMOBILES_TRANSPORTATION = "6"  # 自動車・輸送機
    STEEL_NONFERROUS = "7"  # 鉄鋼・非鉄
    MACHINERY = "8"  # 機械
    ELECTRICAL_PRECISION = "9"  # 電機・精密
    IT_COMMUNICATIONS_SERVICES = "10"  # 情報通信・サービスその他
    ELECTRIC_GAS = "11"  # 電気・ガス
    TRANSPORTATION_LOGISTICS = "12"  # 運輸・物流
    WHOLESALE_TRADE = "13"  # 卸売
    RETAIL_TRADE = "14"  # 小売
    BANKS = "15"  # 銀行
    FINANCIAL_EXCL_BANKS = "16"  # 金融（除く銀行）
    REAL_ESTATE = "17"  # 不動産


class SectorCode33(Enum):
    """33 業種コード"""

    FISHERY_AGRICULTURE_FORESTRY = "0050"  # 水産・農林業
    MINING = "1050"  # 鉱業
    CONSTRUCTION = "2050"  # 建設業
    FOODS = "3050"  # 食料品
    TEXTILES_APPARELS = "3100"  # 繊維製品
    PULP_PAPER = "3150"  # パルプ・紙
    CHEMICALS = "3200"  # 化学
    PHARMACEUTICAL = "3250"  # 医薬品
    OIL_COAL_PRODUCTS = "3300"  # 石油・石炭製品
    RUBBER_PRODUCTS = "3350"  # ゴム製品
    GLASS_CERAMICS_PRODUCTS = "3400"  # ガラス・土石製品
    IRON_STEEL = "3450"  # 鉄鋼
    NONFERROUS_METALS = "3500"  # 非鉄金属
    METAL_PRODUCTS = "3550"  # 金属製品
    MACHINERY = "3600"  # 機械
    ELECTRIC_APPLIANCES = "3650"  # 電気機器
    TRANSPORTATION_EQUIPMENT = "3700"  # 輸送用機器
    PRECISION_INSTRUMENTS = "3750"  # 精密機器
    OTHER_PRODUCTS = "3800"  # その他製品
    ELECTRIC_POWER_GAS = "4050"  # 電気・ガス業
    LAND_TRANSPORTATION = "5050"  # 陸運業
    MARINE_TRANSPORTATION = "5100"  # 海運業
    AIR_TRANSPORTATION = "5150"  # 空運業
    WAREHOUSING_HARBOR_TRANSPORTATION = "5200"  # 倉庫・運輸関連業
    INFORMATION_COMMUNICATION = "5250"  # 情報・通信業
    WHOLESALE_TRADE = "6050"  # 卸売業
    RETAIL_TRADE = "6100"  # 小売業
    BANKS = "7050"  # 銀行業
    SECURITIES_COMMODITY_FUTURES = "7100"  # 証券、商品先物取引業
    INSURANCE = "7150"  # 保険業
    OTHER_FINANCING_BUSINESS = "7200"  # その他金融業
    REAL_ESTATE = "8050"  # 不動産業
    SERVICES = "9050"  # サービス業


@dataclass(frozen=True)
class StockCode:
    """銘柄コードのバリューオブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("銘柄コードは空にできません")
        
        # 銘柄コードの長さチェック（1-10 文字）- J-Quants API は様々な形式を返す可能性がある
        if len(self.value) > 10:
            raise ValueError("銘柄コードは 10 文字以下である必要があります")
        
        # 銘柄コードの形式チェック（英数字とハイフン、アンダースコアのみ）
        if not self.value.replace('-', '').replace('_', '').isalnum():
            raise ValueError("銘柄コードは英数字、ハイフン、アンダースコアのみ使用可能です")


@dataclass(frozen=True)
class Stock:
    """銘柄情報のエンティティ"""

    code: StockCode
    company_name: str
    company_name_english: Optional[str]
    sector_17_code: Optional[SectorCode17]
    sector_17_name: Optional[str]
    sector_33_code: Optional[SectorCode33]
    sector_33_name: Optional[str]
    scale_category: Optional[str]
    market_code: Optional[MarketCode]
    market_name: Optional[str]

    def __post_init__(self) -> None:
        if not self.company_name:
            raise ValueError("会社名は必須です")

    @classmethod
    def from_dict(cls, data: dict) -> Stock:
        """辞書から銘柄情報を作成"""
        # 市場区分コードの変換
        market_code = None
        if data.get("MarketCode"):
            try:
                market_code = MarketCode(data["MarketCode"])
            except ValueError:
                # 未知の市場コードの場合は None にする
                market_code = None

        # 17 業種コードの変換
        sector_17_code = None
        if data.get("Sector17Code"):
            try:
                sector_17_code = SectorCode17(data["Sector17Code"])
            except ValueError:
                sector_17_code = None

        # 33 業種コードの変換
        sector_33_code = None
        if data.get("Sector33Code"):
            try:
                sector_33_code = SectorCode33(data["Sector33Code"])
            except ValueError:
                sector_33_code = None

        return cls(
            code=StockCode(data["Code"]),
            company_name=data["CompanyName"],
            company_name_english=data.get("CompanyNameEnglish"),
            sector_17_code=sector_17_code,
            sector_17_name=data.get("Sector17CodeName"),
            sector_33_code=sector_33_code,
            sector_33_name=data.get("Sector33CodeName"),
            scale_category=data.get("ScaleCategory"),
            market_code=market_code,
            market_name=data.get("MarketCodeName"),
        )

    def is_prime_market(self) -> bool:
        """プライム市場かどうか"""
        return self.market_code == MarketCode.PRIME

    def is_standard_market(self) -> bool:
        """スタンダード市場かどうか"""
        return self.market_code == MarketCode.STANDARD

    def is_growth_market(self) -> bool:
        """グロース市場かどうか"""
        return self.market_code == MarketCode.GROWTH


@dataclass(frozen=True)
class StockList:
    """銘柄リストのバリューオブジェクト"""

    stocks: list[Stock]
    updated_date: Optional[date] = None

    def __post_init__(self) -> None:
        if not isinstance(self.stocks, list):
            raise ValueError("stocks はリストである必要があります")

    def get_by_code(self, code: str) -> Optional[Stock]:
        """銘柄コードで銘柄を検索"""
        stock_code = StockCode(code)
        for stock in self.stocks:
            if stock.code == stock_code:
                return stock
        return None

    def filter_by_market(self, market_code: MarketCode) -> list[Stock]:
        """市場区分でフィルタリング"""
        return [stock for stock in self.stocks if stock.market_code == market_code]

    def filter_by_sector_17(self, sector_code: SectorCode17) -> list[Stock]:
        """17 業種でフィルタリング"""
        return [stock for stock in self.stocks if stock.sector_17_code == sector_code]

    def filter_by_sector_33(self, sector_code: SectorCode33) -> list[Stock]:
        """33 業種でフィルタリング"""
        return [stock for stock in self.stocks if stock.sector_33_code == sector_code]

    def search_by_name(self, keyword: str) -> list[Stock]:
        """会社名で検索（部分一致）"""
        keyword_lower = keyword.lower()
        results = []
        for stock in self.stocks:
            if keyword_lower in stock.company_name.lower():
                results.append(stock)
            elif stock.company_name_english and keyword_lower in stock.company_name_english.lower():
                results.append(stock)
        return results