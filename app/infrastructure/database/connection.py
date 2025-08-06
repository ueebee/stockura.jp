"""Database connection module."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Create base class for SQLAlchemy models
Base = declarative_base()

# Global engine instance - keyed by event loop to prevent cross-loop contamination
import asyncio
from typing import Dict
_engines: Dict[asyncio.AbstractEventLoop, AsyncEngine] = {}
_sessionmakers: Dict[asyncio.AbstractEventLoop, async_sessionmaker] = {}


def get_engine() -> AsyncEngine:
    """Get or create async engine instance for the current event loop.

    Returns:
        AsyncEngine instance
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # If no event loop is running, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop not in _engines:
        _engines[loop] = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,  # Enable connection health checks
        )
        logger.info(f"Database engine created for event loop {id(loop)}")
    return _engines[loop]


def get_sessionmaker() -> async_sessionmaker:
    """Get or create async session maker for the current event loop.

    Returns:
        async_sessionmaker instance
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # If no event loop is running, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop not in _sessionmakers:
        engine = get_engine()
        _sessionmakers[loop] = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info(f"Session maker created for event loop {id(loop)}")
    return _sessionmakers[loop]


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    Yields:
        AsyncSession instance
    """
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def drop_tables() -> None:
    """Drop all database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped")


async def close_database() -> None:
    """Close database connections for all event loops."""
    global _engines, _sessionmakers
    for loop, engine in list(_engines.items()):
        await engine.dispose()
        logger.info(f"Database connections closed for event loop {id(loop)}")
    _engines.clear()
    _sessionmakers.clear()


@asynccontextmanager
async def get_async_session_context():
    """Get async database session context manager for CLI usage.
    
    This is specifically for CLI commands that need a session context.
    
    Yields:
        AsyncSession instance
    """
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_async_session_sync():
    """Get async session for synchronous context (e.g., Celery Beat).
    
    Returns:
        AsyncSession context manager
    """
    return get_async_session_context()