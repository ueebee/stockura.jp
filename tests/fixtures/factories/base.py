"""
FactoryBoy ベース設定

すべてのファクトリーの基底クラスを定義します。
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.database import db_session


class AsyncSQLAlchemyModelFactory(SQLAlchemyModelFactory):
    """
    非同期 SQLAlchemy モデル用のベースファクトリー
    
    AsyncSession をサポートするファクトリー基底クラス。
    """
    
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"
    
    @classmethod
    async def create_async(cls, **kwargs):
        """非同期でインスタンスを作成"""
        instance = cls.build(**kwargs)
        session = cls._meta.sqlalchemy_session
        
        if isinstance(session, AsyncSession):
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
        else:
            # 同期セッションの場合は通常の処理
            session.add(instance)
            session.commit()
            session.refresh(instance)
        
        return instance
    
    @classmethod
    async def create_batch_async(cls, size, **kwargs):
        """非同期で複数のインスタンスを作成"""
        instances = []
        for _ in range(size):
            instance = await cls.create_async(**kwargs)
            instances.append(instance)
        return instances


class BaseFactory(AsyncSQLAlchemyModelFactory):
    """
    プロジェクト共通のベースファクトリー
    
    全てのモデルファクトリーはこのクラスを継承します。
    """
    
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"
    
    # 共通フィールドの定義
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.Faker("date_time_this_year")
    
    @classmethod
    def _setup_next_sequence(cls):
        """シーケンスカウンターをリセット"""
        return 1
    
    @classmethod
    def reset_sequence(cls, value=None):
        """シーケンスを指定値にリセット"""
        cls._sequence = value or 1