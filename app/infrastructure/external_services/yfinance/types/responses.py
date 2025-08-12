"""Response type definitions for yfinance data.

This module defines the structure of data returned by yfinance API.
These types help ensure type safety when working with yfinance data.
"""
from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime


class YfinanceStockInfo(TypedDict):
    """Basic stock information from yfinance."""
    
    symbol: str
    shortName: Optional[str]
    longName: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    marketCap: Optional[int]
    enterpriseValue: Optional[int]
    currency: Optional[str]
    exchange: Optional[str]
    quoteType: Optional[str]
    market: Optional[str]
    country: Optional[str]
    website: Optional[str]
    description: Optional[str]
    employees: Optional[int]
    
    # Price information
    regularMarketPrice: Optional[float]
    regularMarketPreviousClose: Optional[float]
    regularMarketOpen: Optional[float]
    regularMarketDayLow: Optional[float]
    regularMarketDayHigh: Optional[float]
    regularMarketVolume: Optional[int]
    
    # Valuation metrics
    trailingPE: Optional[float]
    forwardPE: Optional[float]
    priceToBook: Optional[float]
    enterpriseToRevenue: Optional[float]
    enterpriseToEbitda: Optional[float]
    
    # Additional info
    fiftyTwoWeekLow: Optional[float]
    fiftyTwoWeekHigh: Optional[float]
    dividendRate: Optional[float]
    dividendYield: Optional[float]
    beta: Optional[float]


class YfinanceHistoricalData(TypedDict):
    """Historical price data structure."""
    
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    dividends: Optional[float]
    stock_splits: Optional[float]


class YfinanceFinancialStatement(TypedDict):
    """Financial statement data structure."""
    
    # This is a simplified version. Actual financial statements
    # contain many more fields depending on the company and data availability
    date: datetime
    total_revenue: Optional[float]
    gross_profit: Optional[float]
    operating_income: Optional[float]
    net_income: Optional[float]
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    total_equity: Optional[float]
    operating_cash_flow: Optional[float]
    free_cash_flow: Optional[float]


class YfinanceSearchResult(TypedDict):
    """Search result structure."""
    
    symbol: str
    name: str
    exchange: str
    type: str  # EQUITY, ETF, MUTUAL_FUND, etc.
    region: str


# Type alias for the full info dictionary returned by yfinance
# The actual structure is very large and varies by security type
YfinanceFullInfo = Dict[str, Any]