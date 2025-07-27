from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.stock_use_case import StockUseCase
from app.domain.entities.stock import (
    MarketCode,
    SectorCode17,
    SectorCode33,
    Stock,
    StockCode,
    StockList,
)
from app.domain.exceptions.jquants_exceptions import DataNotFoundError, ValidationError


@pytest.fixture
def mock_stock_repository():
    """モックの銘柄リポジトリ"""
    return MagicMock()


@pytest.fixture
def stock_use_case(mock_stock_repository):
    """テスト用の銘柄ユースケース"""
    return StockUseCase(mock_stock_repository)


@pytest.fixture
def sample_stock():
    """テスト用の銘柄"""
    return Stock(
        code=StockCode("7203"),
        company_name="トヨタ自動車",
        company_name_english="TOYOTA MOTOR CORPORATION",
        sector_17_code=SectorCode17.AUTOMOBILES_TRANSPORTATION,
        sector_17_name="自動車・輸送機",
        sector_33_code=SectorCode33.TRANSPORTATION_EQUIPMENT,
        sector_33_name="輸送用機器",
        scale_category="TOPIX Large70",
        market_code=MarketCode.PRIME,
        market_name="プライム",
    )


@pytest.fixture
def sample_stock_list(sample_stock):
    """テスト用の銘柄リスト"""
    stocks = [
        sample_stock,
        Stock(
            code=StockCode("6758"),
            company_name="ソニーグループ",
            company_name_english="Sony Group Corporation",
            sector_17_code=SectorCode17.ELECTRICAL_PRECISION,
            sector_17_name="電機・精密",
            sector_33_code=SectorCode33.ELECTRIC_APPLIANCES,
            sector_33_name="電気機器",
            scale_category="TOPIX Large70",
            market_code=MarketCode.PRIME,
            market_name="プライム",
        ),
    ]
    return StockList(stocks=stocks, updated_date=date(2024, 1, 1))


