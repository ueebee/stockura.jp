"""Price entity module."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.value_objects.ticker_symbol import TickerSymbol


@dataclass
class Price:
    """Price entity representing stock price data."""

    id: Optional[int] = field(default=None)
    ticker_symbol: TickerSymbol = field(default_factory=TickerSymbol)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    open: Decimal = field(default_factory=Decimal)
    high: Decimal = field(default_factory=Decimal)
    low: Decimal = field(default_factory=Decimal)
    close: Decimal = field(default_factory=Decimal)
    volume: int = 0
    adjusted_close: Optional[Decimal] = field(default=None)
    created_at: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        """Post initialization validation."""
        self._validate_prices()
        self._validate_volume()

    def _validate_prices(self) -> None:
        """Validate price values."""
        if any(price < 0 for price in [self.open, self.high, self.low, self.close]):
            raise ValueError("Price values cannot be negative")
        
        if self.high < self.low:
            raise ValueError("High price cannot be less than low price")
        
        if self.high < self.open or self.high < self.close:
            raise ValueError("High price must be the highest price of the period")
        
        if self.low > self.open or self.low > self.close:
            raise ValueError("Low price must be the lowest price of the period")

    def _validate_volume(self) -> None:
        """Validate volume."""
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

    @property
    def is_persisted(self) -> bool:
        """Check if the entity is persisted in the database."""
        return self.id is not None

    @property
    def price_range(self) -> Decimal:
        """Calculate the price range (high - low)."""
        return self.high - self.low

    @property
    def daily_change(self) -> Decimal:
        """Calculate daily change (close - open)."""
        return self.close - self.open

    @property
    def daily_change_percent(self) -> Decimal:
        """Calculate daily change percentage."""
        if self.open == 0:
            return Decimal("0")
        return ((self.close - self.open) / self.open) * 100

    @property
    def is_bullish(self) -> bool:
        """Check if the day was bullish (close > open)."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Check if the day was bearish (close < open)."""
        return self.close < self.open

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Price({self.ticker_symbol.value} @ {self.timestamp.strftime('%Y-%m-%d')}: "
            f"O={self.open}, H={self.high}, L={self.low}, C={self.close})"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Price(id={self.id}, ticker={self.ticker_symbol.value}, "
            f"timestamp={self.timestamp.isoformat()}, close={self.close})"
        )