"""Application constants."""
from enum import Enum


class Environment(str, Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Market(str, Enum):
    """Stock market types."""

    TSE = "TSE"  # Tokyo Stock Exchange
    NYSE = "NYSE"  # New York Stock Exchange
    NASDAQ = "NASDAQ"  # NASDAQ
    OTHER = "OTHER"


class OrderType(str, Enum):
    """Order types."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


class TimeFrame(str, Enum):
    """Time frame for stock data."""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class CacheKeyPrefix(str, Enum):
    """Cache key prefixes."""

    STOCK_PRICE = "stock:price"
    STOCK_INFO = "stock:info"
    MARKET_DATA = "market:data"
    USER_SESSION = "user:session"
    API_RATE_LIMIT = "api:rate_limit"


# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503

# Default Values
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_CACHE_TTL = 3600  # 1 hour
DEFAULT_TIMEOUT = 30  # seconds

# Date Formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Regular Expressions
TICKER_SYMBOL_REGEX = r"^[A-Z0-9]{1,10}$"
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# Error Messages
ERROR_STOCK_NOT_FOUND = "Stock not found"
ERROR_INVALID_TICKER = "Invalid ticker symbol"
ERROR_INVALID_DATE_RANGE = "Invalid date range"
ERROR_UNAUTHORIZED = "Unauthorized access"
ERROR_RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
ERROR_EXTERNAL_API_ERROR = "External API error"
ERROR_DATABASE_ERROR = "Database error"
ERROR_VALIDATION_ERROR = "Validation error"

# Success Messages
SUCCESS_CREATED = "Resource created successfully"
SUCCESS_UPDATED = "Resource updated successfully"
SUCCESS_DELETED = "Resource deleted successfully"

# J-Quants Specific
JQUANTS_MARKETS = ["TSE", "OSE", "NSE", "FSE", "SSE"]
JQUANTS_MAX_DATE_RANGE_DAYS = 365

# yFinance Specific
YFINANCE_INTERVALS = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
YFINANCE_PERIODS = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]