"""Logger モジュールのユニットテスト"""
import logging
import sys
from unittest.mock import MagicMock, patch
import pytest
import structlog

from app.core.logger import setup_logging, get_logger


class TestLogger:
    """Logger のテストクラス"""

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        # ロガーのハンドラをクリア
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    @patch('app.core.logger.settings')
    def test_setup_logging_debug_mode(self, mock_settings):
        """デバッグモードでのロギング設定テスト"""
        # Arrange
        mock_settings.log_level = "DEBUG"
        mock_settings.debug = True
        
        # Act
        setup_logging()
        
        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stdout
        # デバッグモードでは通常の Formatter を使用
        assert isinstance(handler.formatter, logging.Formatter)

    @patch('app.core.logger.settings')
    def test_setup_logging_production_mode(self, mock_settings):
        """本番モードでのロギング設定テスト"""
        # Arrange
        mock_settings.log_level = "INFO"
        mock_settings.debug = False
        
        # Act
        setup_logging()
        
        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        # 本番モードでは JSONFormatter を使用
        assert handler.formatter is not None

    @patch('app.core.logger.settings')
    def test_setup_logging_different_log_levels(self, mock_settings):
        """異なるログレベルでの設定テスト"""
        # Arrange & Act & Assert
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        expected_levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL
        ]
        
        for level_str, expected_level in zip(log_levels, expected_levels):
            mock_settings.log_level = level_str
            mock_settings.debug = True
            
            # 前のハンドラをクリア
            logging.getLogger().handlers.clear()
            
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == expected_level

    def test_get_logger_returns_structlog_logger(self):
        """get_logger が structlog ロガーを返すテスト"""
        # Act
        logger = get_logger("test_module")
        
        # Assert
        assert logger is not None
        # structlog のロガーは bind メソッドを持つ
        assert hasattr(logger, 'bind')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')

    def test_get_logger_with_context(self):
        """コンテキスト付きロガー取得のテスト"""
        # Act
        logger = get_logger("test_module")
        # structlog では bind メソッドでコンテキストを追加
        logger_with_context = logger.bind(user_id=123, request_id="abc")
        
        # Assert
        assert logger is not None
        assert logger_with_context is not None
        # structlog のロガーは bind メソッドを持つ
        assert hasattr(logger_with_context, 'bind')

    @patch('app.core.logger.structlog.configure')
    @patch('app.core.logger.settings')
    def test_setup_logging_configures_structlog(self, mock_settings, mock_configure):
        """structlog の設定が正しく行われるテスト"""
        # Arrange
        mock_settings.log_level = "INFO"
        mock_settings.debug = False
        
        # Act
        setup_logging()
        
        # Assert
        mock_configure.assert_called_once()
        # processors が設定されていることを確認
        call_args = mock_configure.call_args
        processors = call_args[1]['processors']
        assert len(processors) > 0

    @patch('app.core.logger.settings')
    def test_setup_logging_with_invalid_log_level(self, mock_settings):
        """無効なログレベルでのエラーハンドリングテスト"""
        # Arrange
        mock_settings.log_level = "INVALID_LEVEL"
        mock_settings.debug = True
        
        # Act & Assert
        with pytest.raises(AttributeError):
            setup_logging()

    def test_multiple_logger_instances(self):
        """複数のロガーインスタンスの独立性テスト"""
        # Act
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        logger3 = get_logger("module1")  # 同じ名前
        
        # Assert
        assert logger1 is not None
        assert logger2 is not None
        assert logger3 is not None
        # 同じ名前でも異なるインスタンス（structlog の仕様）
        assert logger1 is not logger3

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('app.core.logger.settings')
    def test_logging_output_to_stdout(self, mock_settings, mock_stdout):
        """ログが stdout に出力されることのテスト"""
        # Arrange
        mock_settings.log_level = "INFO"
        mock_settings.debug = True
        setup_logging()
        
        # Act
        logger = logging.getLogger("test")
        logger.info("Test message")
        
        # Assert
        # StreamHandler が stdout を使用していることを確認
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        assert handler.stream == sys.stdout