class TestStockUseCase:
    """StockUseCase のテスト"""

    @pytest.mark.asyncio
    async def test_get_all_stocks_with_cache(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """キャッシュを使用した全銘柄取得のテスト"""
        # キャッシュが存在する場合
        mock_stock_repository.load_cached_stock_list = AsyncMock(
            return_value=sample_stock_list
        )

        result = await stock_use_case.get_all_stocks(use_cache=True)

        assert result == sample_stock_list
        # API は呼ばれない
        mock_stock_repository.get_listed_stocks.assert_not_called()
        mock_stock_repository.save_stock_list.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_all_stocks_without_cache(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """キャッシュを使用しない全銘柄取得のテスト"""
        mock_stock_repository.get_listed_stocks = AsyncMock(
            return_value=sample_stock_list
        )
        mock_stock_repository.save_stock_list = AsyncMock()

        result = await stock_use_case.get_all_stocks(use_cache=False)

        assert result == sample_stock_list
        mock_stock_repository.get_listed_stocks.assert_called_once()
        mock_stock_repository.save_stock_list.assert_called_once_with(sample_stock_list)

    @pytest.mark.asyncio
    async def test_get_all_stocks_cache_miss(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """キャッシュミス時の全銘柄取得のテスト"""
        # キャッシュが存在しない
        mock_stock_repository.load_cached_stock_list = AsyncMock(return_value=None)
        mock_stock_repository.get_listed_stocks = AsyncMock(
            return_value=sample_stock_list
        )
        mock_stock_repository.save_stock_list = AsyncMock()

        result = await stock_use_case.get_all_stocks(use_cache=True)

        assert result == sample_stock_list
        mock_stock_repository.get_listed_stocks.assert_called_once()
        mock_stock_repository.save_stock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_by_code_success(
        self, stock_use_case, mock_stock_repository, sample_stock
    ):
        """銘柄コードによる取得成功のテスト"""
        mock_stock_repository.get_stock_by_code = AsyncMock(return_value=sample_stock)

        result = await stock_use_case.get_stock_by_code("7203")

        assert result == sample_stock
        mock_stock_repository.get_stock_by_code.assert_called_once_with("7203")

    @pytest.mark.asyncio
    async def test_get_stock_by_code_invalid_code(self, stock_use_case):
        """無効な銘柄コードのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            await stock_use_case.get_stock_by_code("123")
        assert "銘柄コードは 4 桁の数字である必要があります" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_stock_by_code_not_found(
        self, stock_use_case, mock_stock_repository
    ):
        """銘柄が見つからない場合のテスト"""
        mock_stock_repository.get_stock_by_code = AsyncMock(return_value=None)

        with pytest.raises(DataNotFoundError) as exc_info:
            await stock_use_case.get_stock_by_code("9999")
        assert "銘柄コード 9999 の銘柄が見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_stocks_success(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """銘柄検索成功のテスト"""
        mock_stock_repository.search_stocks = AsyncMock(return_value=sample_stock_list)

        result = await stock_use_case.search_stocks(
            keyword="トヨタ",
            market_code="0101",
            sector_17_code="6",
            sector_33_code="3700",
        )

        assert result == sample_stock_list
        mock_stock_repository.search_stocks.assert_called_once_with(
            keyword="トヨタ",
            market_code="0101",
            sector_17_code="6",
            sector_33_code="3700",
        )

    @pytest.mark.asyncio
    async def test_search_stocks_empty_keyword(self, stock_use_case):
        """空の検索キーワードのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            await stock_use_case.search_stocks("")
        assert "検索キーワードは必須です" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_stocks_by_market_success(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """市場区分による銘柄取得成功のテスト"""
        mock_stock_repository.load_cached_stock_list = AsyncMock(
            return_value=sample_stock_list
        )

        result = await stock_use_case.get_stocks_by_market("0101")

        assert len(result.stocks) == 2  # 両方ともプライム市場
        assert result.updated_date == sample_stock_list.updated_date

    @pytest.mark.asyncio
    async def test_get_stocks_by_market_invalid_code(self, stock_use_case):
        """無効な市場区分コードのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            await stock_use_case.get_stocks_by_market("9999")
        assert "無効な市場区分コード: 9999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_stocks_by_market_not_found(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """該当する市場の銘柄が見つからない場合のテスト"""
        mock_stock_repository.load_cached_stock_list = AsyncMock(
            return_value=sample_stock_list
        )

        with pytest.raises(DataNotFoundError) as exc_info:
            await stock_use_case.get_stocks_by_market("0102")  # スタンダード市場
        assert "市場区分 STANDARD の銘柄が見つかりません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_stocks_by_sector_17_success(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """17 業種による銘柄取得成功のテスト"""
        mock_stock_repository.load_cached_stock_list = AsyncMock(
            return_value=sample_stock_list
        )

        result = await stock_use_case.get_stocks_by_sector_17("6")  # 自動車・輸送機

        assert len(result.stocks) == 1
        assert result.stocks[0].company_name == "トヨタ自動車"

    @pytest.mark.asyncio
    async def test_get_stocks_by_sector_17_invalid_code(self, stock_use_case):
        """無効な 17 業種コードのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            await stock_use_case.get_stocks_by_sector_17("99")
        assert "無効な 17 業種コード: 99" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_stocks_by_sector_33_success(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """33 業種による銘柄取得成功のテスト"""
        mock_stock_repository.load_cached_stock_list = AsyncMock(
            return_value=sample_stock_list
        )

        result = await stock_use_case.get_stocks_by_sector_33("3650")  # 電気機器

        assert len(result.stocks) == 1
        assert result.stocks[0].company_name == "ソニーグループ"

    @pytest.mark.asyncio
    async def test_get_stocks_by_sector_33_invalid_code(self, stock_use_case):
        """無効な 33 業種コードのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            await stock_use_case.get_stocks_by_sector_33("9999")
        assert "無効な 33 業種コード: 9999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_stock_cache(
        self, stock_use_case, mock_stock_repository, sample_stock_list
    ):
        """銘柄キャッシュ更新のテスト"""
        mock_stock_repository.get_listed_stocks = AsyncMock(
            return_value=sample_stock_list
        )
        mock_stock_repository.save_stock_list = AsyncMock()

        result = await stock_use_case.refresh_stock_cache()

        assert result == sample_stock_list
        # キャッシュを無視して API から取得
        mock_stock_repository.load_cached_stock_list.assert_not_called()
        mock_stock_repository.get_listed_stocks.assert_called_once()
        mock_stock_repository.save_stock_list.assert_called_once()