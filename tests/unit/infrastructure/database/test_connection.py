"""Database connection モジュールのユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.infrastructure.database.connection import (
    get_engine,
    get_sessionmaker,
    get_session,
    create_tables,
    drop_tables,
    close_database,
    get_async_session_context,
    get_async_session_sync,
    Base
)


class TestDatabaseConnection:
    """Database connection のテストクラス"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        # グローバル変数をリセット
        import app.infrastructure.database.connection as conn_module
        conn_module._engine = None
        conn_module._sessionmaker = None

    @patch('app.infrastructure.database.connection.create_async_engine')
    @patch('app.infrastructure.database.connection.settings')
    def test_get_engine_creates_engine_once(self, mock_settings, mock_create_engine):
        """get_engine が一度だけエンジンを作成することのテスト"""
        # Arrange
        mock_settings.database_url = "postgresql+asyncpg://test:test@localhost/test"
        mock_settings.database_echo = False
        mock_settings.database_pool_size = 5
        mock_settings.database_max_overflow = 10
        mock_settings.database_pool_timeout = 30
        
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine
        
        # Act
        engine1 = get_engine()
        engine2 = get_engine()
        engine3 = get_engine()
        
        # Assert
        assert engine1 == mock_engine
        assert engine2 == mock_engine
        assert engine3 == mock_engine
        # エンジンは一度だけ作成される
        mock_create_engine.assert_called_once_with(
            "postgresql+asyncpg://test:test@localhost/test",
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True
        )

    @patch('app.infrastructure.database.connection.create_async_engine')
    @patch('app.infrastructure.database.connection.settings')
    def test_get_engine_with_debug_mode(self, mock_settings, mock_create_engine):
        """デバッグモードでのエンジン作成テスト"""
        # Arrange
        mock_settings.database_url = "postgresql+asyncpg://test:test@localhost/test"
        mock_settings.database_echo = True
        mock_settings.database_pool_size = 10
        mock_settings.database_max_overflow = 20
        mock_settings.database_pool_timeout = 60
        
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine
        
        # Act
        engine = get_engine()
        
        # Assert
        assert engine == mock_engine
        mock_create_engine.assert_called_once_with(
            "postgresql+asyncpg://test:test@localhost/test",
            echo=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
            pool_pre_ping=True
        )

    @patch('app.infrastructure.database.connection.get_engine')
    @patch('app.infrastructure.database.connection.async_sessionmaker')
    def test_get_sessionmaker_creates_sessionmaker_once(self, mock_async_sessionmaker, mock_get_engine):
        """get_sessionmaker が一度だけセッションメーカーを作成することのテスト"""
        # Arrange
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_get_engine.return_value = mock_engine
        
        mock_sessionmaker_instance = MagicMock(spec=async_sessionmaker)
        mock_async_sessionmaker.return_value = mock_sessionmaker_instance
        
        # Act
        sessionmaker1 = get_sessionmaker()
        sessionmaker2 = get_sessionmaker()
        sessionmaker3 = get_sessionmaker()
        
        # Assert
        assert sessionmaker1 == mock_sessionmaker_instance
        assert sessionmaker2 == mock_sessionmaker_instance
        assert sessionmaker3 == mock_sessionmaker_instance
        # セッションメーカーは一度だけ作成される
        mock_async_sessionmaker.assert_called_once_with(
            mock_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.get_sessionmaker')
    async def test_get_session_success(self, mock_get_sessionmaker):
        """get_session の正常系テスト"""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker_instance = AsyncMock()
        mock_sessionmaker_instance.__aenter__.return_value = mock_session
        mock_sessionmaker_instance.__aexit__.return_value = None
        mock_get_sessionmaker.return_value = lambda: mock_sessionmaker_instance
        
        # Act
        async for session in get_session():
            assert session == mock_session
        
        # Assert
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.get_sessionmaker')
    async def test_get_session_with_exception(self, mock_get_sessionmaker):
        """get_session の例外発生時のテスト"""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        # commit 時に例外を発生させる
        mock_session.commit.side_effect = ValueError("Test error during commit")
        
        mock_sessionmaker_instance = AsyncMock()
        mock_sessionmaker_instance.__aenter__.return_value = mock_session
        mock_sessionmaker_instance.__aexit__.return_value = None
        mock_get_sessionmaker.return_value = lambda: mock_sessionmaker_instance
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            async for session in get_session():
                # 正常に session を yield するが、その後の commit で例外が発生
                pass
        
        # Assert
        assert "Test error during commit" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.get_engine')
    async def test_create_tables(self, mock_get_engine):
        """create_tables のテスト"""
        # Arrange
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine
        
        # Act
        await create_tables()
        
        # Assert
        mock_conn.run_sync.assert_called_once()
        # run_sync に渡された関数を確認
        call_args = mock_conn.run_sync.call_args
        assert call_args[0][0] == Base.metadata.create_all

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.get_engine')
    async def test_drop_tables(self, mock_get_engine):
        """drop_tables のテスト"""
        # Arrange
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine
        
        # Act
        await drop_tables()
        
        # Assert
        mock_conn.run_sync.assert_called_once()
        # run_sync に渡された関数を確認
        call_args = mock_conn.run_sync.call_args
        assert call_args[0][0] == Base.metadata.drop_all

    @pytest.mark.asyncio
    async def test_close_database_with_engine(self):
        """エンジンが存在する場合の close_database のテスト"""
        # Arrange
        import app.infrastructure.database.connection as conn_module
        mock_engine = AsyncMock(spec=AsyncEngine)
        conn_module._engine = mock_engine
        
        # Act
        await close_database()
        
        # Assert
        mock_engine.dispose.assert_called_once()
        assert conn_module._engine is None

    @pytest.mark.asyncio
    async def test_close_database_without_engine(self):
        """エンジンが存在しない場合の close_database のテスト"""
        # Arrange
        import app.infrastructure.database.connection as conn_module
        conn_module._engine = None
        
        # Act
        await close_database()  # エラーが発生しないことを確認
        
        # Assert
        assert conn_module._engine is None

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.get_sessionmaker')
    async def test_get_async_session_context_success(self, mock_get_sessionmaker):
        """get_async_session_context の正常系テスト"""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker_instance = AsyncMock()
        mock_sessionmaker_instance.__aenter__.return_value = mock_session
        mock_sessionmaker_instance.__aexit__.return_value = None
        mock_get_sessionmaker.return_value = lambda: mock_sessionmaker_instance
        
        # Act
        async with get_async_session_context() as session:
            assert session == mock_session
        
        # Assert
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.get_sessionmaker')
    async def test_get_async_session_context_with_exception(self, mock_get_sessionmaker):
        """get_async_session_context の例外発生時のテスト"""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker_instance = AsyncMock()
        mock_sessionmaker_instance.__aenter__.return_value = mock_session
        mock_sessionmaker_instance.__aexit__.return_value = None
        mock_get_sessionmaker.return_value = lambda: mock_sessionmaker_instance
        
        # Act & Assert
        with pytest.raises(RuntimeError):
            async with get_async_session_context() as session:
                raise RuntimeError("Test error")
        
        # ロールバックされることを確認
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_get_async_session_sync(self):
        """get_async_session_sync のテスト"""
        # Act
        result = get_async_session_sync()
        
        # Assert
        # コンテキストマネージャーが返されることを確認
        assert hasattr(result, '__aenter__')
        assert hasattr(result, '__aexit__')

    def test_base_declarative(self):
        """Base declarative のテスト"""
        # Assert
        assert hasattr(Base, 'metadata')
        assert hasattr(Base, 'registry')

    @patch('app.infrastructure.database.connection.logger')
    @patch('app.infrastructure.database.connection.create_async_engine')
    @patch('app.infrastructure.database.connection.settings')
    def test_get_engine_logs_creation(self, mock_settings, mock_create_engine, mock_logger):
        """エンジン作成時のログ出力テスト"""
        # Arrange
        mock_settings.database_url = "postgresql+asyncpg://test:test@localhost/test"
        mock_settings.database_echo = False
        mock_settings.database_pool_size = 5
        mock_settings.database_max_overflow = 10
        mock_settings.database_pool_timeout = 30
        
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine
        
        # Act
        get_engine()
        
        # Assert
        mock_logger.info.assert_called_once_with("Database engine created")

    @patch('app.infrastructure.database.connection.logger')
    @patch('app.infrastructure.database.connection.get_engine')
    @patch('app.infrastructure.database.connection.async_sessionmaker')
    def test_get_sessionmaker_logs_creation(self, mock_async_sessionmaker, mock_get_engine, mock_logger):
        """セッションメーカー作成時のログ出力テスト"""
        # Arrange
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_get_engine.return_value = mock_engine
        
        mock_sessionmaker_instance = MagicMock(spec=async_sessionmaker)
        mock_async_sessionmaker.return_value = mock_sessionmaker_instance
        
        # Act
        get_sessionmaker()
        
        # Assert
        mock_logger.info.assert_called_once_with("Session maker created")

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.logger')
    async def test_close_database_logs_closure(self, mock_logger):
        """データベース接続クローズ時のログ出力テスト"""
        # Arrange
        import app.infrastructure.database.connection as conn_module
        mock_engine = AsyncMock(spec=AsyncEngine)
        conn_module._engine = mock_engine
        
        # Act
        await close_database()
        
        # Assert
        mock_logger.info.assert_called_once_with("Database connections closed")