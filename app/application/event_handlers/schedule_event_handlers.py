"""Schedule event handlers."""
import logging
from typing import Optional

from app.core.logger import get_logger
from app.domain.events.base import DomainEvent, EventHandler
from app.domain.events.schedule_events import (
    ScheduleCreated,
    ScheduleDeleted,
    ScheduleDisabled,
    ScheduleEnabled,
    ScheduleExecuted,
    ScheduleExecutionFailed,
)
from app.domain.repositories.task_log_repository_interface import TaskLogRepositoryInterface

logger = get_logger(__name__)


class ScheduleEventLogger(EventHandler):
    """スケジュールイベントをログに記録するハンドラー"""
    
    def can_handle(self, event: DomainEvent) -> bool:
        """スケジュール関連のすべてのイベントを処理"""
        return event.event_type.startswith("schedule.")
    
    async def handle(self, event: DomainEvent) -> None:
        """イベントをログに記録"""
        logger.info(
            f"Schedule event occurred: {event.event_type}",
            extra={
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "event_data": event.to_dict(),
            }
        )


class ScheduleExecutionLogger(EventHandler):
    """スケジュール実行結果をタスクログに記録するハンドラー"""
    
    def __init__(self, task_log_repository: TaskLogRepositoryInterface):
        self.task_log_repository = task_log_repository
    
    def can_handle(self, event: DomainEvent) -> bool:
        """実行関連のイベントのみ処理"""
        return event.event_type in ["schedule.executed", "schedule.execution_failed"]
    
    async def handle(self, event: DomainEvent) -> None:
        """実行結果をタスクログに記録"""
        if isinstance(event, ScheduleExecuted):
            await self._handle_execution_success(event)
        elif isinstance(event, ScheduleExecutionFailed):
            await self._handle_execution_failure(event)
    
    async def _handle_execution_success(self, event: ScheduleExecuted) -> None:
        """実行成功をログに記録"""
        logger.info(
            f"Schedule execution succeeded: {event.schedule_name}",
            extra={
                "schedule_name": event.schedule_name,
                "task_name": event.task_name,
                "task_id": event.task_id,
                "execution_time": event.execution_time.isoformat(),
            }
        )
        # タスクログリポジトリへの記録（実装はリポジトリ側で行う）
    
    async def _handle_execution_failure(self, event: ScheduleExecutionFailed) -> None:
        """実行失敗をログに記録"""
        logger.error(
            f"Schedule execution failed: {event.schedule_name}",
            extra={
                "schedule_name": event.schedule_name,
                "task_name": event.task_name,
                "task_id": event.task_id,
                "error_message": event.error_message,
                "execution_time": event.execution_time.isoformat(),
            }
        )
        # タスクログリポジトリへの記録（実装はリポジトリ側で行う）


class ScheduleStateChangeNotifier(EventHandler):
    """スケジュール状態変更を通知するハンドラー"""
    
    def can_handle(self, event: DomainEvent) -> bool:
        """状態変更イベントのみ処理"""
        return event.event_type in [
            "schedule.created",
            "schedule.deleted",
            "schedule.enabled",
            "schedule.disabled"
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """状態変更を通知"""
        if isinstance(event, ScheduleCreated):
            await self._notify_schedule_created(event)
        elif isinstance(event, ScheduleDeleted):
            await self._notify_schedule_deleted(event)
        elif isinstance(event, ScheduleEnabled):
            await self._notify_schedule_enabled(event)
        elif isinstance(event, ScheduleDisabled):
            await self._notify_schedule_disabled(event)
    
    async def _notify_schedule_created(self, event: ScheduleCreated) -> None:
        """スケジュール作成を通知"""
        logger.info(
            f"New schedule created: {event.schedule_name}",
            extra={
                "schedule_name": event.schedule_name,
                "task_name": event.task_name,
                "cron_expression": event.cron_expression,
                "enabled": event.enabled,
            }
        )
        # 実際の通知処理（Slack 、メール等）はここに実装
    
    async def _notify_schedule_deleted(self, event: ScheduleDeleted) -> None:
        """スケジュール削除を通知"""
        logger.info(
            f"Schedule deleted: {event.schedule_name}",
            extra={"schedule_name": event.schedule_name}
        )
        # 実際の通知処理はここに実装
    
    async def _notify_schedule_enabled(self, event: ScheduleEnabled) -> None:
        """スケジュール有効化を通知"""
        logger.info(
            f"Schedule enabled: {event.schedule_name}",
            extra={"schedule_name": event.schedule_name}
        )
        # 実際の通知処理はここに実装
    
    async def _notify_schedule_disabled(self, event: ScheduleDisabled) -> None:
        """スケジュール無効化を通知"""
        logger.warning(
            f"Schedule disabled: {event.schedule_name}",
            extra={
                "schedule_name": event.schedule_name,
                "reason": event.reason,
            }
        )
        # 実際の通知処理はここに実装