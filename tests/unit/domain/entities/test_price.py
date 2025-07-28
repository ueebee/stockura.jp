"""Unit tests for Price entity."""
import pytest
from datetime import date, datetime
from decimal import Decimal

from app.domain.entities.price import Price
from app.domain.value_objects.ticker_symbol import TickerSymbol


class TestPrice:
    """Test cases for Price entity."""
    
    @pytest.fixture
    def ticker_symbol(self):
        """Create a ticker symbol for testing."""
        return TickerSymbol("7203")
    
    @pytest.fixture
    def valid_price_data(self, ticker_symbol):
        """Valid price data for testing."""
        return {
            "ticker_symbol": ticker_symbol,
            "date": date(2023, 1, 4),
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000000
        }
    
    # Initialization tests
    def test_init_valid_price(self, valid_price_data):
        """Test initialization with valid data."""
        price = Price(**valid_price_data)
        
        assert price.ticker_symbol.value == "7203"
        assert price.date == date(2023, 1, 4)
        assert price.open == 100.0
        assert price.high == 105.0
        assert price.low == 99.0
        assert price.close == 103.0
        assert price.volume == 1000000
        assert price.adjusted_close is None
        assert price.timestamp is None
        assert price.daily_change is None
        assert price.daily_change_percent is None
    
    def test_init_with_all_fields(self, ticker_symbol):
        """Test initialization with all optional fields."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000,
            adjusted_close=102.5,
            timestamp=datetime(2023, 1, 4, 15, 0, 0),
            daily_change=Decimal("3.0"),
            daily_change_percent=Decimal("3.0")
        )
        
        assert price.adjusted_close == 102.5
        assert price.timestamp == datetime(2023, 1, 4, 15, 0, 0)
        assert price.daily_change == Decimal("3.0")
        assert price.daily_change_percent == Decimal("3.0")
    
    def test_init_high_less_than_low(self, ticker_symbol):
        """Test initialization with high < low."""
        with pytest.raises(ValueError, match="High price.*cannot be less than low price"):
            Price(
                ticker_symbol=ticker_symbol,
                date=date(2023, 1, 4),
                open=100.0,
                high=98.0,  # Less than low
                low=99.0,
                close=100.0,
                volume=1000000
            )
    
    def test_init_high_less_than_open(self, ticker_symbol):
        """Test initialization with high < open."""
        with pytest.raises(ValueError, match="High price must be greater than or equal to open and close"):
            Price(
                ticker_symbol=ticker_symbol,
                date=date(2023, 1, 4),
                open=106.0,  # Greater than high
                high=105.0,
                low=99.0,
                close=103.0,
                volume=1000000
            )
    
    def test_init_high_less_than_close(self, ticker_symbol):
        """Test initialization with high < close."""
        with pytest.raises(ValueError, match="High price must be greater than or equal to open and close"):
            Price(
                ticker_symbol=ticker_symbol,
                date=date(2023, 1, 4),
                open=100.0,
                high=105.0,
                low=99.0,
                close=106.0,  # Greater than high
                volume=1000000
            )
    
    def test_init_low_greater_than_open(self, ticker_symbol):
        """Test initialization with low > open."""
        with pytest.raises(ValueError, match="Low price must be less than or equal to open and close"):
            Price(
                ticker_symbol=ticker_symbol,
                date=date(2023, 1, 4),
                open=98.0,  # Less than low
                high=105.0,
                low=99.0,
                close=103.0,
                volume=1000000
            )
    
    def test_init_low_greater_than_close(self, ticker_symbol):
        """Test initialization with low > close."""
        with pytest.raises(ValueError, match="Low price must be less than or equal to open and close"):
            Price(
                ticker_symbol=ticker_symbol,
                date=date(2023, 1, 4),
                open=100.0,
                high=105.0,
                low=99.0,
                close=98.0,  # Less than low
                volume=1000000
            )
    
    def test_init_negative_volume(self, ticker_symbol):
        """Test initialization with negative volume."""
        with pytest.raises(ValueError, match="Volume cannot be negative"):
            Price(
                ticker_symbol=ticker_symbol,
                date=date(2023, 1, 4),
                open=100.0,
                high=105.0,
                low=99.0,
                close=103.0,
                volume=-1000
            )
    
    def test_init_zero_volume(self, ticker_symbol):
        """Test initialization with zero volume (valid)."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=0
        )
        assert price.volume == 0
    
    # Edge cases for price validation
    def test_init_all_prices_equal(self, ticker_symbol):
        """Test when all prices are equal (valid scenario)."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000
        )
        assert price.open == price.high == price.low == price.close == 100.0
    
    def test_init_open_equals_high(self, ticker_symbol):
        """Test when open equals high (valid)."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=105.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        assert price.open == price.high
    
    def test_init_close_equals_low(self, ticker_symbol):
        """Test when close equals low (valid)."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=99.0,
            volume=1000000
        )
        assert price.close == price.low
    
    # Property tests
    def test_typical_price(self, valid_price_data):
        """Test typical price calculation."""
        price = Price(**valid_price_data)
        # (105 + 99 + 103) / 3 = 102.33...
        expected = (105.0 + 99.0 + 103.0) / 3
        assert price.typical_price == pytest.approx(expected, rel=1e-9)
    
    def test_typical_price_all_equal(self, ticker_symbol):
        """Test typical price when all prices are equal."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000
        )
        assert price.typical_price == 100.0
    
    def test_price_range(self, valid_price_data):
        """Test price range calculation."""
        price = Price(**valid_price_data)
        # 105 - 99 = 6
        assert price.price_range == 6.0
    
    def test_price_range_no_movement(self, ticker_symbol):
        """Test price range when high equals low."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=1000000
        )
        assert price.price_range == 0.0
    
    def test_change(self, valid_price_data):
        """Test price change calculation."""
        price = Price(**valid_price_data)
        # 103 - 100 = 3
        assert price.change == 3.0
    
    def test_change_negative(self, ticker_symbol):
        """Test negative price change."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=95.0,
            close=97.0,
            volume=1000000
        )
        # 97 - 100 = -3
        assert price.change == -3.0
    
    def test_change_no_movement(self, ticker_symbol):
        """Test price change when open equals close."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=100.0,
            volume=1000000
        )
        assert price.change == 0.0
    
    def test_change_percent(self, valid_price_data):
        """Test price change percentage calculation."""
        price = Price(**valid_price_data)
        # (3 / 100) * 100 = 3%
        assert price.change_percent == 3.0
    
    def test_change_percent_negative(self, ticker_symbol):
        """Test negative price change percentage."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=95.0,
            close=95.0,
            volume=1000000
        )
        # (-5 / 100) * 100 = -5%
        assert price.change_percent == -5.0
    
    def test_change_percent_zero_open(self, ticker_symbol):
        """Test change percentage when open is zero."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=0.0,
            high=1.0,
            low=0.0,
            close=1.0,
            volume=1000000
        )
        assert price.change_percent == 0.0
    
    def test_change_percent_large_gain(self, ticker_symbol):
        """Test large price gain percentage."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=210.0,
            low=99.0,
            close=200.0,
            volume=1000000
        )
        # (100 / 100) * 100 = 100%
        assert price.change_percent == 100.0
    
    # Integration tests
    def test_price_with_fractional_values(self, ticker_symbol):
        """Test price with fractional values."""
        price = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.25,
            high=105.75,
            low=99.50,
            close=103.33,
            volume=1234567
        )
        
        assert price.open == 100.25
        assert price.high == 105.75
        assert price.low == 99.50
        assert price.close == 103.33
        assert price.change == pytest.approx(3.08, rel=1e-9)
        # (3.08 / 100.25) * 100 = 3.072319...
        assert price.change_percent == pytest.approx(3.072319, rel=1e-5)
    
    def test_price_dataclass_features(self, valid_price_data):
        """Test dataclass features (not frozen by default)."""
        price = Price(**valid_price_data)
        
        # Can modify attributes (dataclass is not frozen)
        price.volume = 2000000
        assert price.volume == 2000000
        
        # Has __repr__
        repr_str = repr(price)
        assert "Price(" in repr_str
        assert "ticker_symbol=" in repr_str
        assert "date=" in repr_str
    
    def test_price_equality(self, ticker_symbol):
        """Test price equality."""
        price1 = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        price2 = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        price3 = Price(
            ticker_symbol=ticker_symbol,
            date=date(2023, 1, 5),  # Different date
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        assert price1 == price2
        assert price1 != price3
    
    def test_price_with_different_ticker_symbols(self):
        """Test prices with different ticker symbols."""
        ticker1 = TickerSymbol("7203")
        ticker2 = TickerSymbol("6758")
        
        price1 = Price(
            ticker_symbol=ticker1,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        price2 = Price(
            ticker_symbol=ticker2,
            date=date(2023, 1, 4),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        assert price1 != price2
        assert price1.ticker_symbol != price2.ticker_symbol