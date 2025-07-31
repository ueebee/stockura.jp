"""Config モジュールのユニットテスト"""
import os
from unittest.mock import patch
import pytest

from app.core.config import Settings, get_settings


class TestSettings:
    """Settings クラスのテストクラス"""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_settings(self):
        """デフォルト設定の確認テスト"""
        # Act
        settings = Settings()
        
        # Assert - Application Settings
        assert settings.app_name == "Stockura"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        
        # Assert - API Settings
        assert settings.api_v1_prefix == "/api/v1"
        assert settings.api_title == "Stockura API"
        assert settings.api_description == "Stock Data Analysis Platform API"
        
        # Assert - Database Settings
        assert settings.database_url == "postgresql+asyncpg://user:password@localhost:5432/stockura"
        assert settings.database_pool_size == 10
        assert settings.database_max_overflow == 20
        assert settings.database_pool_timeout == 30
        assert settings.database_echo is False

    @patch.dict(os.environ, {}, clear=True)
    def test_redis_settings_defaults(self):
        """Redis 設定のデフォルト値テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.redis_ttl == 3600
        assert settings.redis_max_connections == 10

    @patch.dict(os.environ, {}, clear=True)
    def test_celery_settings_defaults(self):
        """Celery 設定のデフォルト値テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.celery_broker_url == "redis://localhost:6379/1"
        assert settings.celery_result_backend == "redis://localhost:6379/2"
        assert settings.celery_task_serializer == "json"
        assert settings.celery_result_serializer == "json"
        assert settings.celery_accept_content == ["json"]
        assert settings.celery_timezone == "Asia/Tokyo"
        assert settings.celery_enable_utc is True

    def test_jquants_settings_defaults(self):
        """J-Quants 設定のデフォルト値テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.jquants_api_key == ""
        assert settings.jquants_email == ""
        assert settings.jquants_password == ""
        assert settings.jquants_base_url == "https://api.jquants.com/v1"
        assert settings.jquants_timeout == 30
        assert settings.jquants_max_retries == 3

    def test_security_settings_defaults(self):
        """セキュリティ設定のデフォルト値テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.secret_key == "your-secret-key-here-change-in-production"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30

    def test_cors_settings_defaults(self):
        """CORS 設定のデフォルト値テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:8000"]
        assert settings.cors_allow_credentials is True
        assert settings.cors_allow_methods == ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        assert settings.cors_allow_headers == ["*"]

    def test_rate_limiting_settings(self):
        """レート制限設定のテスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.rate_limit_per_minute == 60
        assert settings.rate_limit_per_hour == 1000

    def test_monitoring_settings(self):
        """モニタリング設定のテスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.sentry_dsn is None
        assert settings.prometheus_port == 9090

    def test_log_level_validator_valid(self):
        """有効なログレベルのバリデーションテスト"""
        # Arrange & Act
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "debug", "info", "warning", "error", "critical"]
        
        for level in valid_levels:
            settings = Settings(log_level=level)
            # Assert - すべて大文字に変換される
            assert settings.log_level == level.upper()

    def test_log_level_validator_invalid(self):
        """無効なログレベルのバリデーションテスト"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Settings(log_level="INVALID")
        
        assert "Log level must be one of" in str(exc_info.value)

    def test_cors_origins_from_string(self):
        """文字列からの CORS origins 変換テスト"""
        # Act
        settings = Settings(cors_origins="http://example.com, https://api.example.com")
        
        # Assert
        assert settings.cors_origins == ["http://example.com", "https://api.example.com"]

    def test_cors_origins_from_list(self):
        """リストからの CORS origins 設定テスト"""
        # Act
        origins = ["http://example.com", "https://api.example.com"]
        settings = Settings(cors_origins=origins)
        
        # Assert
        assert settings.cors_origins == origins

    def test_cors_origins_with_spaces(self):
        """スペース付き CORS origins 変換テスト"""
        # Act
        settings = Settings(cors_origins=" http://example.com , https://api.example.com ")
        
        # Assert
        assert settings.cors_origins == ["http://example.com", "https://api.example.com"]

    def test_celery_accept_content_from_string(self):
        """文字列からの Celery accept content 変換テスト"""
        # Act
        settings = Settings(celery_accept_content="json, msgpack, yaml")
        
        # Assert
        assert settings.celery_accept_content == ["json", "msgpack", "yaml"]

    def test_celery_accept_content_from_json_string(self):
        """JSON 文字列からの Celery accept content 変換テスト"""
        # Act
        settings = Settings(celery_accept_content='["json", "msgpack"]')
        
        # Assert
        assert settings.celery_accept_content == ["json", "msgpack"]

    def test_celery_accept_content_from_invalid_json_string(self):
        """無効な JSON 文字列からの Celery accept content 変換テスト"""
        # Act
        settings = Settings(celery_accept_content='["json", invalid]')
        
        # Assert - JSON 解析に失敗した場合はカンマ区切りとして処理
        assert settings.celery_accept_content == ['["json"', 'invalid]']

    def test_celery_accept_content_from_list(self):
        """リストからの Celery accept content 設定テスト"""
        # Act
        content_types = ["json", "msgpack"]
        settings = Settings(celery_accept_content=content_types)
        
        # Assert
        assert settings.celery_accept_content == content_types

    def test_settings_with_env_vars(self):
        """環境変数からの設定読み込みテスト"""
        # Arrange
        env_vars = {
            "APP_NAME": "TestApp",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "DATABASE_URL": "postgresql+asyncpg://test:test@db:5432/test",
            "REDIS_URL": "redis://redis:6379/0",
            "JQUANTS_API_KEY": "test-api-key"
        }
        
        # Act
        with patch.dict(os.environ, env_vars):
            settings = Settings()
        
        # Assert
        assert settings.app_name == "TestApp"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.database_url == "postgresql+asyncpg://test:test@db:5432/test"
        assert settings.redis_url == "redis://redis:6379/0"
        assert settings.jquants_api_key == "test-api-key"

    @patch.dict(os.environ, {"APP_NAME": "TestApp", "APP_VERSION": "1.0.0"}, clear=True)
    def test_settings_case_insensitive(self):
        """設定名の大文字小文字無視テスト"""
        # Act - 環境変数が大文字でも読み込まれることを確認
        settings = Settings()
        
        # Assert
        assert settings.app_name == "TestApp"
        assert settings.app_version == "1.0.0"

    def test_settings_ignore_extra_fields(self):
        """余分なフィールドの無視テスト"""
        # Act - 余分なフィールドがあってもエラーにならない
        settings = Settings(unknown_field="value", another_unknown="value2")
        
        # Assert
        assert hasattr(settings, "app_name")
        assert not hasattr(settings, "unknown_field")
        assert not hasattr(settings, "another_unknown")

    def test_numeric_settings_types(self):
        """数値設定の型確認テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert isinstance(settings.database_pool_size, int)
        assert isinstance(settings.database_max_overflow, int)
        assert isinstance(settings.database_pool_timeout, int)
        assert isinstance(settings.redis_ttl, int)
        assert isinstance(settings.redis_max_connections, int)
        assert isinstance(settings.jquants_timeout, int)
        assert isinstance(settings.jquants_max_retries, int)
        assert isinstance(settings.access_token_expire_minutes, int)
        assert isinstance(settings.rate_limit_per_minute, int)
        assert isinstance(settings.rate_limit_per_hour, int)
        assert isinstance(settings.prometheus_port, int)

    def test_boolean_settings_types(self):
        """ブール設定の型確認テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.database_echo, bool)
        assert isinstance(settings.celery_enable_utc, bool)
        assert isinstance(settings.cors_allow_credentials, bool)

    def test_list_settings_types(self):
        """リスト設定の型確認テスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert isinstance(settings.celery_accept_content, list)
        assert isinstance(settings.cors_origins, list)
        assert isinstance(settings.cors_allow_methods, list)
        assert isinstance(settings.cors_allow_headers, list)

    def test_optional_settings(self):
        """オプショナル設定のテスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.sentry_dsn is None
        
        # With value
        settings_with_sentry = Settings(sentry_dsn="https://example.com/sentry")
        assert settings_with_sentry.sentry_dsn == "https://example.com/sentry"


