"""Base client for yfinance data source.

This module provides the base client for interacting with yfinance library.
Unlike J-Quants which requires API authentication, yfinance doesn't require
any authentication and directly fetches data from Yahoo Finance.
"""
from typing import Optional, Any, Dict
import yfinance as yf
from app.core.logger import get_logger
from app.infrastructure.config.settings import get_infrastructure_settings
from app.infrastructure.rate_limiter import RateLimiter, with_rate_limit

logger = get_logger(__name__)


class YfinanceBaseClient:
    """Base client for yfinance operations.
    
    This client provides basic functionality for fetching stock data
    using the yfinance library. It handles common operations like
    error handling and logging.
    """
    
    def __init__(self) -> None:
        """Initialize yfinance base client.
        
        Note: yfinance doesn't require authentication.
        """
        logger.info("Initializing yfinance base client")
        
        # レートリミッターの初期化
        settings = get_infrastructure_settings()
        self._rate_limiter = RateLimiter(
            max_requests=settings.rate_limit.yfinance_max_requests,
            window_seconds=settings.rate_limit.yfinance_window_seconds,
            name="yfinance API"
        )
    
    async def __aenter__(self) -> "YfinanceBaseClient":
        """Async context manager entry.
        
        Note: yfinance doesn't maintain persistent connections,
        so this is mainly for API consistency.
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit.
        
        Note: No cleanup required for yfinance.
        """
        pass
    
    @with_rate_limit(lambda self: self._rate_limiter)
    def get_ticker(self, symbol: str) -> yf.Ticker:
        """Get a ticker object for the given symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            
        Returns:
            yfinance Ticker object
        """
        logger.debug(f"Creating ticker object for symbol: {symbol}")
        return yf.Ticker(symbol)
    
    @with_rate_limit(lambda self: self._rate_limiter)
    def download_data(
        self,
        tickers: str | list[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d",
        **kwargs
    ) -> Any:
        """Download historical market data.
        
        Args:
            tickers: Single ticker or list of tickers
            start: Start date (YYYY-MM-DD format)
            end: End date (YYYY-MM-DD format)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            **kwargs: Additional arguments passed to yf.download
            
        Returns:
            Downloaded data (DataFrame or dict of DataFrames)
        """
        logger.info(f"Downloading data for tickers: {tickers}")
        try:
            data = yf.download(
                tickers=tickers,
                start=start,
                end=end,
                interval=interval,
                **kwargs
            )
            logger.info(f"Successfully downloaded data for {tickers}")
            return data
        except Exception as e:
            logger.error(f"Failed to download data: {str(e)}")
            raise