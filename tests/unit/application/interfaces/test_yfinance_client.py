"""Unit tests for YFinanceClientInterface."""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from app.application.interfaces.external.yfinance_client import YFinanceClientInterface
from app.domain.entities.stock import Stock, StockCode, MarketCode, SectorCode17, SectorCode33
from app.domain.entities.price import Price
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod
from app.domain.exceptions.jquants_exceptions import NetworkError


class MockYFinanceClient(YFinanceClientInterface):
    """Mock implementation of YFinanceClientInterface for testing."""
    
    def __init__(self):
        super().__init__()
        self._get_stock_info = AsyncMock()
        self._get_stock_prices = AsyncMock()
        self._get_realtime_price = AsyncMock()
        self._get_options_chain = AsyncMock()
        self._get_dividends = AsyncMock()
        self._get_splits = AsyncMock()
        self._get_major_holders = AsyncMock()
        self._get_institutional_holders = AsyncMock()
        self._get_recommendations = AsyncMock()
        self._search_symbols = AsyncMock()
        self._get_market_summary = AsyncMock()
        self._get_trending_tickers = AsyncMock()
    
    async def get_stock_info(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        return await self._get_stock_info(ticker_symbol)
    
    async def get_stock_prices(self, ticker_symbol: TickerSymbol, period: TimePeriod, interval: str = "1d") -> List[Price]:
        return await self._get_stock_prices(ticker_symbol, period, interval)
    
    async def get_realtime_price(self, ticker_symbol: TickerSymbol) -> Optional[Dict[str, float]]:
        return await self._get_realtime_price(ticker_symbol)
    
    async def get_options_chain(self, ticker_symbol: TickerSymbol, expiration_date: Optional[datetime] = None) -> Dict[str, any]:
        return await self._get_options_chain(ticker_symbol, expiration_date)
    
    async def get_dividends(self, ticker_symbol: TickerSymbol, period: TimePeriod) -> List[Dict[str, any]]:
        return await self._get_dividends(ticker_symbol, period)
    
    async def get_splits(self, ticker_symbol: TickerSymbol, period: TimePeriod) -> List[Dict[str, any]]:
        return await self._get_splits(ticker_symbol, period)
    
    async def get_major_holders(self, ticker_symbol: TickerSymbol) -> Dict[str, any]:
        return await self._get_major_holders(ticker_symbol)
    
    async def get_institutional_holders(self, ticker_symbol: TickerSymbol) -> List[Dict[str, any]]:
        return await self._get_institutional_holders(ticker_symbol)
    
    async def get_recommendations(self, ticker_symbol: TickerSymbol) -> List[Dict[str, any]]:
        return await self._get_recommendations(ticker_symbol)
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        return await self._search_symbols(query, limit)
    
    async def get_market_summary(self) -> Dict[str, any]:
        return await self._get_market_summary()
    
    async def get_trending_tickers(self) -> List[str]:
        return await self._get_trending_tickers()


class TestYFinanceClientInterface:
    """Test cases for YFinanceClientInterface."""
    
    @pytest.fixture
    def client(self):
        """Create mock client instance."""
        return MockYFinanceClient()
    
    @pytest.fixture
    def sample_stock(self):
        """Create sample stock entity."""
        return Stock(
            code=StockCode("7974"),  # Nintendo for US listing
            company_name="Apple Inc.",
            company_name_english="Apple Inc.",
            sector_17_code=SectorCode17.ELECTRICAL_PRECISION,
            sector_17_name="Technology",
            sector_33_code=SectorCode33.ELECTRIC_APPLIANCES,
            sector_33_name="Consumer Electronics",
            scale_category="1",
            market_code=MarketCode.OTHERS,
            market_name="NASDAQ"
        )
    
    @pytest.fixture
    def sample_price(self):
        """Create sample price entity."""
        return Price(
            ticker_symbol=TickerSymbol("AAPL"),
            date=date(2023, 1, 4),
            open=125.52,
            high=130.29,
            low=124.17,
            close=129.62,
            volume=89113633,
            adjusted_close=129.62,
            timestamp=datetime(2023, 1, 4, 16, 0, 0)
        )
    
    # Stock info tests
    @pytest.mark.asyncio
    async def test_get_stock_info_found(self, client, sample_stock):
        """Test getting stock info when found."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        client._get_stock_info.return_value = sample_stock
        
        # Act
        result = await client.get_stock_info(ticker)
        
        # Assert
        assert result == sample_stock
        assert result.code.value == "7974"
        assert result.company_name == "Apple Inc."
        client._get_stock_info.assert_called_once_with(ticker)
    
    @pytest.mark.asyncio
    async def test_get_stock_info_not_found(self, client):
        """Test getting stock info when not found."""
        # Arrange
        ticker = TickerSymbol("INVALID")
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
        ticker = TickerSymbol("AAPL")
        client._get_stock_info.side_effect = NetworkError("API request failed")
        
        # Act & Assert
        with pytest.raises(NetworkError, match="API request failed"):
            await client.get_stock_info(ticker)
    
    # Stock prices tests
    @pytest.mark.asyncio
    async def test_get_stock_prices_with_default_interval(self, client):
        """Test getting historical stock prices with default interval."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        period = TimePeriod(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31)
        )
        
        prices = [
            Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 4 + i),
                open=125.0 + i,
                high=130.0 + i,
                low=124.0 + i,
                close=129.0 + i,
                volume=80000000 + i * 1000000
            )
            for i in range(5)
        ]
        
        client._get_stock_prices.return_value = prices
        
        # Act
        result = await client.get_stock_prices(ticker, period)
        
        # Assert
        assert len(result) == 5
        assert all(isinstance(p, Price) for p in result)
        assert result[0].close == 129.0
        assert result[4].close == 133.0
        client._get_stock_prices.assert_called_once_with(ticker, period, "1d")
    
    @pytest.mark.asyncio
    async def test_get_stock_prices_with_custom_interval(self, client):
        """Test getting stock prices with custom interval."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        period = TimePeriod(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 1)
        )
        interval = "1h"
        
        prices = []  # Intraday prices
        client._get_stock_prices.return_value = prices
        
        # Act
        result = await client.get_stock_prices(ticker, period, interval)
        
        # Assert
        assert result == []
        client._get_stock_prices.assert_called_once_with(ticker, period, interval)
    
    # Realtime price tests
    @pytest.mark.asyncio
    async def test_get_realtime_price_success(self, client):
        """Test getting realtime price data."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        realtime_data = {
            "open": 130.48,
            "high": 133.04,
            "low": 129.89,
            "close": 132.25,
            "volume": 112117471,
            "bid": 132.24,
            "ask": 132.26,
            "bid_size": 1200,
            "ask_size": 800
        }
        client._get_realtime_price.return_value = realtime_data
        
        # Act
        result = await client.get_realtime_price(ticker)
        
        # Assert
        assert result == realtime_data
        assert result["close"] == 132.25
        assert "bid" in result
        assert "ask" in result
        client._get_realtime_price.assert_called_once_with(ticker)
    
    @pytest.mark.asyncio
    async def test_get_realtime_price_not_available(self, client):
        """Test getting realtime price when not available."""
        # Arrange
        ticker = TickerSymbol("INVALID")
        client._get_realtime_price.return_value = None
        
        # Act
        result = await client.get_realtime_price(ticker)
        
        # Assert
        assert result is None
        client._get_realtime_price.assert_called_once()
    
    # Options chain tests
    @pytest.mark.asyncio
    async def test_get_options_chain_no_expiration(self, client):
        """Test getting options chain without specific expiration."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        options_data = {
            "expirations": ["2023-01-20", "2023-01-27", "2023-02-03"],
            "calls": [
                {"strike": 130.0, "lastPrice": 3.45, "volume": 1500},
                {"strike": 135.0, "lastPrice": 1.20, "volume": 2000}
            ],
            "puts": [
                {"strike": 125.0, "lastPrice": 1.80, "volume": 1200},
                {"strike": 120.0, "lastPrice": 0.65, "volume": 800}
            ]
        }
        client._get_options_chain.return_value = options_data
        
        # Act
        result = await client.get_options_chain(ticker)
        
        # Assert
        assert "expirations" in result
        assert len(result["calls"]) == 2
        assert len(result["puts"]) == 2
        client._get_options_chain.assert_called_once_with(ticker, None)
    
    @pytest.mark.asyncio
    async def test_get_options_chain_with_expiration(self, client):
        """Test getting options chain for specific expiration."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        expiration = datetime(2023, 1, 20)
        options_data = {
            "calls": [{"strike": 130.0, "lastPrice": 3.45}],
            "puts": [{"strike": 125.0, "lastPrice": 1.80}]
        }
        client._get_options_chain.return_value = options_data
        
        # Act
        result = await client.get_options_chain(ticker, expiration)
        
        # Assert
        assert "calls" in result
        assert "puts" in result
        client._get_options_chain.assert_called_once_with(ticker, expiration)
    
    # Dividends tests
    @pytest.mark.asyncio
    async def test_get_dividends(self, client):
        """Test getting dividend history."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        period = TimePeriod(
            start_date=date(2022, 1, 1),
            end_date=date(2022, 12, 31)
        )
        dividends = [
            {"date": "2022-02-04", "amount": 0.22},
            {"date": "2022-05-06", "amount": 0.23},
            {"date": "2022-08-05", "amount": 0.23},
            {"date": "2022-11-04", "amount": 0.23}
        ]
        client._get_dividends.return_value = dividends
        
        # Act
        result = await client.get_dividends(ticker, period)
        
        # Assert
        assert len(result) == 4
        assert result[0]["amount"] == 0.22
        assert all("date" in d and "amount" in d for d in result)
        client._get_dividends.assert_called_once_with(ticker, period)
    
    # Splits tests
    @pytest.mark.asyncio
    async def test_get_splits(self, client):
        """Test getting stock split history."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        period = TimePeriod(
            start_date=date(2020, 1, 1),
            end_date=date(2022, 12, 31)
        )
        splits = [
            {"date": "2020-08-31", "ratio": "4:1"}
        ]
        client._get_splits.return_value = splits
        
        # Act
        result = await client.get_splits(ticker, period)
        
        # Assert
        assert len(result) == 1
        assert result[0]["ratio"] == "4:1"
        client._get_splits.assert_called_once_with(ticker, period)
    
    # Major holders tests
    @pytest.mark.asyncio
    async def test_get_major_holders(self, client):
        """Test getting major holders information."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        holders_data = {
            "insidersPercentHeld": 0.0007,
            "institutionsPercentHeld": 0.6012,
            "institutionsFloatPercentHeld": 0.6016,
            "institutionsCount": 5570
        }
        client._get_major_holders.return_value = holders_data
        
        # Act
        result = await client.get_major_holders(ticker)
        
        # Assert
        assert result["institutionsPercentHeld"] == 0.6012
        assert result["institutionsCount"] == 5570
        client._get_major_holders.assert_called_once_with(ticker)
    
    # Institutional holders tests
    @pytest.mark.asyncio
    async def test_get_institutional_holders(self, client):
        """Test getting institutional holders list."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        holders = [
            {
                "holder": "Vanguard Group Inc",
                "shares": 1272378901,
                "value": 165223548130,
                "percentHeld": 0.0801
            },
            {
                "holder": "Blackrock Inc.",
                "shares": 1020245185,
                "value": 132509194005,
                "percentHeld": 0.0643
            }
        ]
        client._get_institutional_holders.return_value = holders
        
        # Act
        result = await client.get_institutional_holders(ticker)
        
        # Assert
        assert len(result) == 2
        assert result[0]["holder"] == "Vanguard Group Inc"
        assert result[1]["percentHeld"] == 0.0643
        client._get_institutional_holders.assert_called_once_with(ticker)
    
    # Recommendations tests
    @pytest.mark.asyncio
    async def test_get_recommendations(self, client):
        """Test getting analyst recommendations."""
        # Arrange
        ticker = TickerSymbol("AAPL")
        recommendations = [
            {
                "firm": "Morgan Stanley",
                "toGrade": "Overweight",
                "fromGrade": "Equal-Weight",
                "action": "up",
                "date": "2023-01-15"
            },
            {
                "firm": "JP Morgan",
                "toGrade": "Overweight",
                "fromGrade": "Overweight",
                "action": "reit",
                "date": "2023-01-10"
            }
        ]
        client._get_recommendations.return_value = recommendations
        
        # Act
        result = await client.get_recommendations(ticker)
        
        # Assert
        assert len(result) == 2
        assert result[0]["firm"] == "Morgan Stanley"
        assert result[0]["action"] == "up"
        client._get_recommendations.assert_called_once_with(ticker)
    
    # Symbol search tests
    @pytest.mark.asyncio
    async def test_search_symbols_default_limit(self, client):
        """Test searching symbols with default limit."""
        # Arrange
        query = "Apple"
        search_results = [
            {"symbol": "AAPL", "name": "Apple Inc.", "type": "EQUITY"},
            {"symbol": "APLE", "name": "Apple Hospitality REIT", "type": "EQUITY"}
        ]
        client._search_symbols.return_value = search_results
        
        # Act
        result = await client.search_symbols(query)
        
        # Assert
        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"
        assert result[1]["name"] == "Apple Hospitality REIT"
        client._search_symbols.assert_called_once_with(query, 10)
    
    @pytest.mark.asyncio
    async def test_search_symbols_custom_limit(self, client):
        """Test searching symbols with custom limit."""
        # Arrange
        query = "Tech"
        limit = 5
        search_results = [
            {"symbol": "TECH", "name": "Bio-Techne Corp", "type": "EQUITY"}
        ]
        client._search_symbols.return_value = search_results
        
        # Act
        result = await client.search_symbols(query, limit)
        
        # Assert
        assert len(result) == 1
        client._search_symbols.assert_called_once_with(query, limit)
    
    # Market summary tests
    @pytest.mark.asyncio
    async def test_get_market_summary(self, client):
        """Test getting market summary."""
        # Arrange
        market_data = {
            "marketState": "REGULAR",
            "indices": {
                "^DJI": {"price": 33269.77, "change": 112.64, "changePercent": 0.34},
                "^IXIC": {"price": 10458.76, "change": -66.05, "changePercent": -0.63},
                "^GSPC": {"price": 3808.10, "change": -2.99, "changePercent": -0.08}
            },
            "currencies": {
                "EURUSD=X": {"price": 1.0732, "change": 0.0025},
                "JPY=X": {"price": 131.82, "change": -0.45}
            }
        }
        client._get_market_summary.return_value = market_data
        
        # Act
        result = await client.get_market_summary()
        
        # Assert
        assert result["marketState"] == "REGULAR"
        assert "^DJI" in result["indices"]
        assert result["indices"]["^DJI"]["changePercent"] == 0.34
        assert "currencies" in result
        client._get_market_summary.assert_called_once()
    
    # Trending tickers tests
    @pytest.mark.asyncio
    async def test_get_trending_tickers(self, client):
        """Test getting trending tickers."""
        # Arrange
        trending = ["TSLA", "AAPL", "AMZN", "NVDA", "META"]
        client._get_trending_tickers.return_value = trending
        
        # Act
        result = await client.get_trending_tickers()
        
        # Assert
        assert len(result) == 5
        assert "TSLA" in result
        assert "AAPL" in result
        assert all(isinstance(ticker, str) for ticker in result)
        client._get_trending_tickers.assert_called_once()
    
    # Error handling tests
    @pytest.mark.asyncio
    async def test_api_error_propagation(self, client):
        """Test that API errors are properly propagated."""
        # Arrange
        error_message = "Connection timeout"
        client._get_market_summary.side_effect = NetworkError(error_message)
        
        # Act & Assert
        with pytest.raises(NetworkError, match=error_message):
            await client.get_market_summary()
    
    # Interface compliance test
    def test_interface_implementation(self):
        """Test that MockYFinanceClient implements all interface methods."""
        # Arrange
        interface_methods = [
            'get_stock_info',
            'get_stock_prices',
            'get_realtime_price',
            'get_options_chain',
            'get_dividends',
            'get_splits',
            'get_major_holders',
            'get_institutional_holders',
            'get_recommendations',
            'search_symbols',
            'get_market_summary',
            'get_trending_tickers'
        ]
        
        client = MockYFinanceClient()
        
        # Assert
        for method_name in interface_methods:
            assert hasattr(client, method_name), f"Missing method: {method_name}"
            method = getattr(client, method_name)
            assert callable(method), f"Method {method_name} is not callable"
            # Check that the private mock also exists
            private_attr = f"_{method_name}"
            assert hasattr(client, private_attr), f"Missing private mock: {private_attr}"
            assert isinstance(getattr(client, private_attr), AsyncMock), f"{private_attr} is not an AsyncMock"