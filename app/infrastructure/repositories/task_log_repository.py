"""Task log repository implementation."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.task_log import TaskExecutionLog
from app.domain.repositories.task_log_repository_interface import (
    TaskLogRepositoryInterface,
)
from app.infrastructure.database.models.task_log import TaskExecutionLog as DBTaskLog


class TaskLogRepository(TaskLogRepositoryInterface):
    """Task log repository implementation."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        self._session = session

    async def create(self, task_log: TaskExecutionLog) -> TaskExecutionLog:
        """Create a new task execution log."""
        db_log = DBTaskLog(
            id=task_log.id,
            schedule_id=task_log.schedule_id,
            task_name=task_log.task_name,
            task_id=task_log.task_id,
            started_at=task_log.started_at,
            finished_at=task_log.finished_at,
            status=task_log.status,
            result=task_log.result,
            error_message=task_log.error_message,
        )
        self._session.add(db_log)
        await self._session.commit()
        await self._session.refresh(db_log)
        return self._to_entity(db_log)

    async def get_by_id(self, log_id: UUID) -> Optional[TaskExecutionLog]:
        """Get task log by ID."""
        result = await self._session.execute(
            select(DBTaskLog).where(DBTaskLog.id == log_id)
        )
        db_log = result.scalar_one_or_none()
        return self._to_entity(db_log) if db_log else None

    async def get_by_task_id(self, task_id: str) -> Optional[TaskExecutionLog]:
        """Get task log by Celery task ID."""
        result = await self._session.execute(
            select(DBTaskLog).where(DBTaskLog.task_id == task_id)
        )
        db_log = result.scalar_one_or_none()
        return self._to_entity(db_log) if db_log else None

    async def get_by_schedule_id(
        self, schedule_id: UUID, limit: int = 100
    ) -> List[TaskExecutionLog]:
        """Get task logs by schedule ID."""
        result = await self._session.execute(
            select(DBTaskLog)
            .where(DBTaskLog.schedule_id == schedule_id)
            .order_by(desc(DBTaskLog.started_at))
            .limit(limit)
        )
        return [self._to_entity(log) for log in result.scalars().all()]

    async def get_recent_logs(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[TaskExecutionLog]:
        """Get recent task logs."""
        query = select(DBTaskLog).order_by(desc(DBTaskLog.started_at)).limit(limit)
        
        if status:
            query = query.where(DBTaskLog.status == status)
        
        if since:
            query = query.where(DBTaskLog.started_at >= since)
        
        result = await self._session.execute(query)
        return [self._to_entity(log) for log in result.scalars().all()]

    async def update_status(
        self,
        log_id: UUID,
        status: str,
        finished_at: Optional[datetime] = None,
        result: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update task execution status."""
        values = {"status": status}
        if finished_at:
            values["finished_at"] = finished_at
        if result is not None:
            values["result"] = result
        if error_message is not None:
            values["error_message"] = error_message

        result = await self._session.execute(
            update(DBTaskLog).where(DBTaskLog.id == log_id).values(**values)
        )
        await self._session.commit()
        return result.rowcount > 0

    def _to_entity(self, db_log: DBTaskLog) -> TaskExecutionLog:
        """Convert database model to domain entity."""
        return TaskExecutionLog(
            id=db_log.id,
            schedule_id=db_log.schedule_id,
            task_name=db_log.task_name,
            task_id=db_log.task_id,
            started_at=db_log.started_at,
            finished_at=db_log.finished_at,
            status=db_log.status,
            result=db_log.result,
            error_message=db_log.error_message,
            created_at=db_log.created_at,
        )