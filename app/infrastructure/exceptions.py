"""Infrastructure layer exceptions."""
from typing import Optional


class InfrastructureError(Exception):
    """Base exception for infrastructure layer errors.
    
    All infrastructure-specific exceptions should inherit from this class
    to maintain a clear exception hierarchy.
    """
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class DatabaseError(InfrastructureError):
    """Exception for database-related errors.
    
    Raised when database operations fail, including:
    - Connection errors
    - Query execution errors
    - Transaction failures
    """
    pass


class ExternalAPIError(InfrastructureError):
    """Exception for external API communication errors.
    
    Raised when external API calls fail, including:
    - Network errors
    - Authentication failures
    - Invalid responses
    """
    def __init__(self, message: str, status_code: Optional[int] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.status_code = status_code


class CacheError(InfrastructureError):
    """Exception for cache-related errors.
    
    Raised when cache operations fail, including:
    - Connection errors to cache server
    - Serialization/deserialization errors
    - Cache invalidation failures
    """
    pass


class ConfigurationError(InfrastructureError):
    """Exception for configuration-related errors.
    
    Raised when configuration is invalid or missing, including:
    - Missing required environment variables
    - Invalid configuration values
    - Configuration file parsing errors
    """
    pass