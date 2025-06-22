from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# 非同期エンジンの作成
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# 非同期セッションの作成
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# モデルのベースクラス
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """非同期セッションを取得する"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close() 