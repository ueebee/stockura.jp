"""Unit tests for JQuantsClientInterface."""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date, datetime
from typing import Dict, List, Optional

from app.application.interfaces.external.jquants_client import JQuantsClientInterface
from app.domain.entities.stock import Stock, StockCode, MarketCode, SectorCode17, SectorCode33
from app.domain.entities.price import Price
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod
from app.domain.exceptions.jquants_exceptions import NetworkError


class MockJQuantsClient(JQuantsClientInterface):
    """Mock implementation of JQuantsClientInterface for testing."""
    
    def __init__(self):
        super().__init__()
        self._authenticate = AsyncMock()
        self._get_stock_info = AsyncMock()
        self._get_stock_prices = AsyncMock()
        self._get_daily_quotes = AsyncMock()
        self._get_listed_stocks = AsyncMock()
        self._get_financial_data = AsyncMock()
        self._get_market_indices = AsyncMock()
        self._get_trading_calendar = AsyncMock()
        self._is_trading_day = AsyncMock()
        self._get_sectors = AsyncMock()
    
    async def authenticate(self) -> str:
        return await self._authenticate()
    
    async def get_stock_info(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        return await self._get_stock_info(ticker_symbol)
    
    async def get_stock_prices(self, ticker_symbol: TickerSymbol, period: TimePeriod) -> List[Price]:
        return await self._get_stock_prices(ticker_symbol, period)
    
    async def get_daily_quotes(self, ticker_symbol: TickerSymbol, target_date: date) -> Optional[Price]:
        return await self._get_daily_quotes(ticker_symbol, target_date)
    
    async def get_listed_stocks(self, market: Optional[str] = None) -> List[Dict[str, str]]:
        return await self._get_listed_stocks(market=market)
    
    async def get_financial_data(self, ticker_symbol: TickerSymbol, fiscal_year: Optional[int] = None) -> Dict[str, any]:
        return await self._get_financial_data(ticker_symbol, fiscal_year=fiscal_year)
    
    async def get_market_indices(self) -> Dict[str, float]:
        return await self._get_market_indices()
    
    async def get_trading_calendar(self, year: int, month: Optional[int] = None) -> List[date]:
        return await self._get_trading_calendar(year, month=month)
    
    async def is_trading_day(self, target_date: date) -> bool:
        return await self._is_trading_day(target_date)
    
    async def get_sectors(self) -> List[str]:
        return await self._get_sectors()


class TestJQuantsClientInterface:
    """Test cases for JQuantsClientInterface."""
    
    @pytest.fixture
    def client(self):
        """Create mock client instance."""
        return MockJQuantsClient()
    
    @pytest.fixture
    def sample_stock(self):
        """Create sample stock entity."""
        return Stock(
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english="Toyota Motor Corporation",
            sector_17_code=SectorCode17.AUTOMOBILES_TRANSPORTATION,
            sector_17_name="自動車・輸送機",
            sector_33_code=SectorCode33.TRANSPORTATION_EQUIPMENT,
            sector_33_name="輸送用機器",
            scale_category="1",
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
    
    @pytest.fixture
    def sample_price(self):
        """Create sample price entity."""
        return Price(
            ticker_symbol=TickerSymbol("7203"),
            date=date(2023, 1, 4),
            open=1800.0,
            high=1850.0,
            low=1790.0,
            close=1835.0,
            volume=15000000,
            adjusted_close=1835.0,
            timestamp=datetime(2023, 1, 4, 15, 0, 0)
        )
    
    # Authentication tests
    @pytest.mark.asyncio
    async def test_authenticate_success(self, client):
        """Test successful authentication."""
        # Arrange
        expected_token = "test_access_token_123"
        client._authenticate.return_value = expected_token
        
        # Act
        token = await client.authenticate()
        
        # Assert
        assert token == expected_token
        client._authenticate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, client):
        """Test authentication failure."""
        # Arrange
        client._authenticate.side_effect = NetworkError("Authentication failed")
        
        # Act & Assert
        with pytest.raises(NetworkError, match="Authentication failed"):
            await client.authenticate()
    
    # Stock info tests
    @pytest.mark.asyncio
    async def test_get_stock_info_found(self, client, sample_stock):
        """Test getting stock info when found."""
        # Arrange
        ticker = TickerSymbol("7203")
        client._get_stock_info.return_value = sample_stock
        
        # Act
        result = await client.get_stock_info(ticker)
        
        # Assert
        assert result == sample_stock
        assert result.code.value == "7203"
        assert result.company_name == "トヨタ自動車"
        client._get_stock_info.assert_called_once_with(ticker)
    
    @pytest.mark.asyncio
    async def test_get_stock_info_not_found(self, client):
        """Test getting stock info when not found."""
        # Arrange
        ticker = TickerSymbol("9999")
        client._get_stock_info.return_value = None
        
        # Act
        result = await client.get_stock_info(ticker)
        
        # Assert
        assert result is None
        client._get_stock_info.assert_called_once_with(ticker)
    
    @pytest.mark.asyncio
    async def test_get_stock_info_error(self, client):
        """Test getting stock info with API error."""
        # Arrange
        ticker = TickerSymbol("7203")
        client._get_stock_info.side_effect = NetworkError("API request failed")
        
        # Act & Assert
        with pytest.raises(NetworkError, match="API request failed"):
            await client.get_stock_info(ticker)
    
    # Stock prices tests
    @pytest.mark.asyncio
    async def test_get_stock_prices_success(self, client):
        """Test getting historical stock prices."""
        # Arrange
        ticker = TickerSymbol("7203")
        period = TimePeriod(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31)
        )
        
        prices = [
            Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 4 + i),
                open=1800.0 + i * 10,
                high=1850.0 + i * 10,
                low=1790.0 + i * 10,
                close=1835.0 + i * 10,
                volume=15000000 + i * 100000
            )
            for i in range(5)
        ]
        
        client._get_stock_prices.return_value = prices
        
        # Act
        result = await client.get_stock_prices(ticker, period)
        
        # Assert
        assert len(result) == 5
        assert all(isinstance(p, Price) for p in result)
        assert result[0].close == 1835.0
        assert result[4].close == 1875.0
        client._get_stock_prices.assert_called_once_with(ticker, period)
    
    @pytest.mark.asyncio
    async def test_get_stock_prices_empty(self, client):
        """Test getting stock prices with no data."""
        # Arrange
        ticker = TickerSymbol("7203")
        period = TimePeriod(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 7)  # Weekend period
        )
        client._get_stock_prices.return_value = []
        
        # Act
        result = await client.get_stock_prices(ticker, period)
        
        # Assert
        assert result == []
        client._get_stock_prices.assert_called_once()
    
    # Daily quotes tests
    @pytest.mark.asyncio
    async def test_get_daily_quotes_found(self, client, sample_price):
        """Test getting daily quote when found."""
        # Arrange
        ticker = TickerSymbol("7203")
        target_date = date(2023, 1, 4)
        client._get_daily_quotes.return_value = sample_price
        
        # Act
        result = await client.get_daily_quotes(ticker, target_date)
        
        # Assert
        assert result == sample_price
        assert result.date == target_date
        client._get_daily_quotes.assert_called_once_with(ticker, target_date)
    
    @pytest.mark.asyncio
    async def test_get_daily_quotes_not_found(self, client):
        """Test getting daily quote for non-trading day."""
        # Arrange
        ticker = TickerSymbol("7203")
        target_date = date(2023, 1, 1)  # New Year's Day
        client._get_daily_quotes.return_value = None
        
        # Act
        result = await client.get_daily_quotes(ticker, target_date)
        
        # Assert
        assert result is None
        client._get_daily_quotes.assert_called_once()
    
    # Listed stocks tests
    @pytest.mark.asyncio
    async def test_get_listed_stocks_all(self, client):
        """Test getting all listed stocks."""
        # Arrange
        stocks_data = [
            {"code": "7203", "name": "トヨタ自動車", "market": "東証プライム"},
            {"code": "6758", "name": "ソニーグループ", "market": "東証プライム"},
            {"code": "9984", "name": "ソフトバンクグループ", "market": "東証プライム"}
        ]
        client._get_listed_stocks.return_value = stocks_data
        
        # Act
        result = await client.get_listed_stocks()
        
        # Assert
        assert len(result) == 3
        assert result[0]["code"] == "7203"
        client._get_listed_stocks.assert_called_once_with(market=None)
    
    @pytest.mark.asyncio
    async def test_get_listed_stocks_by_market(self, client):
        """Test getting listed stocks filtered by market."""
        # Arrange
        stocks_data = [
            {"code": "4755", "name": "楽天グループ", "market": "東証プライム"},
            {"code": "3938", "name": "LINE", "market": "東証プライム"}
        ]
        client._get_listed_stocks.return_value = stocks_data
        
        # Act
        result = await client.get_listed_stocks(market="TSE")
        
        # Assert
        assert len(result) == 2
        client._get_listed_stocks.assert_called_once_with(market="TSE")
    
    # Financial data tests
    @pytest.mark.asyncio
    async def test_get_financial_data_current_year(self, client):
        """Test getting financial data for current year."""
        # Arrange
        ticker = TickerSymbol("7203")
        financial_data = {
            "revenue": 31379507000000,
            "operating_income": 2995695000000,
            "net_income": 2850110000000,
            "total_assets": 67688771000000,
            "shareholders_equity": 26245959000000
        }
        client._get_financial_data.return_value = financial_data
        
        # Act
        result = await client.get_financial_data(ticker)
        
        # Assert
        assert result["revenue"] == 31379507000000
        assert "operating_income" in result
        client._get_financial_data.assert_called_once_with(ticker, fiscal_year=None)
    
    @pytest.mark.asyncio
    async def test_get_financial_data_specific_year(self, client):
        """Test getting financial data for specific year."""
        # Arrange
        ticker = TickerSymbol("7203")
        fiscal_year = 2022
        financial_data = {
            "revenue": 29929980000000,
            "operating_income": 2197748000000
        }
        client._get_financial_data.return_value = financial_data
        
        # Act
        result = await client.get_financial_data(ticker, fiscal_year)
        
        # Assert
        assert result["revenue"] == 29929980000000
        client._get_financial_data.assert_called_once_with(ticker, fiscal_year=2022)
    
    # Market indices tests
    @pytest.mark.asyncio
    async def test_get_market_indices(self, client):
        """Test getting market indices."""
        # Arrange
        indices = {
            "TOPIX": 1989.43,
            "Nikkei 225": 28041.48,
            "TOPIX Small": 2973.42,
            "JASDAQ": 165.89
        }
        client._get_market_indices.return_value = indices
        
        # Act
        result = await client.get_market_indices()
        
        # Assert
        assert result["TOPIX"] == 1989.43
        assert result["Nikkei 225"] == 28041.48
        assert len(result) == 4
        client._get_market_indices.assert_called_once()
    
    # Trading calendar tests
    @pytest.mark.asyncio
    async def test_get_trading_calendar_full_year(self, client):
        """Test getting trading calendar for full year."""
        # Arrange
        year = 2023
        trading_days = [
            date(2023, 1, 4),
            date(2023, 1, 5),
            date(2023, 1, 6),
            # ... more trading days
        ]
        client._get_trading_calendar.return_value = trading_days
        
        # Act
        result = await client.get_trading_calendar(year)
        
        # Assert
        assert len(result) >= 3
        assert all(isinstance(d, date) for d in result)
        client._get_trading_calendar.assert_called_once_with(year, month=None)
    
    @pytest.mark.asyncio
    async def test_get_trading_calendar_specific_month(self, client):
        """Test getting trading calendar for specific month."""
        # Arrange
        year = 2023
        month = 1
        trading_days = [
            date(2023, 1, 4),
            date(2023, 1, 5),
            date(2023, 1, 6),
            date(2023, 1, 10),
            date(2023, 1, 11),
        ]
        client._get_trading_calendar.return_value = trading_days
        
        # Act
        result = await client.get_trading_calendar(year, month)
        
        # Assert
        assert len(result) == 5
        assert all(d.month == 1 for d in result)
        client._get_trading_calendar.assert_called_once_with(year, month=1)
    
    # Trading day check tests
    @pytest.mark.asyncio
    async def test_is_trading_day_true(self, client):
        """Test checking if date is trading day."""
        # Arrange
        test_date = date(2023, 1, 4)  # Wednesday
        client._is_trading_day.return_value = True
        
        # Act
        result = await client.is_trading_day(test_date)
        
        # Assert
        assert result is True
        client._is_trading_day.assert_called_once_with(test_date)
    
    @pytest.mark.asyncio
    async def test_is_trading_day_false(self, client):
        """Test checking if date is not trading day."""
        # Arrange
        test_date = date(2023, 1, 1)  # New Year's Day
        client._is_trading_day.return_value = False
        
        # Act
        result = await client.is_trading_day(test_date)
        
        # Assert
        assert result is False
        client._is_trading_day.assert_called_once_with(test_date)
    
    # Sectors tests
    @pytest.mark.asyncio
    async def test_get_sectors(self, client):
        """Test getting list of sectors."""
        # Arrange
        sectors = [
            "情報・通信",
            "電気機器",
            "輸送用機器",
            "銀行業",
            "医薬品",
            "小売業"
        ]
        client._get_sectors.return_value = sectors
        
        # Act
        result = await client.get_sectors()
        
        # Assert
        assert len(result) == 6
        assert "情報・通信" in result
        assert all(isinstance(s, str) for s in result)
        client._get_sectors.assert_called_once()
    
    # Error handling tests
    @pytest.mark.asyncio
    async def test_api_error_propagation(self, client):
        """Test that API errors are properly propagated."""
        # Arrange
        error_message = "Rate limit exceeded"
        client._get_sectors.side_effect = NetworkError(error_message)
        
        # Act & Assert
        with pytest.raises(NetworkError, match=error_message):
            await client.get_sectors()
    
    # Interface compliance test
    def test_interface_implementation(self):
        """Test that MockJQuantsClient implements all interface methods."""
        # Arrange
        interface_methods = [
            'authenticate',
            'get_stock_info',
            'get_stock_prices',
            'get_daily_quotes',
            'get_listed_stocks',
            'get_financial_data',
            'get_market_indices',
            'get_trading_calendar',
            'is_trading_day',
            'get_sectors'
        ]
        
        client = MockJQuantsClient()
        
        # Assert
        for method_name in interface_methods:
            assert hasattr(client, method_name), f"Missing method: {method_name}"
            method = getattr(client, method_name)
            assert callable(method), f"Method {method_name} is not callable"
            # Check that the private mock also exists
            private_attr = f"_{method_name}"
            assert hasattr(client, private_attr), f"Missing private mock: {private_attr}"
            assert isinstance(getattr(client, private_attr), AsyncMock), f"{private_attr} is not an AsyncMock"