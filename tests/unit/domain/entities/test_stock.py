"""
株式エンティティのテスト（新テスト環境版）

FactoryBoy を使用してテストデータ作成を簡素化しています。
"""

import pytest
from datetime import date

from app.domain.entities.stock import (
    MarketCode,
    SectorCode17,
    SectorCode33,
    Stock,
    StockCode,
    StockList,
)
from tests.fixtures.factories.stock import StockCodeFactory, StockFactory, StockListFactory


@pytest.mark.unit
class TestStockCode:
    """StockCode のテスト"""

    def test_valid_stock_code(self):
        """有効な銘柄コード"""
        code = StockCodeFactory.build(value="7203")
        assert code.value == "7203"

    def test_empty_stock_code(self):
        """空の銘柄コード"""
        with pytest.raises(ValueError) as exc_info:
            StockCode("")
        assert "銘柄コードは空にできません" in str(exc_info.value)

    def test_invalid_length_stock_code(self):
        """長さが不正な銘柄コード"""
        with pytest.raises(ValueError) as exc_info:
            StockCode("123")
        assert "銘柄コードは 4 桁の数字である必要があります" in str(exc_info.value)

    def test_non_digit_stock_code(self):
        """数字以外を含む銘柄コード"""
        with pytest.raises(ValueError) as exc_info:
            StockCode("12AB")
        assert "銘柄コードは 4 桁の数字である必要があります" in str(exc_info.value)


@pytest.mark.unit
class TestStock:
    """Stock エンティティのテスト"""

    def test_create_stock_with_factory(self):
        """ファクトリーを使った銘柄情報の作成"""
        # トヨタ自動車のトレイトを使用
        stock = StockFactory.build(toyota=True)
        
        assert stock.code.value == "7203"
        assert stock.company_name == "トヨタ自動車"
        assert stock.company_name_english == "Toyota Motor Corporation"
        assert stock.sector_17_code == SectorCode17.AUTOMOBILES_TRANSPORTATION
        assert stock.sector_33_code == SectorCode33.TRANSPORTATION_EQUIPMENT
        assert stock.market_code == MarketCode.PRIME
        assert stock.is_prime_market()
        assert not stock.is_standard_market()
        assert not stock.is_growth_market()

    def test_create_random_stock(self):
        """ランダムな銘柄情報の作成"""
        stock = StockFactory.build()
        
        # 必須フィールドが設定されていることを確認
        assert stock.code
        assert stock.company_name
        assert stock.market_code in list(MarketCode)
        assert stock.sector_17_code in list(SectorCode17)
        assert stock.sector_33_code in list(SectorCode33)

    def test_create_stock_without_company_name(self):
        """会社名なしの銘柄情報"""
        with pytest.raises(ValueError) as exc_info:
            StockFactory.build(company_name="")
        assert "会社名は必須です" in str(exc_info.value)

    def test_stock_from_dict(self):
        """辞書から銘柄情報を作成"""
        data = {
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
            "CompanyNameEnglish": "TOYOTA MOTOR CORPORATION",
            "Sector17Code": "6",
            "Sector17CodeName": "自動車・輸送機",
            "Sector33Code": "3700",
            "Sector33CodeName": "輸送用機器",
            "ScaleCategory": "TOPIX Large70",
            "MarketCode": "0101",
            "MarketCodeName": "プライム",
        }

        stock = Stock.from_dict(data)
        assert stock.code.value == "7203"
        assert stock.company_name == "トヨタ自動車"
        assert stock.sector_17_code == SectorCode17.AUTOMOBILES_TRANSPORTATION
        assert stock.sector_33_code == SectorCode33.TRANSPORTATION_EQUIPMENT
        assert stock.market_code == MarketCode.PRIME

    def test_stock_from_dict_with_invalid_codes(self):
        """無効なコードを含む辞書から銘柄情報を作成"""
        data = {
            "Code": "9999",
            "CompanyName": "テスト会社",
            "MarketCode": "9999",  # 無効な市場コード
            "Sector17Code": "99",  # 無効な業種コード
            "Sector33Code": "9999",  # 無効な業種コード
        }

        stock = Stock.from_dict(data)
        assert stock.code.value == "9999"
        assert stock.company_name == "テスト会社"
        assert stock.market_code is None
        assert stock.sector_17_code is None
        assert stock.sector_33_code is None

    def test_market_specific_stocks(self):
        """市場別の銘柄作成"""
        # プライム市場
        prime_stock = StockFactory.build(prime=True)
        assert prime_stock.market_code == MarketCode.PRIME
        assert prime_stock.is_prime_market()

        # スタンダード市場
        standard_stock = StockFactory.build(standard=True)
        assert standard_stock.market_code == MarketCode.STANDARD
        assert standard_stock.is_standard_market()

        # グロース市場
        growth_stock = StockFactory.build(growth=True)
        assert growth_stock.market_code == MarketCode.GROWTH
        assert growth_stock.is_growth_market()


