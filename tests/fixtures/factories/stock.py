"""
株式関連のテストファクトリー

株式エンティティのテストデータを生成します。
"""

from datetime import date

import factory

from app.domain.entities.stock import (
    MarketCode,
    SectorCode17,
    SectorCode33,
    Stock,
    StockCode,
    StockList,
)
from tests.fixtures.factories.base import BaseFactory


class StockCodeFactory(factory.Factory):
    """銘柄コードのファクトリー"""
    
    class Meta:
        model = StockCode
    
    value = factory.Sequence(lambda n: f"{1000 + n:04d}")


class StockFactory(factory.Factory):
    """株式情報のファクトリー"""
    
    class Meta:
        model = Stock
    
    code = factory.SubFactory(StockCodeFactory)
    company_name = factory.Faker("company", locale="ja_JP")
    company_name_english = factory.Faker("company")
    sector_17_code = factory.Faker(
        "random_element",
        elements=list(SectorCode17)
    )
    sector_17_name = factory.LazyAttribute(
        lambda obj: _get_sector_17_name(obj.sector_17_code)
    )
    sector_33_code = factory.Faker(
        "random_element",
        elements=list(SectorCode33)
    )
    sector_33_name = factory.LazyAttribute(
        lambda obj: _get_sector_33_name(obj.sector_33_code)
    )
    scale_category = factory.Faker(
        "random_element",
        elements=["TOPIX Large70", "TOPIX Mid400", "TOPIX Small", "その他"]
    )
    market_code = factory.Faker(
        "random_element",
        elements=list(MarketCode)
    )
    market_name = factory.LazyAttribute(
        lambda obj: _get_market_name(obj.market_code)
    )
    
    class Params:
        # トヨタ自動車のテストデータ
        toyota = factory.Trait(
            code=factory.SubFactory(StockCodeFactory, value="7203"),
            company_name="トヨタ自動車",
            company_name_english="Toyota Motor Corporation",
            sector_17_code=SectorCode17.AUTOMOBILES_TRANSPORTATION,
            sector_17_name="自動車・輸送機",
            sector_33_code=SectorCode33.TRANSPORTATION_EQUIPMENT,
            sector_33_name="輸送用機器",
            scale_category="TOPIX Large70",
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
        # プライム市場銘柄
        prime = factory.Trait(
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
        # スタンダード市場銘柄
        standard = factory.Trait(
            market_code=MarketCode.STANDARD,
            market_name="スタンダード市場"
        )
        # グロース市場銘柄
        growth = factory.Trait(
            market_code=MarketCode.GROWTH,
            market_name="グロース市場"
        )


class StockListFactory(factory.Factory):
    """銘柄リストのファクトリー"""
    
    class Meta:
        model = StockList
    
    stocks = factory.List([
        factory.SubFactory(StockFactory) for _ in range(3)
    ])
    updated_date = factory.Faker("date_this_year")
    
    @factory.post_generation
    def add_stocks(obj, create, extracted, **kwargs):
        """追加の銘柄を生成"""
        if extracted:
            for stock in extracted:
                obj.stocks.append(stock)


def _get_sector_17_name(sector_code):
    """17 業種コードから業種名を取得"""
    sector_names = {
        SectorCode17.FOODS: "食品",
        SectorCode17.ENERGY_RESOURCES: "エネルギー資源",
        SectorCode17.CONSTRUCTION_MATERIALS: "建設・資材",
        SectorCode17.MATERIALS_CHEMICALS: "素材・化学",
        SectorCode17.PHARMACEUTICALS: "医薬品",
        SectorCode17.AUTOMOBILES_TRANSPORTATION: "自動車・輸送機",
        SectorCode17.STEEL_NONFERROUS: "鉄鋼・非鉄",
        SectorCode17.MACHINERY: "機械",
        SectorCode17.ELECTRICAL_PRECISION: "電機・精密",
        SectorCode17.IT_COMMUNICATIONS_SERVICES: "情報通信・サービスその他",
        SectorCode17.ELECTRIC_GAS: "電気・ガス",
        SectorCode17.TRANSPORTATION_LOGISTICS: "運輸・物流",
        SectorCode17.WHOLESALE_TRADE: "卸売",
        SectorCode17.RETAIL_TRADE: "小売",
        SectorCode17.BANKS: "銀行",
        SectorCode17.FINANCIAL_EXCL_BANKS: "金融（除く銀行）",
        SectorCode17.REAL_ESTATE: "不動産",
    }
    return sector_names.get(sector_code, "その他")


def _get_sector_33_name(sector_code):
    """33 業種コードから業種名を取得"""
    # 簡略化のため一部のみ実装
    sector_names = {
        SectorCode33.FOODS: "食料品",
        SectorCode33.CHEMICALS: "化学",
        SectorCode33.PHARMACEUTICAL: "医薬品",
        SectorCode33.MACHINERY: "機械",
        SectorCode33.ELECTRIC_APPLIANCES: "電気機器",
        SectorCode33.TRANSPORTATION_EQUIPMENT: "輸送用機器",
        SectorCode33.BANKS: "銀行業",
        SectorCode33.REAL_ESTATE: "不動産業",
        SectorCode33.SERVICES: "サービス業",
    }
    return sector_names.get(sector_code, "その他")


def _get_market_name(market_code):
    """市場コードから市場名を取得"""
    market_names = {
        MarketCode.PRIME: "プライム市場",
        MarketCode.STANDARD: "スタンダード市場",
        MarketCode.GROWTH: "グロース市場",
        MarketCode.OTHERS: "その他",
        MarketCode.PRO_MARKET: "PRO Market",
        MarketCode.OLD_TSE1: "東証 1 部（旧）",
        MarketCode.OLD_TSE2: "東証 2 部（旧）",
        MarketCode.OLD_MOTHERS: "マザーズ（旧）",
        MarketCode.OLD_JASDAQ_STANDARD: "JASDAQ スタンダード（旧）",
        MarketCode.OLD_JASDAQ_GROWTH: "JASDAQ グロース（旧）",
    }
    return market_names.get(market_code, "その他")