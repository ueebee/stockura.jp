"""J-Quants client interface."""
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional

from app.domain.entities.price import Price
from app.domain.entities.stock import Stock
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod


class JQuantsClientInterface(ABC):
    """Abstract interface for J-Quants API client."""

    @abstractmethod
    async def authenticate(self) -> str:
        """Authenticate with J-Quants API and get access token.

        Returns:
            Access token

        Raises:
            ExternalAPIError: If authentication fails
        """
        pass

    @abstractmethod
    async def get_stock_info(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        """Get stock information from J-Quants.

        Args:
            ticker_symbol: Ticker symbol value object

        Returns:
            Stock entity or None if not found

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_stock_prices(
        self,
        ticker_symbol: TickerSymbol,
        period: TimePeriod
    ) -> List[Price]:
        """Get historical stock prices.

        Args:
            ticker_symbol: Ticker symbol value object
            period: Time period for price data

        Returns:
            List of price entities

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_daily_quotes(
        self,
        ticker_symbol: TickerSymbol,
        target_date: date
    ) -> Optional[Price]:
        """Get daily quote for a specific date.

        Args:
            ticker_symbol: Ticker symbol value object
            target_date: Target date

        Returns:
            Price entity or None if not available

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_listed_stocks(
        self,
        market: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Get list of all listed stocks.

        Args:
            market: Filter by market (e.g., 'TSE')

        Returns:
            List of stock information dictionaries

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_financial_data(
        self,
        ticker_symbol: TickerSymbol,
        fiscal_year: Optional[int] = None
    ) -> Dict[str, any]:
        """Get financial data for a stock.

        Args:
            ticker_symbol: Ticker symbol value object
            fiscal_year: Specific fiscal year (optional)

        Returns:
            Financial data dictionary

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_market_indices(self) -> Dict[str, float]:
        """Get current market indices (TOPIX, Nikkei 225, etc.).

        Returns:
            Dictionary of index names and values

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_trading_calendar(
        self,
        year: int,
        month: Optional[int] = None
    ) -> List[date]:
        """Get trading calendar (business days).

        Args:
            year: Target year
            month: Target month (optional)

        Returns:
            List of trading dates

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def is_trading_day(self, target_date: date) -> bool:
        """Check if a date is a trading day.

        Args:
            target_date: Date to check

        Returns:
            True if trading day, False otherwise

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_sectors(self) -> List[str]:
        """Get list of all sectors.

        Returns:
            List of sector names

        Raises:
            ExternalAPIError: If API request fails
        """
        pass