@pytest.mark.unit
class TestStockList:
    """StockList のテスト"""

    @pytest.fixture
    def sample_stock_list(self):
        """ファクトリーを使ったテスト用銘柄リスト"""
        # 特定の銘柄を作成
        toyota = StockFactory.build(toyota=True)
        sony = StockFactory.build(
            code=StockCodeFactory.build(value="6758"),
            company_name="ソニーグループ",
            company_name_english="Sony Group Corporation",
            sector_17_code=SectorCode17.ELECTRICAL_PRECISION,
            sector_17_name="電機・精密",
            sector_33_code=SectorCode33.ELECTRIC_APPLIANCES,
            sector_33_name="電気機器",
            scale_category="TOPIX Large70",
            market_code=MarketCode.PRIME,
            market_name="プライム",
        )
        mitsukoshi = StockFactory.build(
            code=StockCodeFactory.build(value="3099"),
            company_name="三越伊勢丹ホールディングス",
            company_name_english="Isetan Mitsukoshi Holdings Ltd.",
            sector_17_code=SectorCode17.RETAIL_TRADE,
            sector_17_name="小売",
            sector_33_code=SectorCode33.RETAIL_TRADE,
            sector_33_name="小売業",
            scale_category="TOPIX Mid400",
            market_code=MarketCode.PRIME,
            market_name="プライム",
        )
        
        return StockListFactory.build(
            stocks=[toyota, sony, mitsukoshi],
            updated_date=date(2024, 1, 1)
        )

    def test_create_stock_list_with_factory(self):
        """ファクトリーを使った銘柄リストの作成"""
        stock_list = StockListFactory.build()
        assert len(stock_list.stocks) >= 3
        assert stock_list.updated_date
        assert all(isinstance(stock, Stock) for stock in stock_list.stocks)

    def test_create_stock_list_invalid_type(self):
        """無効な型での銘柄リスト作成"""
        with pytest.raises(ValueError) as exc_info:
            StockList(stocks="not a list")
        assert "stocks はリストである必要があります" in str(exc_info.value)

    def test_get_by_code(self, sample_stock_list):
        """銘柄コードで検索"""
        stock = sample_stock_list.get_by_code("7203")
        assert stock is not None
        assert stock.company_name == "トヨタ自動車"
        
        stock = sample_stock_list.get_by_code("9999")
        assert stock is None

    def test_filter_by_market(self, sample_stock_list):
        """市場区分でフィルタリング"""
        prime_stocks = sample_stock_list.filter_by_market(MarketCode.PRIME)
        assert len(prime_stocks) == 3
        
        standard_stocks = sample_stock_list.filter_by_market(MarketCode.STANDARD)
        assert len(standard_stocks) == 0

    def test_filter_by_sector_17(self, sample_stock_list):
        """17 業種でフィルタリング"""
        auto_stocks = sample_stock_list.filter_by_sector_17(SectorCode17.AUTOMOBILES_TRANSPORTATION)
        assert len(auto_stocks) == 1
        assert auto_stocks[0].company_name == "トヨタ自動車"

    def test_filter_by_sector_33(self, sample_stock_list):
        """33 業種でフィルタリング"""
        electric_stocks = sample_stock_list.filter_by_sector_33(SectorCode33.ELECTRIC_APPLIANCES)
        assert len(electric_stocks) == 1
        assert electric_stocks[0].company_name == "ソニーグループ"

    def test_search_by_name(self, sample_stock_list):
        """会社名で検索"""
        # 日本語名で検索
        results = sample_stock_list.search_by_name("トヨタ")
        assert len(results) == 1
        assert results[0].code.value == "7203"
        
        # 英語名で検索
        results = sample_stock_list.search_by_name("Sony")
        assert len(results) == 1
        assert results[0].code.value == "6758"
        
        # 部分一致
        results = sample_stock_list.search_by_name("ホールディングス")
        assert len(results) == 1
        assert results[0].code.value == "3099"
        
        # 該当なし
        results = sample_stock_list.search_by_name("存在しない会社")
        assert len(results) == 0

    def test_mixed_market_stocks(self):
        """複数市場の銘柄を含むリスト"""
        # 各市場の銘柄を作成
        prime_stocks = [StockFactory.build(prime=True) for _ in range(3)]
        standard_stocks = [StockFactory.build(standard=True) for _ in range(2)]
        growth_stocks = [StockFactory.build(growth=True) for _ in range(1)]
        
        stock_list = StockListFactory.build(
            stocks=prime_stocks + standard_stocks + growth_stocks
        )
        
        # 市場別にフィルタリング
        assert len(stock_list.filter_by_market(MarketCode.PRIME)) == 3
        assert len(stock_list.filter_by_market(MarketCode.STANDARD)) == 2
        assert len(stock_list.filter_by_market(MarketCode.GROWTH)) == 1