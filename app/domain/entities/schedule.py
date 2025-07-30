"""Schedule entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class Schedule:
    """Schedule entity for Celery Beat tasks."""

    id: UUID
    name: str
    task_name: str
    cron_expression: str
    enabled: bool = True
    args: List[Any] = None
    kwargs: Dict[str, Any] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Post initialization."""
        if self.args is None:
            self.args = []
        if self.kwargs is None:
            self.kwargs = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "task_name": self.task_name,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "args": self.args,
            "kwargs": self.kwargs,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }