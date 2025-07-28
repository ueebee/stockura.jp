"""Price entity."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.domain.value_objects.ticker_symbol import TickerSymbol


@dataclass
class Price:
    """Price entity representing stock price data."""
    
    ticker_symbol: TickerSymbol
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    timestamp: Optional[datetime] = None
    daily_change: Optional[Decimal] = None
    daily_change_percent: Optional[Decimal] = None
    
    def __post_init__(self):
        """Validate price data."""
        if self.high < self.low:
            raise ValueError(f"High price ({self.high}) cannot be less than low price ({self.low})")
        
        if self.high < self.open or self.high < self.close:
            raise ValueError("High price must be greater than or equal to open and close prices")
            
        if self.low > self.open or self.low > self.close:
            raise ValueError("Low price must be less than or equal to open and close prices")
            
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
    
    @property
    def typical_price(self) -> float:
        """Calculate typical price (HLC average)."""
        return (self.high + self.low + self.close) / 3
    
    @property
    def price_range(self) -> float:
        """Calculate price range (high - low)."""
        return self.high - self.low
    
    @property
    def change(self) -> float:
        """Calculate price change from open to close."""
        return self.close - self.open
    
    @property
    def change_percent(self) -> float:
        """Calculate price change percentage."""
        if self.open == 0:
            return 0.0
        return (self.change / self.open) * 100