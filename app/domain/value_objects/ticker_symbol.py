"""Ticker symbol value object module."""
import re
from typing import Any

from app.core.constants import TICKER_SYMBOL_REGEX


class TickerSymbol:
    """Value object representing a stock ticker symbol."""

    def __init__(self, value: str = "") -> None:
        """Initialize ticker symbol.

        Args:
            value: Ticker symbol string

        Raises:
            ValueError: If ticker symbol is invalid
        """
        self._value = self._validate_and_normalize(value)

    @property
    def value(self) -> str:
        """Get ticker symbol value."""
        return self._value

    def _validate_and_normalize(self, value: str) -> str:
        """Validate and normalize ticker symbol.

        Args:
            value: Raw ticker symbol

        Returns:
            Normalized ticker symbol

        Raises:
            ValueError: If ticker symbol is invalid
        """
        if not value:
            return ""
        
        # Normalize to uppercase
        normalized = value.upper().strip()
        
        # Validate format
        if not re.match(TICKER_SYMBOL_REGEX, normalized):
            raise ValueError(
                f"Invalid ticker symbol: {value}. "
                f"Must be 1-10 uppercase alphanumeric characters."
            )
        
        return normalized

    def __str__(self) -> str:
        """String representation."""
        return self._value

    def __repr__(self) -> str:
        """Developer representation."""
        return f"TickerSymbol('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, TickerSymbol):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Get hash value."""
        return hash(self._value)

    def __bool__(self) -> bool:
        """Check if ticker symbol has a value."""
        return bool(self._value)

    def to_jquants_format(self) -> str:
        """Convert to J-Quants API format.

        Returns:
            Ticker symbol in J-Quants format (with .T suffix for TSE stocks)
        """
        if self._value.isdigit() and len(self._value) == 4:
            return f"{self._value}.T"
        return self._value

    def to_yfinance_format(self) -> str:
        """Convert to yFinance format.

        Returns:
            Ticker symbol in yFinance format
        """
        # For Japanese stocks, yfinance uses the format "1234.T"
        if self._value.isdigit() and len(self._value) == 4:
            return f"{self._value}.T"
        return self._value

    @classmethod
    def from_string(cls, value: str) -> "TickerSymbol":
        """Create TickerSymbol from string.

        Args:
            value: Ticker symbol string

        Returns:
            TickerSymbol instance
        """
        return cls(value)