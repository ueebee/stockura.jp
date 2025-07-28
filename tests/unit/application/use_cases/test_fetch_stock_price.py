"""Unit tests for FetchStockPriceUseCase."""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date, datetime
from decimal import Decimal

from app.application.use_cases.fetch_stock_price import FetchStockPriceUseCase
from app.domain.entities.stock import Stock, StockCode, MarketCode, SectorCode17, SectorCode33
from app.domain.entities.price import Price
from app.domain.exceptions.stock_exceptions import StockNotFoundError
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod
from tests.mocks.jquants_mock import MockJQuantsClient, MockYFinanceClient


class TestFetchStockPriceUseCase:
    """Test cases for FetchStockPriceUseCase."""
    
    @pytest.fixture
    def mock_stock_repository(self):
        """Create mock stock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def sample_stock(self):
        """Create sample stock."""
        return Stock(
            code=StockCode("1234"),
            company_name="Test Company",
            company_name_english="Test Company Ltd.",
            sector_17_code=SectorCode17.FOODS,
            sector_17_name="食品",
            sector_33_code=SectorCode33.FISHERY_AGRICULTURE_FORESTRY,
            sector_33_name="水産・農林業",
            scale_category="1",
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
    
    @pytest.fixture
    def sample_price(self):
        """Create sample price."""
        return Price(
            ticker_symbol=TickerSymbol("1234"),
            date=date(2024, 1, 1),
            open=1000.0,
            high=1050.0,
            low=980.0,
            close=1020.0,
            volume=1000000
        )
    
    @pytest.fixture
    def mock_jquants_client(self):
        """Create mock JQuants client."""
        mock = AsyncMock()
        mock.get_daily_quotes = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_yfinance_client(self):
        """Create mock YFinance client."""
        mock = AsyncMock()
        mock.get_realtime_price = AsyncMock()
        mock.get_stock_prices = AsyncMock()
        return mock
    
    @pytest.fixture
    def use_case(self, mock_stock_repository, mock_jquants_client, mock_yfinance_client):
        """Create use case instance."""
        return FetchStockPriceUseCase(
            stock_repository=mock_stock_repository,
            jquants_client=mock_jquants_client,
            yfinance_client=mock_yfinance_client
        )
    
    # 正常系テストケース
    @pytest.mark.asyncio
    async def test_fetch_latest_price(self, use_case, mock_stock_repository, sample_stock, sample_price, mock_jquants_client):
        """Test fetching latest price."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        
        # Create price with daily_change attributes
        price_with_change = sample_price
        price_with_change.daily_change = Decimal("20.0")
        price_with_change.daily_change_percent = Decimal("2.0")
        mock_jquants_client.get_daily_quotes.return_value = price_with_change
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.stock.company_name == "Test Company"
        assert result.current_price is not None
        assert result.price_change == 20.0
        assert result.price_change_percent == 2.0
        assert result.volume_average == 1000000.0
    
    @pytest.mark.asyncio
    async def test_fetch_price_for_specific_date(self, use_case, mock_stock_repository, sample_stock, sample_price, mock_jquants_client):
        """Test fetching price for specific date."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        specific_date = date(2024, 1, 15)
        mock_jquants_client.get_daily_quotes.return_value = sample_price
        
        # Act
        result = await use_case.execute("1234", target_date=specific_date)
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is not None
        mock_jquants_client.get_daily_quotes.assert_called_once_with(
            TickerSymbol("1234"), specific_date
        )
    
    @pytest.mark.asyncio
    async def test_fetch_price_with_cache_hit(self, use_case, mock_stock_repository, sample_stock, sample_price, mock_jquants_client):
        """Test fetching price when stock exists in repository."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        mock_jquants_client.get_daily_quotes.return_value = sample_price
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        # Should not try to fetch stock info from external APIs
        mock_jquants_client.get_stock_info.assert_not_called()
        # Should not save to repository
        mock_stock_repository.save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetch_price_with_cache_miss(self, use_case, mock_stock_repository, sample_stock, sample_price, mock_jquants_client):
        """Test fetching price when stock not in repository."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = None
        mock_jquants_client.get_stock_info.return_value = sample_stock
        mock_stock_repository.save.return_value = sample_stock
        mock_jquants_client.get_daily_quotes.return_value = sample_price
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        # Should fetch stock info from external API
        mock_jquants_client.get_stock_info.assert_called_once()
        # Should save to repository
        mock_stock_repository.save.assert_called_once()
    
    # 異常系テストケース
    @pytest.mark.asyncio
    async def test_fetch_price_invalid_stock_code(self, use_case, mock_stock_repository, mock_jquants_client):
        """Test fetching price with invalid stock code."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = None
        mock_jquants_client.get_stock_info.return_value = None
        
        # Act & Assert
        with pytest.raises(StockNotFoundError) as exc_info:
            await use_case.execute("9999")
        
        assert "9999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_price_future_date(self, use_case, mock_stock_repository, sample_stock, mock_jquants_client):
        """Test fetching price for future date returns None."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        future_date = date(2025, 12, 31)
        mock_jquants_client.get_daily_quotes.return_value = None
        
        # Act
        result = await use_case.execute("1234", target_date=future_date)
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is None
        assert result.price_change is None
        assert result.price_change_percent is None
    
    @pytest.mark.asyncio
    async def test_fetch_price_weekend_date(self, use_case, mock_stock_repository, sample_stock, mock_jquants_client):
        """Test fetching price for weekend date."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        weekend_date = date(2024, 1, 6)  # Saturday
        mock_jquants_client.get_daily_quotes.return_value = None
        
        # Act
        result = await use_case.execute("1234", target_date=weekend_date)
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is None
    
    @pytest.mark.asyncio
    async def test_fetch_price_api_error(self, use_case, mock_stock_repository, sample_stock, mock_jquants_client):
        """Test handling API errors."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        mock_jquants_client.get_daily_quotes.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute("1234")
        
        assert "API Error" in str(exc_info.value)
    
    # データソース切り替えテスト
    @pytest.mark.asyncio
    async def test_fetch_from_jquants(self, use_case, mock_stock_repository, sample_stock, sample_price, mock_jquants_client):
        """Test fetching from JQuants source."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        mock_jquants_client.get_daily_quotes.return_value = sample_price
        
        # Act
        result = await use_case.execute("1234", source="jquants")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        mock_jquants_client.get_daily_quotes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_from_yfinance_fallback(self, use_case, mock_stock_repository, sample_stock, mock_yfinance_client):
        """Test fetching from YFinance source."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        realtime_data = {
            "open": 1000.0,
            "high": 1050.0,
            "low": 980.0,
            "close": 1020.0,
            "volume": 1000000
        }
        mock_yfinance_client.get_realtime_price.return_value = realtime_data
        
        # Act
        result = await use_case.execute("1234", source="yfinance")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is not None
        mock_yfinance_client.get_realtime_price.assert_called_once()
    
    # 追加テスト: YFinance で特定日付の価格取得
    @pytest.mark.asyncio
    async def test_fetch_yfinance_specific_date(self, use_case, mock_stock_repository, sample_stock, sample_price, mock_yfinance_client):
        """Test fetching specific date price from YFinance."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        specific_date = date(2024, 1, 15)
        mock_yfinance_client.get_stock_prices.return_value = [sample_price]
        
        # Act
        result = await use_case.execute("1234", target_date=specific_date, source="yfinance")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is not None
        # Check that TimePeriod was created correctly
        call_args = mock_yfinance_client.get_stock_prices.call_args
        assert call_args[0][0] == TickerSymbol("1234")
        assert call_args[0][1].start_date == specific_date
        assert call_args[0][1].end_date == specific_date
    
    @pytest.mark.asyncio
    async def test_fetch_yfinance_no_realtime_data(self, use_case, mock_stock_repository, sample_stock, mock_yfinance_client):
        """Test handling when YFinance returns no realtime data."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        mock_yfinance_client.get_realtime_price.return_value = None
        
        # Act
        result = await use_case.execute("1234", source="yfinance")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is None
        assert result.price_change is None
        assert result.volume_average is None