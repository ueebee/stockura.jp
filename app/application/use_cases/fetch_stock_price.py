"""Fetch stock price use case."""
from datetime import date
from typing import Optional

from app.application.dtos.stock_dto import PriceDTO, StockPriceDTO, StockDTO
from app.application.interfaces.external.jquants_client import JQuantsClientInterface
from app.application.interfaces.external.yfinance_client import YFinanceClientInterface
from app.application.interfaces.repositories.stock_repository import (
    StockRepositoryInterface,
)
from app.core.logger import get_logger
from app.domain.exceptions.stock_exceptions import StockNotFoundError
from app.domain.value_objects.ticker_symbol import TickerSymbol

logger = get_logger(__name__)


class FetchStockPriceUseCase:
    """Use case for fetching stock prices."""

    def __init__(
        self,
        stock_repository: StockRepositoryInterface,
        jquants_client: JQuantsClientInterface,
        yfinance_client: YFinanceClientInterface,
    ) -> None:
        """Initialize use case.

        Args:
            stock_repository: Stock repository interface
            jquants_client: J-Quants client interface
            yfinance_client: yFinance client interface
        """
        self._stock_repository = stock_repository
        self._jquants_client = jquants_client
        self._yfinance_client = yfinance_client

    async def execute(
        self,
        ticker_symbol_str: str,
        target_date: Optional[date] = None,
        source: str = "jquants",
    ) -> StockPriceDTO:
        """Execute fetch stock price use case.

        Args:
            ticker_symbol_str: Ticker symbol string
            target_date: Target date for price (defaults to latest)
            source: Data source ('jquants' or 'yfinance')

        Returns:
            Stock price DTO

        Raises:
            StockNotFoundError: If stock not found
            ValueError: If invalid parameters
        """
        # Validate and create ticker symbol
        ticker_symbol = TickerSymbol(ticker_symbol_str)
        
        # Get stock information from repository
        stock = await self._stock_repository.find_by_ticker(ticker_symbol)
        if not stock:
            logger.warning(f"Stock not found in repository: {ticker_symbol}")
            # Try to fetch from external source
            if source == "jquants":
                stock = await self._jquants_client.get_stock_info(ticker_symbol)
            else:
                stock = await self._yfinance_client.get_stock_info(ticker_symbol)
            
            if not stock:
                raise StockNotFoundError(ticker_symbol_str)
            
            # Save to repository for future use
            stock = await self._stock_repository.save(stock)
            logger.info(f"Stock saved to repository: {ticker_symbol}")

        # Fetch price data
        if target_date:
            price = await self._fetch_price_for_date(ticker_symbol, target_date, source)
        else:
            price = await self._fetch_latest_price(ticker_symbol, source)

        if not price:
            logger.warning(f"No price data available for {ticker_symbol}")
            return StockPriceDTO(
                stock=StockDTO.from_entity(stock),
                current_price=None,
                price_change=None,
                price_change_percent=None,
                volume_average=None,
            )

        # Calculate price changes
        price_change = None
        price_change_percent = None
        
        if price.daily_change:
            price_change = float(price.daily_change)
            price_change_percent = float(price.daily_change_percent)

        return StockPriceDTO(
            stock=StockDTO.from_entity(stock),
            current_price=PriceDTO.from_entity(price),
            price_change=price_change,
            price_change_percent=price_change_percent,
            volume_average=float(price.volume),
        )

    async def _fetch_price_for_date(
        self,
        ticker_symbol: TickerSymbol,
        target_date: date,
        source: str,
    ) -> Optional["Price"]:
        """Fetch price for specific date.

        Args:
            ticker_symbol: Ticker symbol
            target_date: Target date
            source: Data source

        Returns:
            Price entity or None
        """
        if source == "jquants":
            return await self._jquants_client.get_daily_quotes(ticker_symbol, target_date)
        else:
            # For yFinance, we need to fetch a range and extract the date
            from app.domain.value_objects.time_period import TimePeriod
            
            period = TimePeriod(start_date=target_date, end_date=target_date)
            prices = await self._yfinance_client.get_stock_prices(
                ticker_symbol, period, interval="1d"
            )
            return prices[0] if prices else None

    async def _fetch_latest_price(
        self,
        ticker_symbol: TickerSymbol,
        source: str,
    ) -> Optional["Price"]:
        """Fetch latest price.

        Args:
            ticker_symbol: Ticker symbol
            source: Data source

        Returns:
            Price entity or None
        """
        if source == "jquants":
            # Get today's date or last trading day
            today = date.today()
            return await self._jquants_client.get_daily_quotes(ticker_symbol, today)
        else:
            # Get real-time data from yFinance
            from decimal import Decimal
            from datetime import datetime
            from app.domain.entities.price import Price
            
            realtime = await self._yfinance_client.get_realtime_price(ticker_symbol)
            if not realtime:
                return None
            
            return Price(
                ticker_symbol=ticker_symbol,
                date=date.today(),
                timestamp=datetime.now(),
                open=float(realtime.get("open", 0)),
                high=float(realtime.get("high", 0)),
                low=float(realtime.get("low", 0)),
                close=float(realtime.get("close", 0)),
                volume=int(realtime.get("volume", 0)),
            )