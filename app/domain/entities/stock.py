"""Stock entity module."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.value_objects.ticker_symbol import TickerSymbol


@dataclass
class Stock:
    """Stock entity representing a stock/security."""

    id: Optional[int] = field(default=None)
    ticker_symbol: TickerSymbol = field(default_factory=TickerSymbol)
    company_name: str = ""
    market: str = ""
    sector: Optional[str] = field(default=None)
    industry: Optional[str] = field(default=None)
    market_cap: Optional[float] = field(default=None)
    description: Optional[str] = field(default=None)
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        """Post initialization validation."""
        if not self.company_name:
            raise ValueError("Company name is required")
        if not self.market:
            raise ValueError("Market is required")

    @property
    def is_persisted(self) -> bool:
        """Check if the entity is persisted in the database."""
        return self.id is not None

    def update_market_cap(self, market_cap: float) -> None:
        """Update market capitalization.

        Args:
            market_cap: New market capitalization value
        """
        if market_cap < 0:
            raise ValueError("Market cap cannot be negative")
        self.market_cap = market_cap
        self.updated_at = datetime.utcnow()

    def update_info(
        self,
        company_name: Optional[str] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Update stock information.

        Args:
            company_name: Company name
            sector: Business sector
            industry: Industry classification
            description: Company description
        """
        if company_name is not None:
            self.company_name = company_name
        if sector is not None:
            self.sector = sector
        if industry is not None:
            self.industry = industry
        if description is not None:
            self.description = description
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation."""
        return f"Stock({self.ticker_symbol.value}: {self.company_name})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Stock(id={self.id}, ticker={self.ticker_symbol.value}, "
            f"company={self.company_name}, market={self.market})"
        )