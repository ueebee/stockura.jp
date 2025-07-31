"""スケジュール関連のテストデータファクトリー"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from app.application.dto.schedule_dto import ScheduleCreateDto, ScheduleDto, ScheduleUpdateDto, TaskParamsDto
from app.domain.entities.schedule import Schedule


class ScheduleFactory:
    """スケジュールエンティティと DTO を生成するファクトリー"""

    @staticmethod
    def create_schedule_entity(
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        task_name: Optional[str] = None,
        args: Optional[list] = None,
        kwargs: Optional[dict] = None,
        cron_expression: Optional[str] = None,
        enabled: bool = True,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> Schedule:
        """Schedule エンティティを生成"""
        now = datetime.now()
        return Schedule(
            id=id or uuid4(),
            name=name or f"test_schedule_{uuid4().hex[:8]}",
            task_name=task_name or "test_task",
            args=args or [],
            kwargs=kwargs or {},
            cron_expression=cron_expression or "0 0 * * *",  # 毎日 0 時
            enabled=enabled,
            description=description or "Test schedule",
            created_at=created_at or now,
            updated_at=updated_at or now
        )

    @staticmethod
    def create_schedule_dto(
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        task_name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        enabled: bool = True,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        task_params: Optional[TaskParamsDto] = None
    ) -> ScheduleDto:
        """ScheduleDTO を生成"""
        now = datetime.now()
        return ScheduleDto(
            id=id or uuid4(),
            name=name or f"test_schedule_{uuid4().hex[:8]}",
            task_name=task_name or "test_task",
            cron_expression=cron_expression or "0 0 * * *",
            enabled=enabled,
            description=description,
            created_at=created_at or now,
            updated_at=updated_at or now,
            task_params=task_params
        )

    @staticmethod
    def create_schedule_create_dto(
        name: Optional[str] = None,
        task_name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        enabled: bool = True,
        description: Optional[str] = None,
        task_params: Optional[TaskParamsDto] = None
    ) -> ScheduleCreateDto:
        """ScheduleCreateDto を生成"""
        return ScheduleCreateDto(
            name=name or f"test_schedule_{uuid4().hex[:8]}",
            task_name=task_name or "test_task",
            cron_expression=cron_expression or "0 0 * * *",
            enabled=enabled,
            description=description,
            task_params=task_params
        )

    @staticmethod
    def create_schedule_update_dto(
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        enabled: Optional[bool] = None,
        description: Optional[str] = None,
        task_params: Optional[TaskParamsDto] = None
    ) -> ScheduleUpdateDto:
        """ScheduleUpdateDto を生成"""
        return ScheduleUpdateDto(
            name=name,
            cron_expression=cron_expression,
            enabled=enabled,
            description=description,
            task_params=task_params
        )