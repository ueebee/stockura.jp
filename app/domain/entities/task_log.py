"""Task execution log entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class TaskExecutionLog:
    """Task execution log entity."""

    id: UUID
    task_name: str
    started_at: datetime
    status: str  # 'running', 'success', 'failed'
    schedule_id: Optional[UUID] = None
    task_id: Optional[str] = None  # Celery task ID
    finished_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "schedule_id": str(self.schedule_id) if self.schedule_id else None,
            "task_name": self.task_name,
            "task_id": self.task_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None