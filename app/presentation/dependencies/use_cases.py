"""Use case dependency injection providers."""
from typing import Optional

from fastapi import Depends

from app.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.application.use_cases.auth_use_case import AuthUseCase
from app.application.use_cases.manage_listed_info_schedule import ManageListedInfoScheduleUseCase
from app.domain.repositories.schedule_repository_interface import ScheduleRepositoryInterface
from app.domain.repositories.auth_repository_interface import AuthRepositoryInterface
from app.domain.repositories.listed_info_repository_interface import ListedInfoRepositoryInterface
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher
from .repositories import get_schedule_repository, get_auth_repository
from .services import get_schedule_event_publisher


def get_manage_schedule_use_case(
    repository: ScheduleRepositoryInterface = Depends(get_schedule_repository),
    event_publisher: Optional[ScheduleEventPublisher] = Depends(get_schedule_event_publisher),
) -> ManageScheduleUseCase:
    """スケジュール管理ユースケースの依存性注入"""
    return ManageScheduleUseCase(repository, event_publisher=event_publisher)


def get_auth_use_case(
    auth_repository: AuthRepositoryInterface = Depends(get_auth_repository),
) -> AuthUseCase:
    """認証ユースケースの依存性注入"""
    return AuthUseCase(auth_repository)


def get_manage_listed_info_schedule_use_case(
    schedule_repository: ScheduleRepositoryInterface = Depends(get_schedule_repository),
    event_publisher: Optional[ScheduleEventPublisher] = Depends(get_schedule_event_publisher),
) -> ManageListedInfoScheduleUseCase:
    """上場銘柄情報スケジュール管理ユースケースの依存性注入"""
    # ManageListedInfoScheduleUseCase が schedule_repository のみを必要とする場合
    return ManageListedInfoScheduleUseCase(
        schedule_repository,
        event_publisher=event_publisher,
    )