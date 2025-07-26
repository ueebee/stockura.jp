"""Analyze stock use case."""
from typing import List

from app.application.dtos.stock_dto import StockAnalysisDTO, StockDTO
from app.application.interfaces.external.jquants_client import JQuantsClientInterface
from app.application.interfaces.external.yfinance_client import YFinanceClientInterface
from app.application.interfaces.repositories.stock_repository import (
    StockRepositoryInterface,
)
from app.core.logger import get_logger
from app.domain.entities.price import Price
from app.domain.exceptions.stock_exceptions import (
    InsufficientDataError,
    StockNotFoundError,
)
from app.domain.services.price_calculator import PriceCalculator
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod

logger = get_logger(__name__)


class AnalyzeStockUseCase:
    """Use case for analyzing stock technical indicators."""

    def __init__(
        self,
        stock_repository: StockRepositoryInterface,
        jquants_client: JQuantsClientInterface,
        yfinance_client: YFinanceClientInterface,
        price_calculator: PriceCalculator,
    ) -> None:
        """Initialize use case.

        Args:
            stock_repository: Stock repository interface
            jquants_client: J-Quants client interface
            yfinance_client: yFinance client interface
            price_calculator: Price calculator service
        """
        self._stock_repository = stock_repository
        self._jquants_client = jquants_client
        self._yfinance_client = yfinance_client
        self._price_calculator = price_calculator

    async def execute(
        self,
        ticker_symbol_str: str,
        days: int = 100,
        source: str = "jquants",
    ) -> StockAnalysisDTO:
        """Execute stock analysis use case.

        Args:
            ticker_symbol_str: Ticker symbol string
            days: Number of days for historical data
            source: Data source ('jquants' or 'yfinance')

        Returns:
            Stock analysis DTO

        Raises:
            StockNotFoundError: If stock not found
            InsufficientDataError: If not enough data for analysis
        """
        # Validate and create ticker symbol
        ticker_symbol = TickerSymbol(ticker_symbol_str)
        
        # Get stock information
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
            
            # Save to repository
            stock = await self._stock_repository.save(stock)

        # Get historical price data
        period = TimePeriod.last_n_days(days)
        prices = await self._fetch_price_history(ticker_symbol, period, source)
        
        if len(prices) < 20:
            raise InsufficientDataError(
                required=20,
                available=len(prices),
                operation="stock analysis"
            )

        # Calculate technical indicators
        current_price = float(prices[-1].close) if prices else None
        
        try:
            sma_20 = float(self._price_calculator.calculate_sma(prices, 20))
        except InsufficientDataError:
            sma_20 = None
        
        try:
            sma_50 = float(self._price_calculator.calculate_sma(prices, 50))
        except InsufficientDataError:
            sma_50 = None
        
        try:
            ema_20 = float(self._price_calculator.calculate_ema(prices, 20))
        except InsufficientDataError:
            ema_20 = None
        
        try:
            rsi_14 = float(self._price_calculator.calculate_rsi(prices, 14))
        except InsufficientDataError:
            rsi_14 = None
        
        try:
            volatility_20 = float(self._price_calculator.calculate_volatility(prices, 20))
        except InsufficientDataError:
            volatility_20 = None

        # Identify support and resistance levels
        levels = self._price_calculator.identify_support_resistance(prices)
        support_levels = [float(level) for level in levels["support"]]
        resistance_levels = [float(level) for level in levels["resistance"]]

        # Generate recommendation
        recommendation = self._generate_recommendation(
            current_price=current_price,
            sma_20=sma_20,
            sma_50=sma_50,
            rsi_14=rsi_14,
        )

        return StockAnalysisDTO(
            stock=StockDTO.from_entity(stock),
            current_price=current_price,
            sma_20=sma_20,
            sma_50=sma_50,
            ema_20=ema_20,
            rsi_14=rsi_14,
            volatility_20=volatility_20,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            recommendation=recommendation,
        )

    async def _fetch_price_history(
        self,
        ticker_symbol: TickerSymbol,
        period: TimePeriod,
        source: str,
    ) -> List[Price]:
        """Fetch price history.

        Args:
            ticker_symbol: Ticker symbol
            period: Time period
            source: Data source

        Returns:
            List of price entities
        """
        if source == "jquants":
            return await self._jquants_client.get_stock_prices(ticker_symbol, period)
        else:
            return await self._yfinance_client.get_stock_prices(
                ticker_symbol, period, interval="1d"
            )

    def _generate_recommendation(
        self,
        current_price: Optional[float],
        sma_20: Optional[float],
        sma_50: Optional[float],
        rsi_14: Optional[float],
    ) -> str:
        """Generate investment recommendation based on technical indicators.

        Args:
            current_price: Current stock price
            sma_20: 20-day simple moving average
            sma_50: 50-day simple moving average
            rsi_14: 14-day RSI

        Returns:
            Recommendation string
        """
        if not current_price:
            return "Insufficient data for recommendation"

        signals = []
        
        # Moving average signals
        if sma_20 and sma_50:
            if sma_20 > sma_50:
                signals.append("bullish")
            else:
                signals.append("bearish")
        
        if sma_20:
            if current_price > sma_20:
                signals.append("bullish")
            else:
                signals.append("bearish")

        # RSI signals
        if rsi_14:
            if rsi_14 > 70:
                signals.append("overbought")
            elif rsi_14 < 30:
                signals.append("oversold")
            else:
                signals.append("neutral")

        # Count signals
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")
        
        if "overbought" in signals:
            return "SELL - Stock appears overbought"
        elif "oversold" in signals:
            return "BUY - Stock appears oversold"
        elif bullish_count > bearish_count:
            return "BUY - Bullish technical indicators"
        elif bearish_count > bullish_count:
            return "SELL - Bearish technical indicators"
        else:
            return "HOLD - Mixed signals"