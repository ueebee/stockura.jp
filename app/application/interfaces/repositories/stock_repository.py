"""Stock repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.stock import Stock
from app.domain.value_objects.ticker_symbol import TickerSymbol


class StockRepositoryInterface(ABC):
    """Abstract interface for stock repository."""

    @abstractmethod
    async def find_by_id(self, stock_id: int) -> Optional[Stock]:
        """Find stock by ID.

        Args:
            stock_id: Stock ID

        Returns:
            Stock entity or None if not found
        """
        pass

    @abstractmethod
    async def find_by_ticker(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        """Find stock by ticker symbol.

        Args:
            ticker_symbol: Ticker symbol value object

        Returns:
            Stock entity or None if not found
        """
        pass

    @abstractmethod
    async def find_all(
        self,
        market: Optional[str] = None,
        sector: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Stock]:
        """Find all stocks with optional filters.

        Args:
            market: Filter by market
            sector: Filter by sector
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of stock entities
        """
        pass

    @abstractmethod
    async def save(self, stock: Stock) -> Stock:
        """Save or update a stock.

        Args:
            stock: Stock entity to save

        Returns:
            Saved stock entity with ID
        """
        pass

    @abstractmethod
    async def delete(self, stock_id: int) -> bool:
        """Delete a stock by ID.

        Args:
            stock_id: Stock ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, ticker_symbol: TickerSymbol) -> bool:
        """Check if stock exists by ticker symbol.

        Args:
            ticker_symbol: Ticker symbol value object

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def count(
        self,
        market: Optional[str] = None,
        sector: Optional[str] = None
    ) -> int:
        """Count stocks with optional filters.

        Args:
            market: Filter by market
            sector: Filter by sector

        Returns:
            Number of stocks matching criteria
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Stock]:
        """Search stocks by company name or ticker.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching stock entities
        """
        pass

    @abstractmethod
    async def find_by_market(self, market: str) -> List[Stock]:
        """Find all stocks in a specific market.

        Args:
            market: Market name

        Returns:
            List of stock entities in the market
        """
        pass

    @abstractmethod
    async def update_market_cap(
        self,
        ticker_symbol: TickerSymbol,
        market_cap: float
    ) -> bool:
        """Update market capitalization for a stock.

        Args:
            ticker_symbol: Ticker symbol value object
            market_cap: New market cap value

        Returns:
            True if updated, False if not found
        """
        pass