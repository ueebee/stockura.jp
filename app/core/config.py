import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # アプリケーション設定
    APP_NAME: str = "Stockura"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "default-secret-key-change-in-production"
    
    # サーバー設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # データベース設定
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/stockura"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False
    
    # Celery設定
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # Redis設定
    REDIS_URL: str = "redis://redis:6379/0"
    
    # API設定
    JQUANTS_API_KEY: Optional[str] = None
    JQUANTS_REFRESH_TOKEN: Optional[str] = None
    JQUANTS_MAILADDRESS: Optional[str] = None
    JQUANTS_PASSWORD: Optional[str] = None
    
    # 暗号化設定
    ENCRYPTION_KEY: str = "default-encryption-key-change-in-production"
    ENCRYPTION_SALT: str = "default-salt-change-in-production"
    ENCRYPTION_ITERATIONS: int = 100000
    ENCRYPTION_KEY_LENGTH: int = 32
    ENCRYPTION_ALGORITHM: str = "SHA256"
    
    # レート制限設定
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

# 設定インスタンスの作成
settings = Settings()
