"""Stock-related Data Transfer Objects."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class StockDTO:
    """Stock data transfer object."""

    id: Optional[int]
    ticker_symbol: str
    company_name: str
    market: str
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[float]
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_entity(cls, entity: "Stock") -> "StockDTO":
        """Create DTO from entity.

        Args:
            entity: Stock entity

        Returns:
            StockDTO instance
        """
        from app.domain.entities.stock import Stock
        
        return cls(
            id=entity.id,
            ticker_symbol=entity.ticker_symbol.value,
            company_name=entity.company_name,
            market=entity.market,
            sector=entity.sector,
            industry=entity.industry,
            market_cap=entity.market_cap,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


@dataclass
class PriceDTO:
    """Price data transfer object."""

    id: Optional[int]
    ticker_symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float]
    created_at: Optional[datetime]

    @classmethod
    def from_entity(cls, entity: "Price") -> "PriceDTO":
        """Create DTO from entity.

        Args:
            entity: Price entity

        Returns:
            PriceDTO instance
        """
        from app.domain.entities.price import Price
        
        return cls(
            id=entity.id,
            ticker_symbol=entity.ticker_symbol.value,
            timestamp=entity.timestamp,
            open=float(entity.open),
            high=float(entity.high),
            low=float(entity.low),
            close=float(entity.close),
            volume=entity.volume,
            adjusted_close=float(entity.adjusted_close) if entity.adjusted_close else None,
            created_at=entity.created_at,
        )


@dataclass
class StockPriceDTO:
    """Combined stock and price data transfer object."""

    stock: StockDTO
    current_price: Optional[PriceDTO]
    price_change: Optional[float]
    price_change_percent: Optional[float]
    volume_average: Optional[float]


@dataclass
class PriceHistoryDTO:
    """Price history data transfer object."""

    ticker_symbol: str
    period_start: datetime
    period_end: datetime
    prices: List[PriceDTO]
    highest_price: Optional[float]
    lowest_price: Optional[float]
    average_volume: Optional[float]


@dataclass
class StockAnalysisDTO:
    """Stock analysis data transfer object."""

    stock: StockDTO
    current_price: Optional[float]
    sma_20: Optional[float]
    sma_50: Optional[float]
    ema_20: Optional[float]
    rsi_14: Optional[float]
    volatility_20: Optional[float]
    support_levels: List[float]
    resistance_levels: List[float]
    recommendation: Optional[str]


@dataclass
class MarketOverviewDTO:
    """Market overview data transfer object."""

    market_name: str
    total_stocks: int
    advancing: int
    declining: int
    unchanged: int
    total_volume: int
    market_cap: float
    top_gainers: List[StockPriceDTO]
    top_losers: List[StockPriceDTO]
    most_active: List[StockPriceDTO]


@dataclass
class SearchResultDTO:
    """Search result data transfer object."""

    query: str
    total_results: int
    results: List[StockDTO]
    suggestions: List[str]


@dataclass
class CreateStockDTO:
    """DTO for creating a new stock."""

    ticker_symbol: str
    company_name: str
    market: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None


@dataclass
class UpdateStockDTO:
    """DTO for updating stock information."""

    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    market_cap: Optional[float] = None