class TestLoggerAdapter:
    """LoggerAdapter のテストクラス"""

    def test_logger_adapter_initialization(self):
        """LoggerAdapter の初期化テスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        
        # Act
        adapter = LoggerAdapter(mock_logger)
        
        # Assert
        assert adapter.logger == mock_logger
        assert adapter._context == {}

    def test_logger_adapter_bind(self):
        """LoggerAdapter の bind メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        
        # Act
        result = adapter.bind(user_id=123, request_id="abc")
        
        # Assert
        assert adapter._context == {"user_id": 123, "request_id": "abc"}
        assert result == adapter  # チェイニング可能

    def test_logger_adapter_bind_multiple_times(self):
        """LoggerAdapter の複数回 bind テスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        
        # Act
        adapter.bind(user_id=123)
        adapter.bind(request_id="abc", session_id="xyz")
        
        # Assert
        assert adapter._context == {
            "user_id": 123,
            "request_id": "abc",
            "session_id": "xyz"
        }

    def test_logger_adapter_unbind(self):
        """LoggerAdapter の unbind メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        adapter._context = {"user_id": 123, "request_id": "abc", "session_id": "xyz"}
        
        # Act
        result = adapter.unbind("request_id", "session_id")
        
        # Assert
        assert adapter._context == {"user_id": 123}
        assert result == adapter  # チェイニング可能

    def test_logger_adapter_unbind_nonexistent_key(self):
        """存在しないキーの unbind テスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        adapter._context = {"user_id": 123}
        
        # Act
        adapter.unbind("nonexistent_key")
        
        # Assert
        assert adapter._context == {"user_id": 123}  # 変更なし

    def test_logger_adapter_debug(self):
        """LoggerAdapter の debug メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        adapter._context = {"user_id": 123}
        
        # Act
        adapter.debug("Debug message", extra_key="extra_value")
        
        # Assert
        mock_logger.debug.assert_called_once_with(
            "Debug message",
            user_id=123,
            extra_key="extra_value"
        )

    def test_logger_adapter_info(self):
        """LoggerAdapter の info メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        adapter._context = {"request_id": "abc"}
        
        # Act
        adapter.info("Info message", status_code=200)
        
        # Assert
        mock_logger.info.assert_called_once_with(
            "Info message",
            request_id="abc",
            status_code=200
        )

    def test_logger_adapter_warning(self):
        """LoggerAdapter の warning メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        
        # Act
        adapter.warning("Warning message")
        
        # Assert
        mock_logger.warning.assert_called_once_with("Warning message")

    def test_logger_adapter_error(self):
        """LoggerAdapter の error メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        adapter._context = {"user_id": 123}
        
        # Act
        adapter.error("Error message", error_code="E001")
        
        # Assert
        mock_logger.error.assert_called_once_with(
            "Error message",
            user_id=123,
            error_code="E001"
        )

    def test_logger_adapter_critical(self):
        """LoggerAdapter の critical メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        
        # Act
        adapter.critical("Critical message")
        
        # Assert
        mock_logger.critical.assert_called_once_with("Critical message")

    def test_logger_adapter_exception(self):
        """LoggerAdapter の exception メソッドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        
        # Act
        adapter.exception("Exception occurred", exc_info=True)
        
        # Assert
        mock_logger.exception.assert_called_once_with(
            "Exception occurred",
            exc_info=True
        )

    def test_logger_adapter_context_override(self):
        """コンテキストのオーバーライドテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        adapter._context = {"user_id": 123, "status": "active"}
        
        # Act
        adapter.info("Message", user_id=456, extra="data")
        
        # Assert
        # kwargs のコンテキストが優先される
        mock_logger.info.assert_called_once_with(
            "Message",
            user_id=456,  # 456 が優先される
            status="active",
            extra="data"
        )

    def test_logger_adapter_chaining(self):
        """メソッドチェイニングテスト"""
        # Arrange
        from app.core.logger import LoggerAdapter
        mock_logger = MagicMock()
        adapter = LoggerAdapter(mock_logger)
        
        # Act
        adapter.bind(user_id=123).bind(request_id="abc").unbind("user_id")
        
        # Assert
        assert adapter._context == {"request_id": "abc"}