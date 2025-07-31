"""タスクログ関連のテストデータファクトリー"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from app.domain.entities.task_log import TaskExecutionLog


class TaskLogFactory:
    """TaskExecutionLog エンティティを生成するファクトリー"""

    @staticmethod
    def create_task_log(
        id: Optional[UUID] = None,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        schedule_id: Optional[UUID] = None,
        status: str = "PENDING",
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        result: Optional[dict] = None,
        error_message: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> TaskExecutionLog:
        """TaskExecutionLog エンティティを生成"""
        now = datetime.now()
        return TaskExecutionLog(
            id=id or uuid4(),
            task_id=task_id or f"task_{uuid4().hex}",
            task_name=task_name or "test_task",
            schedule_id=schedule_id or uuid4(),
            status=status,
            started_at=started_at or now,
            finished_at=finished_at,
            result=result,
            error_message=error_message,
            created_at=created_at or now
        )

    @staticmethod
    def create_pending_task_log(
        task_name: Optional[str] = None,
        schedule_id: Optional[UUID] = None
    ) -> TaskExecutionLog:
        """保留中のタスクログを生成"""
        return TaskLogFactory.create_task_log(
            task_name=task_name,
            schedule_id=schedule_id,
            status="PENDING"
        )

    @staticmethod
    def create_running_task_log(
        task_name: Optional[str] = None,
        schedule_id: Optional[UUID] = None,
        started_at: Optional[datetime] = None
    ) -> TaskExecutionLog:
        """実行中のタスクログを生成"""
        return TaskLogFactory.create_task_log(
            task_name=task_name,
            schedule_id=schedule_id,
            status="RUNNING",
            started_at=started_at or datetime.now()
        )

    @staticmethod
    def create_success_task_log(
        task_name: Optional[str] = None,
        schedule_id: Optional[UUID] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        result: Optional[dict] = None
    ) -> TaskExecutionLog:
        """成功したタスクログを生成"""
        start_time = started_at or datetime.now()
        end_time = finished_at or datetime.now()
        
        return TaskLogFactory.create_task_log(
            task_name=task_name,
            schedule_id=schedule_id,
            status="SUCCESS",
            started_at=start_time,
            finished_at=end_time,
            result=result or {"message": "Task completed successfully"}
        )

    @staticmethod
    def create_failed_task_log(
        task_name: Optional[str] = None,
        schedule_id: Optional[UUID] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> TaskExecutionLog:
        """失敗したタスクログを生成"""
        start_time = started_at or datetime.now()
        end_time = finished_at or datetime.now()
        
        return TaskLogFactory.create_task_log(
            task_name=task_name,
            schedule_id=schedule_id,
            status="FAILURE",
            started_at=start_time,
            finished_at=end_time,
            error_message=error_message or "Task failed with error"
        )