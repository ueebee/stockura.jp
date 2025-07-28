"""Unit tests for PriceCalculator domain service."""
import pytest
from decimal import Decimal
from datetime import date, datetime
from typing import List

from app.domain.services.price_calculator import PriceCalculator
from app.domain.entities.price import Price
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.exceptions.stock_exceptions import InsufficientDataError


class TestPriceCalculator:
    """Test cases for PriceCalculator domain service."""
    
    @pytest.fixture
    def sample_prices(self) -> List[Price]:
        """Create sample price data for testing."""
        ticker = TickerSymbol("7203")
        prices = []
        
        # Create 30 days of price data
        for i in range(30):
            prices.append(Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1 + i),
                open=100.0 + i * 0.5,
                high=102.0 + i * 0.5,
                low=99.0 + i * 0.5,
                close=101.0 + i * 0.5,
                volume=1000000 + i * 10000,
                adjusted_close=101.0 + i * 0.5,
                timestamp=datetime(2023, 1, 1 + i, 15, 0, 0)
            ))
        
        return prices
    
    @pytest.fixture
    def volatile_prices(self) -> List[Price]:
        """Create volatile price data for testing."""
        ticker = TickerSymbol("7203")
        prices = []
        
        # Create volatile price movements
        price_values = [100, 105, 98, 110, 95, 108, 92, 106, 102, 99]
        
        for i, close_price in enumerate(price_values):
            prices.append(Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1 + i),
                open=close_price - 1,
                high=close_price + 2,
                low=close_price - 2,
                close=float(close_price),
                volume=1000000,
                adjusted_close=float(close_price)
            ))
        
        return prices
    
    # SMA tests
    def test_calculate_sma_valid(self, sample_prices):
        """Test SMA calculation with valid data."""
        # Calculate 10-day SMA
        sma = PriceCalculator.calculate_sma(sample_prices, 10)
        
        # Last 10 prices: 101 + 19.5 to 101 + 29*0.5
        # = 120.5 to 115.5, average = (120.5 + 121 + ... + 115.5) / 10
        expected = sum(101.0 + i * 0.5 for i in range(20, 30)) / 10
        
        assert isinstance(sma, (Decimal, float))
        assert float(sma) == pytest.approx(expected, rel=0.01)
    
    def test_calculate_sma_minimum_period(self, sample_prices):
        """Test SMA with minimum period."""
        sma = PriceCalculator.calculate_sma(sample_prices[:1], 1)
        assert float(sma) == 101.0
    
    def test_calculate_sma_insufficient_data(self, sample_prices):
        """Test SMA with insufficient data."""
        with pytest.raises(InsufficientDataError) as exc_info:
            PriceCalculator.calculate_sma(sample_prices[:5], 10)
        
        assert exc_info.value.required == 10
        assert exc_info.value.available == 5
        assert "SMA calculation" in str(exc_info.value)
    
    def test_calculate_sma_all_data(self, sample_prices):
        """Test SMA using all available data."""
        sma = PriceCalculator.calculate_sma(sample_prices, 30)
        expected = sum(101.0 + i * 0.5 for i in range(30)) / 30
        assert float(sma) == pytest.approx(expected, rel=0.01)
    
    # EMA tests
    def test_calculate_ema_valid(self, sample_prices):
        """Test EMA calculation with valid data."""
        ema = PriceCalculator.calculate_ema(sample_prices, 10)
        
        # EMA should be a valid decimal
        assert isinstance(ema, (Decimal, float))
        # EMA should be within reasonable range of prices
        assert 100 < float(ema) < 130
    
    def test_calculate_ema_convergence(self, volatile_prices):
        """Test that EMA converges differently than SMA."""
        # Use volatile prices to ensure EMA differs from SMA
        prices = volatile_prices * 3  # Ensure enough data
        sma = PriceCalculator.calculate_sma(prices, 10)
        ema = PriceCalculator.calculate_ema(prices, 10)
        
        # EMA should differ from SMA with volatile data
        assert abs(float(ema) - float(sma)) > 0.01
    
    def test_calculate_ema_insufficient_data(self, sample_prices):
        """Test EMA with insufficient data."""
        with pytest.raises(InsufficientDataError) as exc_info:
            PriceCalculator.calculate_ema(sample_prices[:5], 10)
        
        assert exc_info.value.required == 10
        assert exc_info.value.available == 5
        assert "EMA calculation" in str(exc_info.value)
    
    # RSI tests
    def test_calculate_rsi_valid(self, volatile_prices):
        """Test RSI calculation with valid data."""
        # Need at least 15 prices for default 14-period RSI
        prices = volatile_prices * 2  # Duplicate to have enough data
        rsi = PriceCalculator.calculate_rsi(prices, 14)
        
        # RSI should be between 0 and 100
        assert 0 <= float(rsi) <= 100
    
    def test_calculate_rsi_overbought(self, sample_prices):
        """Test RSI with consistently rising prices (overbought)."""
        # Prices consistently rising should give high RSI
        rsi = PriceCalculator.calculate_rsi(sample_prices, 14)
        
        # With consistently rising prices, RSI should be high
        assert float(rsi) > 70
    
    def test_calculate_rsi_oversold(self):
        """Test RSI with consistently falling prices (oversold)."""
        ticker = TickerSymbol("7203")
        prices = []
        
        # Create falling prices
        for i in range(20):
            prices.append(Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1 + i),
                open=100.0 - i * 0.5,
                high=101.0 - i * 0.5,
                low=99.0 - i * 0.5,
                close=100.0 - i * 0.5,
                volume=1000000
            ))
        
        rsi = PriceCalculator.calculate_rsi(prices, 14)
        
        # With consistently falling prices, RSI should be low
        assert float(rsi) < 30
    
    def test_calculate_rsi_no_losses(self):
        """Test RSI when there are no losses (edge case)."""
        ticker = TickerSymbol("7203")
        prices = []
        
        # Create only rising prices
        for i in range(20):
            prices.append(Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1 + i),
                open=100.0 + i,
                high=102.0 + i,
                low=99.0 + i,
                close=101.0 + i,
                volume=1000000
            ))
        
        rsi = PriceCalculator.calculate_rsi(prices, 14)
        
        # With no losses, RSI should be 100
        assert float(rsi) == 100
    
    def test_calculate_rsi_insufficient_data(self, sample_prices):
        """Test RSI with insufficient data."""
        with pytest.raises(InsufficientDataError) as exc_info:
            PriceCalculator.calculate_rsi(sample_prices[:10], 14)
        
        assert exc_info.value.required == 15
        assert exc_info.value.available == 10
        assert "RSI calculation" in str(exc_info.value)
    
    def test_calculate_rsi_custom_period(self, sample_prices):
        """Test RSI with custom period."""
        rsi = PriceCalculator.calculate_rsi(sample_prices, 7)
        assert 0 <= float(rsi) <= 100
    
    # Volatility tests
    def test_calculate_volatility_valid(self, volatile_prices):
        """Test volatility calculation with valid data."""
        volatility = PriceCalculator.calculate_volatility(volatile_prices * 3, 20)
        
        # Volatility should be positive
        assert float(volatility) > 0
    
    def test_calculate_volatility_stable_prices(self):
        """Test volatility with stable prices."""
        ticker = TickerSymbol("7203")
        prices = []
        
        # Create stable prices
        for i in range(20):
            prices.append(Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1 + i),
                open=100.0,
                high=100.5,
                low=99.5,
                close=100.0,
                volume=1000000
            ))
        
        volatility = PriceCalculator.calculate_volatility(prices, 20)
        
        # With stable prices, volatility should be near 0
        assert float(volatility) < 0.01
    
    def test_calculate_volatility_insufficient_data(self, sample_prices):
        """Test volatility with insufficient data."""
        with pytest.raises(InsufficientDataError) as exc_info:
            PriceCalculator.calculate_volatility(sample_prices[:10], 20)
        
        assert exc_info.value.required == 20
        assert exc_info.value.available == 10
        assert "volatility calculation" in str(exc_info.value)
    
    def test_calculate_volatility_single_price(self):
        """Test volatility edge case with single price."""
        ticker = TickerSymbol("7203")
        prices = [Price(
            ticker_symbol=ticker,
            date=date(2023, 1, 1),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=1000000
        )]
        
        volatility = PriceCalculator.calculate_volatility(prices, 1)
        
        # With single price, no returns to calculate, should be 0
        assert float(volatility) == 0
    
    # VWAP tests
    def test_calculate_vwap_valid(self, sample_prices):
        """Test VWAP calculation with valid data."""
        vwap = PriceCalculator.calculate_vwap(sample_prices)
        
        assert vwap is not None
        # VWAP should be within price range
        min_close = min(p.close for p in sample_prices)
        max_close = max(p.close for p in sample_prices)
        assert min_close <= float(vwap) <= max_close
    
    def test_calculate_vwap_single_price(self):
        """Test VWAP with single price."""
        ticker = TickerSymbol("7203")
        prices = [Price(
            ticker_symbol=ticker,
            date=date(2023, 1, 1),
            open=99.0,
            high=101.0,
            low=98.0,
            close=100.0,
            volume=1000000
        )]
        
        vwap = PriceCalculator.calculate_vwap(prices)
        
        # Typical price = (101 + 98 + 100) / 3 = 99.67
        expected = (101.0 + 98.0 + 100.0) / 3
        assert float(vwap) == pytest.approx(expected, rel=0.01)
    
    def test_calculate_vwap_no_volume(self):
        """Test VWAP with zero volume."""
        ticker = TickerSymbol("7203")
        prices = [Price(
            ticker_symbol=ticker,
            date=date(2023, 1, 1),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=0
        )]
        
        vwap = PriceCalculator.calculate_vwap(prices)
        assert vwap is None
    
    def test_calculate_vwap_no_data(self):
        """Test VWAP with no data."""
        with pytest.raises(InsufficientDataError) as exc_info:
            PriceCalculator.calculate_vwap([])
        
        assert exc_info.value.required == 1
        assert exc_info.value.available == 0
        assert "VWAP calculation" in str(exc_info.value)
    
    # Support/Resistance tests
    def test_identify_support_resistance_valid(self, volatile_prices):
        """Test support/resistance identification with valid data."""
        # Need more data for proper identification
        prices = volatile_prices * 3
        levels = PriceCalculator.identify_support_resistance(prices, window=2)
        
        assert "support" in levels
        assert "resistance" in levels
        assert isinstance(levels["support"], list)
        assert isinstance(levels["resistance"], list)
    
    def test_identify_support_resistance_insufficient_data(self, sample_prices):
        """Test support/resistance with insufficient data."""
        levels = PriceCalculator.identify_support_resistance(sample_prices[:5], window=5)
        
        # Should return empty lists
        assert levels["support"] == []
        assert levels["resistance"] == []
    
    def test_identify_support_resistance_trending_market(self):
        """Test support/resistance in trending market."""
        ticker = TickerSymbol("7203")
        prices = []
        
        # Create V-shaped price pattern
        for i in range(20):
            if i < 10:
                close = 100.0 - i * 2  # Falling
            else:
                close = 80.0 + (i - 10) * 2  # Rising
            
            prices.append(Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1 + i),
                open=close - 1,
                high=close + 1,
                low=close - 1,
                close=close,
                volume=1000000
            ))
        
        levels = PriceCalculator.identify_support_resistance(prices, window=3)
        
        # Should identify support around the bottom
        assert len(levels["support"]) >= 1
        # The lowest point should be around 80
        if levels["support"]:
            assert 75 < float(levels["support"][0]) < 85
    
    def test_identify_support_resistance_grouping(self):
        """Test that similar levels are grouped together."""
        ticker = TickerSymbol("7203")
        prices = []
        
        # Create prices that test around same levels multiple times
        for i in range(30):
            # Oscillate between 98-102
            if i % 4 < 2:
                close = 100.0
            else:
                close = 100.5
            
            prices.append(Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1 + i),
                open=close - 0.5,
                high=close + 0.5,
                low=close - 0.5,
                close=close,
                volume=1000000
            ))
        
        levels = PriceCalculator.identify_support_resistance(
            prices, 
            window=2, 
            threshold=Decimal("0.02")
        )
        
        # Similar levels should be grouped
        # With small threshold, nearby levels should be combined
        assert len(levels["support"]) <= 3
        assert len(levels["resistance"]) <= 3
    
    # Edge cases and error handling
    def test_decimal_precision(self, sample_prices):
        """Test that calculations maintain decimal precision."""
        sma = PriceCalculator.calculate_sma(sample_prices[:10], 10)
        
        # Should return Decimal for precision
        assert isinstance(sma, (Decimal, float))
        
        # Test with Decimal inputs
        ticker = TickerSymbol("7203")
        decimal_prices = [
            Price(
                ticker_symbol=ticker,
                date=date(2023, 1, 1),
                open=Decimal("100.123456789"),
                high=Decimal("101.123456789"),
                low=Decimal("99.123456789"),
                close=Decimal("100.123456789"),
                volume=1000000
            )
        ]
        
        vwap = PriceCalculator.calculate_vwap(decimal_prices)
        assert vwap is not None