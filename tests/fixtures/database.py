"""
データベース関連のテストフィクスチャ

このモジュールはテスト用のデータベース接続、トランザクション管理、
およびクリーンアップ機能を提供します。
"""

import asyncio
import logging
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.infrastructure.database.connection import Base
from tests.settings.test_config import test_settings

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def database_url() -> str:
    """テスト用データベース URL"""
    return test_settings.database_url_with_schema


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    テスト用の非同期データベースエンジン
    
    セッションスコープで一度だけ作成され、
    すべてのテストで共有されます。
    """
    # プール無効化（テスト環境では接続プールは不要）
    engine = create_async_engine(
        test_settings.database_url_with_schema,
        echo=test_settings.database_echo,
        poolclass=NullPool,
    )
    
    # データベース作成とマイグレーション
    async with engine.begin() as conn:
        # スキーマが指定されている場合は作成
        if test_settings.test_db_schema:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {test_settings.test_db_schema}"))
            await conn.execute(text(f"SET search_path TO {test_settings.test_db_schema}"))
        
        # テーブル作成
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # クリーンアップ
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        if test_settings.test_db_schema:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {test_settings.test_db_schema} CASCADE"))
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    関数スコープのデータベースセッション
    
    各テストごとにトランザクションを開始し、
    テスト終了時にロールバックします。
    """
    # セッションファクトリー作成
    async_session_factory = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_factory() as session:
        async with session.begin():
            yield session
            # テスト終了時に自動的にロールバック


@pytest.fixture(scope="session")
def sync_test_engine():
    """
    同期版のテストエンジン（マイグレーション等で使用）
    """
    # PostgreSQL URL を同期版に変換
    sync_url = test_settings.database_url_with_schema.replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    
    engine = create_engine(
        sync_url,
        echo=test_settings.database_echo,
        poolclass=NullPool,
    )
    
    # データベース作成
    with engine.begin() as conn:
        if test_settings.test_db_schema:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {test_settings.test_db_schema}"))
            conn.execute(text(f"SET search_path TO {test_settings.test_db_schema}"))
        
        Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # クリーンアップ
    with engine.begin() as conn:
        Base.metadata.drop_all(bind=engine)
        if test_settings.test_db_schema:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {test_settings.test_db_schema} CASCADE"))
    
    engine.dispose()


@pytest.fixture(scope="function")
def sync_db_session(sync_test_engine) -> Generator[Session, None, None]:
    """
    同期版のデータベースセッション
    
    非同期でないテストで使用します。
    """
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sync_test_engine,
    )
    
    session = SessionLocal()
    
    # トランザクション開始
    session.begin()
    
    yield session
    
    # ロールバック
    session.rollback()
    session.close()


@pytest_asyncio.fixture(scope="function")
async def clean_db(db_session: AsyncSession):
    """
    データベースをクリーンな状態に保つフィクスチャ
    
    テスト実行前にデータをクリアします。
    """
    # 全テーブルのデータを削除（メタデータは保持）
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(table.delete())
    await db_session.commit()
    
    yield
    
    # テスト後のクリーンアップは db_session のロールバックで行われる


@pytest.fixture
def db_transaction_spy(sync_test_engine):
    """
    データベーストランザクションを監視するフィクスチャ
    
    テスト中のコミット/ロールバックを検出します。
    """
    commits = []
    rollbacks = []
    
    @event.listens_for(sync_test_engine, "commit")
    def receive_commit(conn):
        commits.append(True)
    
    @event.listens_for(sync_test_engine, "rollback")
    def receive_rollback(conn):
        rollbacks.append(True)
    
    yield {
        "commits": commits,
        "rollbacks": rollbacks,
    }
    
    # イベントリスナーを削除
    event.remove(sync_test_engine, "commit", receive_commit)
    event.remove(sync_test_engine, "rollback", receive_rollback)


# テスト用のデータベース接続確認
@pytest_asyncio.fixture(scope="session", autouse=True)
async def verify_test_database():
    """テストデータベースへの接続を確認"""
    try:
        engine = create_async_engine(
            test_settings.database_url,
            poolclass=NullPool,
        )
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        await engine.dispose()
        logger.info("Test database connection verified")
    except Exception as e:
        pytest.skip(f"Test database is not available: {e}")


# Alembic マイグレーションを実行するフィクスチャ（オプション）
@pytest.fixture(scope="session")
def migrated_db(sync_test_engine):
    """
    Alembic マイグレーションを適用したデータベース
    
    本番と同じマイグレーションを適用してテストする場合に使用。
    """
    from alembic import command
    from alembic.config import Config
    
    # Alembic 設定
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", str(sync_test_engine.url))
    
    # マイグレーション実行
    command.upgrade(alembic_cfg, "head")
    
    yield sync_test_engine
    
    # ダウングレード
    command.downgrade(alembic_cfg, "base")