"""Repository dependency injection providers."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.schedule_repository_interface import ScheduleRepositoryInterface
from app.domain.repositories.task_log_repository_interface import TaskLogRepositoryInterface
from app.domain.repositories.auth_repository_interface import AuthRepositoryInterface
from app.infrastructure.database.connection import get_session
from app.infrastructure.redis.redis_client import get_redis_client


def get_schedule_repository(
    session: AsyncSession = Depends(get_session)
) -> ScheduleRepositoryInterface:
    """スケジュールリポジトリの依存性注入"""
    # 動的インポートで循環参照を回避
    from app.infrastructure.repositories.database.schedule_repository import ScheduleRepositoryImpl
    return ScheduleRepositoryImpl(session)


def get_task_log_repository(
    session: AsyncSession = Depends(get_session)
) -> TaskLogRepositoryInterface:
    """タスクログリポジトリの依存性注入"""
    # 動的インポートで循環参照を回避
    from app.infrastructure.repositories.database.task_log_repository import TaskLogRepository
    return TaskLogRepository(session)


async def get_auth_repository() -> AuthRepositoryInterface:
    """認証リポジトリの依存性注入"""
    # 動的インポートで循環参照を回避
    from app.infrastructure.repositories.redis.auth_repository_impl import RedisAuthRepository
    redis_client = await get_redis_client()
    return RedisAuthRepository(redis_client)