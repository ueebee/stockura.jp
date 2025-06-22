import os
from typing import Optional
from pydantic import Field, validator

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定"""

    # アプリケーション設定
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"

    # サーバー設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # データベース設定
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/stockura"
    DATABASE_POOL_SIZE: int = Field(10, description="データベースコネクションプールサイズ")
    DATABASE_MAX_OVERFLOW: int = Field(20, description="データベースコネクションプール最大オーバーフロー")
    DATABASE_POOL_TIMEOUT: int = Field(30, description="データベースコネクションプールタイムアウト（秒）")
    DATABASE_POOL_RECYCLE: int = Field(3600, description="データベースコネクションリサイクル時間（秒）")
    DATABASE_ECHO: bool = Field(False, description="SQLクエリのエコー出力")

    # Redis設定
    REDIS_URL: str = "redis://localhost:6379/0"

    # API設定
    API_KEY_JQUANTS: Optional[str] = None

    # データソース認証情報（J-Quantsのみ）
    JQUANTS_MAILADDRESS: str = Field("system@stockura.jp", description="J-Quantsメールアドレス")
    JQUANTS_PASSWORD: str = Field("system_password_placeholder", description="J-Quantsパスワード")

    # 暗号化設定
    ENCRYPTION_KEY: str = Field(..., description="暗号化キー（必須）")
    ENCRYPTION_SALT: str = Field(..., description="暗号化ソルト（必須）")
    ENCRYPTION_ITERATIONS: int = Field(100000, description="PBKDF2イテレーション回数")
    ENCRYPTION_KEY_LENGTH: int = Field(32, description="暗号化キー長（バイト）")
    ENCRYPTION_ALGORITHM: str = Field("SHA256", description="ハッシュアルゴリズム")

    @validator('ENCRYPTION_KEY')
    def validate_encryption_key(cls, v):
        """暗号化キーの検証"""
        if len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters")
        return v

    @validator('ENCRYPTION_SALT')
    def validate_encryption_salt(cls, v):
        """暗号化ソルトの検証"""
        if len(v) < 16:
            raise ValueError("ENCRYPTION_SALT must be at least 16 characters")
        return v

    @validator('ENCRYPTION_ITERATIONS')
    def validate_encryption_iterations(cls, v):
        """イテレーション回数の検証"""
        if v < 100000:
            raise ValueError("ENCRYPTION_ITERATIONS must be at least 100000")
        return v

    @validator('ENCRYPTION_KEY_LENGTH')
    def validate_encryption_key_length(cls, v):
        """キー長の検証"""
        if v not in [16, 24, 32]:
            raise ValueError("ENCRYPTION_KEY_LENGTH must be 16, 24, or 32")
        return v

    @validator('DATABASE_POOL_SIZE')
    def validate_database_pool_size(cls, v):
        """データベースプールサイズの検証"""
        if v < 1 or v > 100:
            raise ValueError("DATABASE_POOL_SIZE must be between 1 and 100")
        return v

    @validator('DATABASE_MAX_OVERFLOW')
    def validate_database_max_overflow(cls, v):
        """データベース最大オーバーフローの検証"""
        if v < 0 or v > 100:
            raise ValueError("DATABASE_MAX_OVERFLOW must be between 0 and 100")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 