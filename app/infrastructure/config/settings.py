"""Infrastructure-specific settings."""
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database-specific configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
    )
    
    url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/stockura",
        description="Database connection URL"
    )
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    echo: bool = Field(default=False, description="Echo SQL statements")


class RedisSettings(BaseSettings):
    """Redis-specific configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False,
    )
    
    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    ttl: int = Field(default=3600, description="Default TTL in seconds")
    max_connections: int = Field(default=10, description="Max connections")
    decode_responses: bool = Field(default=True, description="Decode responses")


class CelerySettings(BaseSettings):
    """Celery-specific configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        case_sensitive=False,
    )
    
    broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend"
    )
    task_serializer: str = Field(default="json", description="Task serializer")
    result_serializer: str = Field(default="json", description="Result serializer")
    accept_content: list[str] = Field(default=["json"], description="Accept content types")
    timezone: str = Field(default="Asia/Tokyo", description="Timezone")
    enable_utc: bool = Field(default=True, description="Enable UTC")
    beat_schedule_filename: str = Field(
        default="celerybeat-schedule",
        description="Beat schedule filename"
    )
    beat_scheduler: str = Field(
        default="app.infrastructure.celery.schedulers.database_scheduler:DatabaseScheduler",
        description="Beat scheduler class"
    )
    beat_redis_sync_enabled: bool = Field(
        default=True,
        description="Enable Redis sync for Celery Beat"
    )


class JQuantsSettings(BaseSettings):
    """J-Quants API configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="JQUANTS_",
        case_sensitive=False,
    )
    
    api_key: Optional[str] = Field(default=None, description="J-Quants API key")
    mail_address: str = Field(default="", description="J-Quants mail address")
    password: str = Field(default="", description="J-Quants password")
    base_url: str = Field(
        default="https://api.jquants.com/v1",
        description="J-Quants API base URL"
    )
    timeout: int = Field(default=30, description="API timeout in seconds")
    max_retries: int = Field(default=3, description="Max retry attempts")


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration for external APIs."""
    
    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        case_sensitive=False,
    )
    
    # J-Quants rate limiting
    jquants_max_requests: int = Field(
        default=100,
        description="Maximum requests per window for J-Quants API",
        env="JQUANTS_RATE_LIMIT_REQUESTS"
    )
    jquants_window_seconds: int = Field(
        default=60,
        description="Time window in seconds for J-Quants rate limiting",
        env="JQUANTS_RATE_LIMIT_WINDOW"
    )
    
    # yfinance rate limiting
    yfinance_max_requests: int = Field(
        default=2000,
        description="Maximum requests per window for yfinance API",
        env="YFINANCE_RATE_LIMIT_REQUESTS"
    )
    yfinance_window_seconds: int = Field(
        default=3600,
        description="Time window in seconds for yfinance rate limiting",
        env="YFINANCE_RATE_LIMIT_WINDOW"
    )


class InfrastructureSettings(BaseSettings):
    """Combined infrastructure settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    jquants: JQuantsSettings = Field(default_factory=JQuantsSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    
    def __init__(self, **kwargs):
        """Initialize settings with environment variables."""
        super().__init__(**kwargs)
        # Load environment variables for nested settings
        import os
        
        # Database settings from core config environment variables
        if database_url := os.getenv("DATABASE_URL"):
            self.database.url = database_url
        if pool_size := os.getenv("DATABASE_POOL_SIZE"):
            self.database.pool_size = int(pool_size)
        if max_overflow := os.getenv("DATABASE_MAX_OVERFLOW"):
            self.database.max_overflow = int(max_overflow)
        if pool_timeout := os.getenv("DATABASE_POOL_TIMEOUT"):
            self.database.pool_timeout = int(pool_timeout)
        if echo := os.getenv("DATABASE_ECHO"):
            self.database.echo = echo.lower() == "true"
            
        # Redis settings
        if redis_url := os.getenv("REDIS_URL"):
            self.redis.url = redis_url
        if redis_ttl := os.getenv("REDIS_TTL"):
            self.redis.ttl = int(redis_ttl)
        if redis_max_connections := os.getenv("REDIS_MAX_CONNECTIONS"):
            self.redis.max_connections = int(redis_max_connections)
            
        # Celery settings
        if broker_url := os.getenv("CELERY_BROKER_URL"):
            self.celery.broker_url = broker_url
        if result_backend := os.getenv("CELERY_RESULT_BACKEND"):
            self.celery.result_backend = result_backend
            
        # Rate limit settings
        if jquants_max_requests := os.getenv("JQUANTS_RATE_LIMIT_REQUESTS"):
            self.rate_limit.jquants_max_requests = int(jquants_max_requests)
        if jquants_window := os.getenv("JQUANTS_RATE_LIMIT_WINDOW"):
            self.rate_limit.jquants_window_seconds = int(jquants_window)
        if yfinance_max_requests := os.getenv("YFINANCE_RATE_LIMIT_REQUESTS"):
            self.rate_limit.yfinance_max_requests = int(yfinance_max_requests)
        if yfinance_window := os.getenv("YFINANCE_RATE_LIMIT_WINDOW"):
            self.rate_limit.yfinance_window_seconds = int(yfinance_window)


_infrastructure_settings: Optional[InfrastructureSettings] = None


def get_infrastructure_settings() -> InfrastructureSettings:
    """Get infrastructure settings singleton."""
    global _infrastructure_settings
    if _infrastructure_settings is None:
        _infrastructure_settings = InfrastructureSettings()
    return _infrastructure_settings