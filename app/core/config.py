import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # アプリケーション設定
    APP_NAME: str = "Stockura"
    DEBUG: bool = False
    
    # データベース設定
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/stockura"
    
    # Celery設定
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # API設定
    JQUANTS_API_KEY: Optional[str] = None
    JQUANTS_REFRESH_TOKEN: Optional[str] = None
    
    # レート制限設定
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100
    
    class Config:
        env_file = ".env"

# 設定インスタンスの作成
settings = Settings()
