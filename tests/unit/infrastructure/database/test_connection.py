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
        conn_module._engines = {}
        conn_module._sessionmakers = {}

    @patch('app.infrastructure.database.connection.create_async_engine')
    @patch('app.infrastructure.database.connection.get_infrastructure_settings')
    @patch('app.infrastructure.database.connection.asyncio.get_running_loop')
    def test_get_engine_creates_engine_once(self, mock_get_loop, mock_get_settings, mock_create_engine):
        """get_engine が一度だけエンジンを作成することのテスト"""
        # Arrange
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        
        mock_infra_settings = MagicMock()
        mock_infra_settings.database.url = "postgresql+asyncpg://test:test@localhost/test"
        mock_infra_settings.database.echo = False
        mock_infra_settings.database.pool_size = 5
        mock_infra_settings.database.max_overflow = 10
        mock_infra_settings.database.pool_timeout = 30
        mock_get_settings.return_value = mock_infra_settings
        
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
    @patch('app.infrastructure.database.connection.get_infrastructure_settings')
    @patch('app.infrastructure.database.connection.asyncio.get_running_loop')
    def test_get_engine_with_debug_mode(self, mock_get_loop, mock_get_settings, mock_create_engine):
        """デバッグモードでのエンジン作成テスト"""
        # Arrange
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        
        mock_infra_settings = MagicMock()
        mock_infra_settings.database.url = "postgresql+asyncpg://test:test@localhost/test"
        mock_infra_settings.database.echo = True
        mock_infra_settings.database.pool_size = 10
        mock_infra_settings.database.max_overflow = 20
        mock_infra_settings.database.pool_timeout = 60
        mock_get_settings.return_value = mock_infra_settings
        
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
    @patch('app.infrastructure.database.connection.asyncio.get_running_loop')
    def test_get_sessionmaker_creates_sessionmaker_once(self, mock_get_loop, mock_async_sessionmaker, mock_get_engine):
        """get_sessionmaker が一度だけセッションメーカーを作成することのテスト"""
        # Arrange
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        
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
    async def test_get_session_success(self):
        """get_session が正常にセッションを返すテスト"""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker = MagicMock()
        mock_sessionmaker.return_value.__aenter__.return_value = mock_session
        
        with patch('app.infrastructure.database.connection.get_sessionmaker', return_value=mock_sessionmaker):
            # Act
            async for session in get_session():
                # Assert
                assert session == mock_session
                
        # セッションのコミットとクローズが呼ばれている
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_error(self):
        """エラー時にロールバックされることのテスト"""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = Exception("Database error")
        mock_sessionmaker = MagicMock()
        mock_sessionmaker.return_value.__aenter__.return_value = mock_session
        
        with patch('app.infrastructure.database.connection.get_sessionmaker', return_value=mock_sessionmaker):
            # Act & Assert
            with pytest.raises(Exception, match="Database error"):
                async for session in get_session():
                    assert session == mock_session
        
        # ロールバックが呼ばれている
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tables(self):
        """create_tables のテスト"""
        # Arrange
        mock_conn = AsyncMock()
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        
        with patch('app.infrastructure.database.connection.get_engine', return_value=mock_engine):
            # Act
            await create_tables()
            
        # Assert
        mock_conn.run_sync.assert_called_once()
        # run_sync に渡される関数を確認
        args = mock_conn.run_sync.call_args[0]
        assert args[0] == Base.metadata.create_all

    @pytest.mark.asyncio
    async def test_drop_tables(self):
        """drop_tables のテスト"""
        # Arrange
        mock_conn = AsyncMock()
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        
        with patch('app.infrastructure.database.connection.get_engine', return_value=mock_engine):
            # Act
            await drop_tables()
            
        # Assert
        mock_conn.run_sync.assert_called_once()
        # run_sync に渡される関数を確認
        args = mock_conn.run_sync.call_args[0]
        assert args[0] == Base.metadata.drop_all

    @pytest.mark.asyncio
    async def test_close_database_with_engine(self):
        """close_database がエンジンを正しく破棄することのテスト"""
        # Arrange
        import app.infrastructure.database.connection as conn_module
        
        mock_loop = MagicMock()
        mock_engine = AsyncMock(spec=AsyncEngine)
        conn_module._engines = {mock_loop: mock_engine}
        conn_module._sessionmakers = {mock_loop: MagicMock()}
        
        # Act
        await close_database()
        
        # Assert
        mock_engine.dispose.assert_called_once()
        assert len(conn_module._engines) == 0
        assert len(conn_module._sessionmakers) == 0

    @pytest.mark.asyncio
    async def test_close_database_without_engine(self):
        """エンジンがない場合の close_database のテスト"""
        # Arrange
        import app.infrastructure.database.connection as conn_module
        conn_module._engines = {}
        conn_module._sessionmakers = {}
        
        # Act & Assert - エラーが発生しないこと
        await close_database()
        
        assert len(conn_module._engines) == 0
        assert len(conn_module._sessionmakers) == 0

    @pytest.mark.asyncio
    async def test_get_async_session_context(self):
        """get_async_session_context のテスト"""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker = MagicMock()
        mock_sessionmaker.return_value.__aenter__.return_value = mock_session
        
        with patch('app.infrastructure.database.connection.get_sessionmaker', return_value=mock_sessionmaker):
            # Act
            async with get_async_session_context() as session:
                # Assert
                assert session == mock_session
                
        # セッションのコミットとクローズが呼ばれている
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_get_async_session_sync(self):
        """get_async_session_sync のテスト"""
        # Act
        result = get_async_session_sync()
        
        # Assert - get_async_session_context を返すこと
        assert result is not None

    @patch('app.infrastructure.database.connection.logger')
    @patch('app.infrastructure.database.connection.create_async_engine')
    @patch('app.infrastructure.database.connection.get_infrastructure_settings')
    @patch('app.infrastructure.database.connection.asyncio.get_running_loop')
    def test_get_engine_logs_creation(self, mock_get_loop, mock_get_settings, mock_create_engine, mock_logger):
        """エンジン作成時のログ出力テスト"""
        # Arrange
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        
        mock_infra_settings = MagicMock()
        mock_infra_settings.database.url = "postgresql+asyncpg://test:test@localhost/test"
        mock_infra_settings.database.echo = False
        mock_infra_settings.database.pool_size = 5
        mock_infra_settings.database.max_overflow = 10
        mock_infra_settings.database.pool_timeout = 30
        mock_get_settings.return_value = mock_infra_settings
        
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine
        
        # Act
        get_engine()
        
        # Assert
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Database engine created" in log_message

    @patch('app.infrastructure.database.connection.logger')
    @patch('app.infrastructure.database.connection.get_engine')
    @patch('app.infrastructure.database.connection.async_sessionmaker')
    @patch('app.infrastructure.database.connection.asyncio.get_running_loop')
    def test_get_sessionmaker_logs_creation(self, mock_get_loop, mock_async_sessionmaker, mock_get_engine, mock_logger):
        """セッションメーカー作成時のログ出力テスト"""
        # Arrange
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_get_engine.return_value = mock_engine
        
        mock_sessionmaker_instance = MagicMock(spec=async_sessionmaker)
        mock_async_sessionmaker.return_value = mock_sessionmaker_instance
        
        # Act
        get_sessionmaker()
        
        # Assert
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Session maker created" in log_message

    @pytest.mark.asyncio
    @patch('app.infrastructure.database.connection.logger')
    async def test_close_database_logs_closure(self, mock_logger):
        """データベースクローズ時のログ出力テスト"""
        # Arrange
        import app.infrastructure.database.connection as conn_module
        
        mock_loop = MagicMock()
        mock_engine = AsyncMock(spec=AsyncEngine)
        conn_module._engines = {mock_loop: mock_engine}
        conn_module._sessionmakers = {mock_loop: MagicMock()}
        
        # Act
        await close_database()
        
        # Assert
        mock_logger.info.assert_called()
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Database connections closed" in msg for msg in log_messages)