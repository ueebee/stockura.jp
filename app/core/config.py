"""Application configuration module."""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application Settings
    app_name: str = Field(default="Stockura", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    api_title: str = Field(default="Stockura API", description="API title")
    api_description: str = Field(
        default="Stock Data Analysis Platform API", description="API description"
    )

    # Database Settings
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/stockura",
        description="Database connection URL",
    )
    database_pool_size: int = Field(default=10, description="Database pool size")
    database_max_overflow: int = Field(
        default=20, description="Database max overflow"
    )
    database_pool_timeout: int = Field(
        default=30, description="Database pool timeout"
    )
    database_echo: bool = Field(default=False, description="Database echo SQL")

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    redis_ttl: int = Field(default=3600, description="Redis default TTL")
    redis_max_connections: int = Field(
        default=10, description="Redis max connections"
    )

    # Celery Settings
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", description="Celery result backend"
    )
    celery_task_serializer: str = Field(
        default="json", description="Celery task serializer"
    )
    celery_result_serializer: str = Field(
        default="json", description="Celery result serializer"
    )
    celery_accept_content: List[str] = Field(
        default=["json"], description="Celery accept content"
    )
    celery_timezone: str = Field(
        default="Asia/Tokyo", description="Celery timezone"
    )
    celery_enable_utc: bool = Field(default=True, description="Celery enable UTC")

    # J-Quants API Settings
    jquants_api_key: str = Field(
        default="", description="J-Quants API key"
    )
    jquants_email: str = Field(
        default="", description="J-Quants API email"
    )
    jquants_password: str = Field(
        default="", description="J-Quants API password"
    )
    jquants_base_url: str = Field(
        default="https://api.jquants.com/v1", description="J-Quants base URL"
    )
    jquants_timeout: int = Field(default=30, description="J-Quants timeout")
    jquants_max_retries: int = Field(default=3, description="J-Quants max retries")

    # yFinance Settings
    yfinance_timeout: int = Field(default=30, description="yFinance timeout")
    yfinance_max_retries: int = Field(default=3, description="yFinance max retries")

    # Security Settings
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time"
    )

    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="CORS allow credentials"
    )
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="CORS allowed methods",
    )
    cors_allow_headers: List[str] = Field(
        default=["*"], description="CORS allowed headers"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60, description="Rate limit per minute"
    )
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour")

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    prometheus_port: int = Field(default=9090, description="Prometheus port")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create a global settings instance
settings = get_settings()