class TestGetSettings:
    """get_settings 関数のテストクラス"""

    def test_get_settings_returns_settings_instance(self):
        """get_settings が Settings インスタンスを返すテスト"""
        # Act
        settings = get_settings()
        
        # Assert
        assert isinstance(settings, Settings)

    @patch("app.core.config.get_settings")
    def test_get_settings_caching(self, mock_get_settings):
        """get_settings のキャッシング動作テスト"""
        # Arrange
        from app.core.config import get_settings
        
        # Clear cache first
        get_settings.cache_clear()
        
        mock_settings = Settings()
        mock_get_settings.return_value = mock_settings
        
        # Act - 複数回呼び出し
        settings1 = get_settings()
        settings2 = get_settings()
        settings3 = get_settings()
        
        # Assert - 一度だけ呼ばれる（キャッシュが効いている）
        assert mock_get_settings.call_count == 3  # パッチされたものが呼ばれる
        assert settings1 == mock_settings
        assert settings2 == mock_settings
        assert settings3 == mock_settings

    def test_settings_singleton_pattern(self):
        """settings グローバル変数のシングルトンパターンテスト"""
        # Arrange
        from app.core.config import settings, get_settings
        
        # Act
        settings_from_function = get_settings()
        
        # Assert
        assert settings is settings_from_function

    def test_settings_field_descriptions(self):
        """設定フィールドの説明文テスト"""
        # Act
        settings = Settings()
        
        # Assert - いくつかのフィールドの説明文を確認
        field_info = settings.model_fields
        assert field_info["app_name"].description == "Application name"
        assert field_info["debug"].description == "Debug mode"
        assert field_info["log_level"].description == "Logging level"
        assert field_info["database_url"].description == "Database connection URL"
        assert field_info["redis_url"].description == "Redis connection URL"
        assert field_info["secret_key"].description == "Secret key for JWT"

    def test_env_file_configuration(self):
        """環境ファイル設定のテスト"""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.model_config["env_file"] == ".env"
        assert settings.model_config["env_file_encoding"] == "utf-8"
        assert settings.model_config["case_sensitive"] is False
        assert settings.model_config["extra"] == "ignore"