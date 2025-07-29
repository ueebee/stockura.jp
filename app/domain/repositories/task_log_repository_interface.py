"""Task log repository interface."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.entities.task_log import TaskExecutionLog


class TaskLogRepositoryInterface(ABC):
    """Task log repository interface."""

    @abstractmethod
    async def create(self, task_log: TaskExecutionLog) -> TaskExecutionLog:
        """Create a new task execution log."""
        pass

    @abstractmethod
    async def get_by_id(self, log_id: UUID) -> Optional[TaskExecutionLog]:
        """Get task log by ID."""
        pass

    @abstractmethod
    async def get_by_task_id(self, task_id: str) -> Optional[TaskExecutionLog]:
        """Get task log by Celery task ID."""
        pass

    @abstractmethod
    async def get_by_schedule_id(
        self, schedule_id: UUID, limit: int = 100
    ) -> List[TaskExecutionLog]:
        """Get task logs by schedule ID."""
        pass

    @abstractmethod
    async def get_recent_logs(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[TaskExecutionLog]:
        """Get recent task logs."""
        pass

    @abstractmethod
    async def update_status(
        self,
        log_id: UUID,
        status: str,
        finished_at: Optional[datetime] = None,
        result: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update task execution status."""
        pass