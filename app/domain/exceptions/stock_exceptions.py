"""Domain exceptions for stock-related operations."""


class StockDomainError(Exception):
    """Base exception for stock domain errors."""

    pass


class StockNotFoundError(StockDomainError):
    """Exception raised when a stock is not found."""

    def __init__(self, ticker_symbol: str) -> None:
        """Initialize exception.

        Args:
            ticker_symbol: The ticker symbol that was not found
        """
        self.ticker_symbol = ticker_symbol
        super().__init__(f"Stock with ticker symbol '{ticker_symbol}' not found")


class InvalidTickerSymbolError(StockDomainError):
    """Exception raised when a ticker symbol is invalid."""

    def __init__(self, ticker_symbol: str, reason: str = "") -> None:
        """Initialize exception.

        Args:
            ticker_symbol: The invalid ticker symbol
            reason: Additional reason for invalidity
        """
        self.ticker_symbol = ticker_symbol
        message = f"Invalid ticker symbol: '{ticker_symbol}'"
        if reason:
            message += f". {reason}"
        super().__init__(message)


class InvalidPriceDataError(StockDomainError):
    """Exception raised when price data is invalid."""

    def __init__(self, message: str) -> None:
        """Initialize exception.

        Args:
            message: Error message
        """
        super().__init__(f"Invalid price data: {message}")


class InvalidTimePeriodError(StockDomainError):
    """Exception raised when a time period is invalid."""

    def __init__(self, message: str) -> None:
        """Initialize exception.

        Args:
            message: Error message
        """
        super().__init__(f"Invalid time period: {message}")


class MarketClosedError(StockDomainError):
    """Exception raised when attempting operations during market closure."""

    def __init__(self, market: str, message: str = "") -> None:
        """Initialize exception.

        Args:
            market: The market that is closed
            message: Additional message
        """
        self.market = market
        base_message = f"Market '{market}' is closed"
        if message:
            base_message += f". {message}"
        super().__init__(base_message)


class InsufficientDataError(StockDomainError):
    """Exception raised when there's insufficient data for an operation."""

    def __init__(self, required: int, available: int, operation: str) -> None:
        """Initialize exception.

        Args:
            required: Required data points
            available: Available data points
            operation: The operation being attempted
        """
        self.required = required
        self.available = available
        self.operation = operation
        super().__init__(
            f"Insufficient data for {operation}. "
            f"Required: {required}, Available: {available}"
        )


class DuplicateStockError(StockDomainError):
    """Exception raised when attempting to create a duplicate stock."""

    def __init__(self, ticker_symbol: str) -> None:
        """Initialize exception.

        Args:
            ticker_symbol: The duplicate ticker symbol
        """
        self.ticker_symbol = ticker_symbol
        super().__init__(f"Stock with ticker symbol '{ticker_symbol}' already exists")