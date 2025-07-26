"""yFinance client interface."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from app.domain.entities.price import Price
from app.domain.entities.stock import Stock
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod


class YFinanceClientInterface(ABC):
    """Abstract interface for yFinance API client."""

    @abstractmethod
    async def get_stock_info(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        """Get stock information from yFinance.

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
        period: TimePeriod,
        interval: str = "1d"
    ) -> List[Price]:
        """Get historical stock prices.

        Args:
            ticker_symbol: Ticker symbol value object
            period: Time period for price data
            interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)

        Returns:
            List of price entities

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_realtime_price(
        self,
        ticker_symbol: TickerSymbol
    ) -> Optional[Dict[str, float]]:
        """Get real-time price data.

        Args:
            ticker_symbol: Ticker symbol value object

        Returns:
            Dictionary with current price data or None

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_options_chain(
        self,
        ticker_symbol: TickerSymbol,
        expiration_date: Optional[datetime] = None
    ) -> Dict[str, any]:
        """Get options chain data.

        Args:
            ticker_symbol: Ticker symbol value object
            expiration_date: Options expiration date

        Returns:
            Options chain data

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_dividends(
        self,
        ticker_symbol: TickerSymbol,
        period: TimePeriod
    ) -> List[Dict[str, any]]:
        """Get dividend history.

        Args:
            ticker_symbol: Ticker symbol value object
            period: Time period for dividend data

        Returns:
            List of dividend records

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_splits(
        self,
        ticker_symbol: TickerSymbol,
        period: TimePeriod
    ) -> List[Dict[str, any]]:
        """Get stock split history.

        Args:
            ticker_symbol: Ticker symbol value object
            period: Time period for split data

        Returns:
            List of split records

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_major_holders(
        self,
        ticker_symbol: TickerSymbol
    ) -> Dict[str, any]:
        """Get major shareholders information.

        Args:
            ticker_symbol: Ticker symbol value object

        Returns:
            Major holders data

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_institutional_holders(
        self,
        ticker_symbol: TickerSymbol
    ) -> List[Dict[str, any]]:
        """Get institutional holders information.

        Args:
            ticker_symbol: Ticker symbol value object

        Returns:
            List of institutional holders

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_recommendations(
        self,
        ticker_symbol: TickerSymbol
    ) -> List[Dict[str, any]]:
        """Get analyst recommendations.

        Args:
            ticker_symbol: Ticker symbol value object

        Returns:
            List of recommendations

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def search_symbols(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Search for ticker symbols.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching symbols with basic info

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_market_summary(self) -> Dict[str, any]:
        """Get overall market summary.

        Returns:
            Market summary data

        Raises:
            ExternalAPIError: If API request fails
        """
        pass

    @abstractmethod
    async def get_trending_tickers(self) -> List[str]:
        """Get trending ticker symbols.

        Returns:
            List of trending ticker symbols

        Raises:
            ExternalAPIError: If API request fails
        """
        pass