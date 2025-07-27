"""
テスト環境設定

このモジュールはテスト実行時に使用する設定を定義します。
本番環境の設定を上書きし、テスト専用の設定を提供します。
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent.parent
TEST_ENV_FILE = PROJECT_ROOT / ".env.test"


class TestSettings(BaseSettings):
    """テスト環境専用の設定クラス"""

    model_config = SettingsConfigDict(
        env_file=str(TEST_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # Database
    database_url: str = "postgresql://test_user:test_pass@localhost:5432/stockura_test"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 0

    # Redis
    redis_url: str = "redis://localhost:6379/1"
    redis_prefix: str = "test:"
    redis_decode_responses: bool = True

    # J-Quants API
    jquants_api_base_url: str = "http://localhost:8001"
    jquants_email: str = "test@example.com"
    jquants_password: str = "test_password"

    # Application
    secret_key: str = "test_secret_key_for_testing_only"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Test Mode
    test_mode: bool = True
    env: str = "test"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/2"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = True

    # Rate Limiting
    rate_limit_enabled: bool = False

    # Test Specific
    test_db_schema: Optional[str] = None  # 並列実行時のスキーマ名
    test_redis_db: Optional[int] = None  # 並列実行時の Redis DB 番号

    @property
    def database_url_with_schema(self) -> str:
        """スキーマ付きのデータベース URL を返す"""
        if self.test_db_schema:
            # PostgreSQL のスキーマ指定
            return f"{self.database_url}?options=-csearch_path={self.test_db_schema}"
        return self.database_url

    @property
    def redis_url_with_db(self) -> str:
        """DB 番号付きの Redis URL を返す"""
        if self.test_redis_db is not None:
            # Redis URL の DB 番号を置換
            base_url = self.redis_url.rsplit("/", 1)[0]
            return f"{base_url}/{self.test_redis_db}"
        return self.redis_url


# シングルトンインスタンス
test_settings = TestSettings()


def get_test_database_url() -> str:
    """テスト用データベース URL を取得"""
    return test_settings.database_url_with_schema


def get_test_redis_url() -> str:
    """テスト用 Redis URL を取得"""
    return test_settings.redis_url_with_db


def override_app_settings():
    """アプリケーション設定をテスト用に上書き"""
    from app.core.config import settings

    # テスト設定で本番設定を上書き
    for key, value in test_settings.model_dump().items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    # 環境変数も上書き
    os.environ["TEST_MODE"] = "true"
    os.environ["ENV"] = "test"