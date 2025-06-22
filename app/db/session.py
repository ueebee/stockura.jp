import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings

logger = logging.getLogger(__name__)

# 同期エンジン（既存）
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# 非同期エンジン（新規追加）
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # コネクションプールの健全性チェック
)

# 非同期セッションメーカー
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_db():
    """データベースセッションを取得します（同期版）。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_session() -> AsyncSession:
    """非同期データベースセッションを取得します。"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# 非同期セッションのコンテキストマネージャー
async def get_async_session() -> AsyncSession:
    """非同期データベースセッションを取得します（コンテキストマネージャー版）。"""
    return async_session_maker()


async def check_database_connection() -> bool:
    """データベース接続の健全性をチェックします。"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            await session.commit()
            logger.info("Database connection check passed")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database connection check: {e}")
        return False


def check_sync_database_connection() -> bool:
    """同期データベース接続の健全性をチェックします。"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Sync database connection check passed")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Sync database connection check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during sync database connection check: {e}")
        return False 