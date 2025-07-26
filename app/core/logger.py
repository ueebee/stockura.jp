"""Logging configuration module."""
import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    # Configure standard logging
    log_level = getattr(logging, settings.log_level.upper())
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use JSON formatter for production, simple format for development
    if settings.debug:
        formatter = logging.Formatter(
            "%(asctime) s - %(name) s - %(levelname) s - %(message) s"
        )
    else:
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp) s %(level) s %(name) s %(message) s",
            timestamp=True,
        )
    
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [console_handler]
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


class LoggerAdapter:
    """Logger adapter for adding context to log messages."""
    
    def __init__(self, logger: structlog.BoundLogger):
        """Initialize logger adapter.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
        self._context: Dict[str, Any] = {}
    
    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """Bind context data to logger.
        
        Args:
            **kwargs: Context key-value pairs
            
        Returns:
            Self for chaining
        """
        self._context.update(kwargs)
        return self
    
    def unbind(self, *keys: str) -> "LoggerAdapter":
        """Remove context data from logger.
        
        Args:
            *keys: Context keys to remove
            
        Returns:
            Self for chaining
        """
        for key in keys:
            self._context.pop(key, None)
        return self
    
    def _log(self, method: str, msg: str, **kwargs: Any) -> None:
        """Internal log method.
        
        Args:
            method: Log method name
            msg: Log message
            **kwargs: Additional context
        """
        context = {**self._context, **kwargs}
        getattr(self.logger, method)(msg, **context)
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("debug", msg, **kwargs)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("info", msg, **kwargs)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("warning", msg, **kwargs)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("error", msg, **kwargs)
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log("critical", msg, **kwargs)
    
    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._log("exception", msg, **kwargs)


# Initialize logging on module import
setup_logging()

# Create default logger
logger = get_logger(__name__)