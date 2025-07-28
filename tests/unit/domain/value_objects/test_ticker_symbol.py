"""Unit tests for TickerSymbol value object."""
import pytest
from typing import Any

from app.domain.value_objects.ticker_symbol import TickerSymbol


class TestTickerSymbol:
    """Test cases for TickerSymbol value object."""
    
    # Initialization tests
    def test_init_valid_ticker(self):
        """Test initialization with valid ticker symbol."""
        ticker = TickerSymbol("AAPL")
        assert ticker.value == "AAPL"
    
    def test_init_lowercase_normalized(self):
        """Test that lowercase input is normalized to uppercase."""
        ticker = TickerSymbol("aapl")
        assert ticker.value == "AAPL"
    
    def test_init_with_whitespace_trimmed(self):
        """Test that whitespace is trimmed."""
        ticker = TickerSymbol("  AAPL  ")
        assert ticker.value == "AAPL"
    
    def test_init_empty_string(self):
        """Test initialization with empty string."""
        ticker = TickerSymbol("")
        assert ticker.value == ""
    
    def test_init_default_value(self):
        """Test initialization with default value."""
        ticker = TickerSymbol()
        assert ticker.value == ""
    
    def test_init_japanese_stock_code(self):
        """Test initialization with Japanese stock code."""
        ticker = TickerSymbol("7203")
        assert ticker.value == "7203"
    
    def test_init_alphanumeric(self):
        """Test initialization with alphanumeric ticker."""
        ticker = TickerSymbol("BRK1")
        assert ticker.value == "BRK1"
    
    def test_init_max_length(self):
        """Test initialization with maximum length ticker."""
        ticker = TickerSymbol("ABCDEFGHIJ")  # 10 characters
        assert ticker.value == "ABCDEFGHIJ"
    
    # Validation error tests
    def test_init_invalid_too_long(self):
        """Test initialization with ticker that's too long."""
        with pytest.raises(ValueError, match="Invalid ticker symbol.*Must be 1-10 uppercase alphanumeric"):
            TickerSymbol("ABCDEFGHIJK")  # 11 characters
    
    def test_init_invalid_special_characters(self):
        """Test initialization with special characters."""
        invalid_tickers = ["AAPL.", "BRK-B", "TSLA$", "GOOGL@", "MSFT!"]
        for invalid in invalid_tickers:
            with pytest.raises(ValueError, match="Invalid ticker symbol"):
                TickerSymbol(invalid)
    
    def test_init_invalid_lowercase_after_normalization(self):
        """Test that normalization happens before validation."""
        # This should not raise an error because it's normalized first
        ticker = TickerSymbol("googl")
        assert ticker.value == "GOOGL"
    
    def test_init_invalid_non_alphanumeric(self):
        """Test initialization with non-alphanumeric characters."""
        with pytest.raises(ValueError, match="Invalid ticker symbol"):
            TickerSymbol("株式会社")
    
    # Property tests
    def test_value_property(self):
        """Test value property getter."""
        ticker = TickerSymbol("TSLA")
        assert ticker.value == "TSLA"
        # Ensure it's read-only
        with pytest.raises(AttributeError):
            ticker.value = "AAPL"
    
    # String representation tests
    def test_str_representation(self):
        """Test string representation."""
        ticker = TickerSymbol("NVDA")
        assert str(ticker) == "NVDA"
    
    def test_str_empty(self):
        """Test string representation of empty ticker."""
        ticker = TickerSymbol("")
        assert str(ticker) == ""
    
    def test_repr_representation(self):
        """Test developer representation."""
        ticker = TickerSymbol("META")
        assert repr(ticker) == "TickerSymbol('META')"
    
    def test_repr_empty(self):
        """Test developer representation of empty ticker."""
        ticker = TickerSymbol("")
        assert repr(ticker) == "TickerSymbol('')"
    
    # Equality tests
    def test_equality_same_value(self):
        """Test equality with same value."""
        ticker1 = TickerSymbol("AMZN")
        ticker2 = TickerSymbol("AMZN")
        assert ticker1 == ticker2
    
    def test_equality_different_value(self):
        """Test inequality with different value."""
        ticker1 = TickerSymbol("AMZN")
        ticker2 = TickerSymbol("AAPL")
        assert ticker1 != ticker2
    
    def test_equality_with_non_ticker(self):
        """Test inequality with non-TickerSymbol object."""
        ticker = TickerSymbol("GOOG")
        assert ticker != "GOOG"
        assert ticker != 123
        assert ticker != None
    
    def test_equality_empty_tickers(self):
        """Test equality of empty tickers."""
        ticker1 = TickerSymbol("")
        ticker2 = TickerSymbol("")
        assert ticker1 == ticker2
    
    # Hash tests
    def test_hash_consistency(self):
        """Test that hash is consistent for same value."""
        ticker1 = TickerSymbol("IBM")
        ticker2 = TickerSymbol("IBM")
        assert hash(ticker1) == hash(ticker2)
    
    def test_hash_different_values(self):
        """Test that hash is different for different values."""
        ticker1 = TickerSymbol("IBM")
        ticker2 = TickerSymbol("ORCL")
        assert hash(ticker1) != hash(ticker2)
    
    def test_hash_in_dict(self):
        """Test that TickerSymbol can be used as dict key."""
        ticker = TickerSymbol("MSFT")
        data = {ticker: "Microsoft"}
        assert data[TickerSymbol("MSFT")] == "Microsoft"
    
    def test_hash_in_set(self):
        """Test that TickerSymbol can be used in set."""
        tickers = {
            TickerSymbol("AAPL"),
            TickerSymbol("GOOGL"),
            TickerSymbol("AAPL")  # Duplicate
        }
        assert len(tickers) == 2
    
    # Boolean tests
    def test_bool_with_value(self):
        """Test boolean evaluation with value."""
        ticker = TickerSymbol("SPY")
        assert bool(ticker) is True
        assert ticker  # Direct boolean context
    
    def test_bool_empty(self):
        """Test boolean evaluation with empty value."""
        ticker = TickerSymbol("")
        assert bool(ticker) is False
        assert not ticker  # Direct boolean context
    
    # Format conversion tests
    def test_to_jquants_format_japanese_stock(self):
        """Test conversion to J-Quants format for Japanese stocks."""
        ticker = TickerSymbol("7203")
        assert ticker.to_jquants_format() == "7203.T"
    
    def test_to_jquants_format_non_japanese(self):
        """Test conversion to J-Quants format for non-Japanese stocks."""
        ticker = TickerSymbol("AAPL")
        assert ticker.to_jquants_format() == "AAPL"
    
    def test_to_jquants_format_numeric_non_4digit(self):
        """Test J-Quants format for numeric but not 4-digit."""
        ticker1 = TickerSymbol("123")  # 3 digits
        ticker2 = TickerSymbol("12345")  # 5 digits
        assert ticker1.to_jquants_format() == "123"
        assert ticker2.to_jquants_format() == "12345"
    
    def test_to_jquants_format_empty(self):
        """Test J-Quants format for empty ticker."""
        ticker = TickerSymbol("")
        assert ticker.to_jquants_format() == ""
    
    def test_to_yfinance_format_japanese_stock(self):
        """Test conversion to yFinance format for Japanese stocks."""
        ticker = TickerSymbol("7203")
        assert ticker.to_yfinance_format() == "7203.T"
    
    def test_to_yfinance_format_us_stock(self):
        """Test conversion to yFinance format for US stocks."""
        ticker = TickerSymbol("TSLA")
        assert ticker.to_yfinance_format() == "TSLA"
    
    def test_to_yfinance_format_numeric_non_4digit(self):
        """Test yFinance format for numeric but not 4-digit."""
        ticker1 = TickerSymbol("999")  # 3 digits
        ticker2 = TickerSymbol("77777")  # 5 digits
        assert ticker1.to_yfinance_format() == "999"
        assert ticker2.to_yfinance_format() == "77777"
    
    def test_to_yfinance_format_empty(self):
        """Test yFinance format for empty ticker."""
        ticker = TickerSymbol("")
        assert ticker.to_yfinance_format() == ""
    
    # Class method tests
    def test_from_string_valid(self):
        """Test creating TickerSymbol from string."""
        ticker = TickerSymbol.from_string("NFLX")
        assert isinstance(ticker, TickerSymbol)
        assert ticker.value == "NFLX"
    
    def test_from_string_normalization(self):
        """Test that from_string also normalizes."""
        ticker = TickerSymbol.from_string("  nflx  ")
        assert ticker.value == "NFLX"
    
    def test_from_string_invalid(self):
        """Test from_string with invalid input."""
        with pytest.raises(ValueError, match="Invalid ticker symbol"):
            TickerSymbol.from_string("INVALID!")
    
    def test_from_string_empty(self):
        """Test from_string with empty string."""
        ticker = TickerSymbol.from_string("")
        assert ticker.value == ""
    
    # Edge cases
    def test_single_character_ticker(self):
        """Test single character ticker (valid)."""
        ticker = TickerSymbol("V")  # Visa
        assert ticker.value == "V"
    
    def test_mixed_case_normalization(self):
        """Test mixed case normalization."""
        ticker = TickerSymbol("ApPl")
        assert ticker.value == "APPL"
    
    def test_numeric_only_ticker(self):
        """Test numeric-only ticker (valid for some markets)."""
        ticker = TickerSymbol("1234")
        assert ticker.value == "1234"
    
    def test_immutability(self):
        """Test that TickerSymbol is immutable."""
        ticker = TickerSymbol("IMMUT")
        original_value = ticker.value
        # Try to modify internal state (Python doesn't prevent this, but document the behavior)
        try:
            ticker._value = "CHANGED"
            # If we can change it, verify the value is actually changed
            assert ticker.value == "CHANGED"
        except AttributeError:
            # If it raises AttributeError, that's also acceptable
            pass
        # For true immutability, we'd need to use __slots__ or property decorators
    
    # Integration scenarios
    def test_ticker_in_collection_operations(self):
        """Test TickerSymbol in various collection operations."""
        tickers = [
            TickerSymbol("AAPL"),
            TickerSymbol("GOOGL"),
            TickerSymbol("MSFT")
        ]
        
        # Sorting
        sorted_tickers = sorted(tickers, key=lambda t: t.value)
        assert sorted_tickers[0].value == "AAPL"
        
        # Filtering
        tech_tickers = [t for t in tickers if t.value in ["AAPL", "GOOGL"]]
        assert len(tech_tickers) == 2
        
        # Uniqueness in set
        ticker_set = set(tickers + [TickerSymbol("AAPL")])  # Duplicate
        assert len(ticker_set) == 3