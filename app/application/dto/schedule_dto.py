"""Schedule DTOs."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.entities.schedule import Schedule


@dataclass
class TaskParamsDto:
    """Task parameters DTO."""

    period_type: str = "yesterday"
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    codes: Optional[List[str]] = None
    market: Optional[str] = None

    def to_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs for Celery task."""
        kwargs = {"period_type": self.period_type}
        
        if self.from_date:
            kwargs["from_date"] = self.from_date
        if self.to_date:
            kwargs["to_date"] = self.to_date
        if self.codes:
            kwargs["codes"] = self.codes
        if self.market:
            kwargs["market"] = self.market
            
        return kwargs


@dataclass
class ScheduleCreateDto:
    """Schedule creation DTO."""

    name: Optional[str]  # Optional now for auto-generation
    task_name: str
    cron_expression: str
    enabled: bool = True
    description: Optional[str] = None
    task_params: Optional[TaskParamsDto] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    execution_policy: Optional[str] = None


@dataclass
class ScheduleUpdateDto:
    """Schedule update DTO."""

    name: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    task_params: Optional[TaskParamsDto] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    execution_policy: Optional[str] = None


@dataclass
class ScheduleDto:
    """Schedule DTO."""

    id: UUID
    name: str
    task_name: str
    cron_expression: str
    enabled: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    task_params: Optional[TaskParamsDto] = None
    category: Optional[str] = None
    tags: List[str] = None
    execution_policy: str = "allow"
    auto_generated_name: bool = False

    def __post_init__(self):
        """Post initialization."""
        if self.tags is None:
            self.tags = []

    @classmethod
    def from_entity(cls, entity: Schedule) -> "ScheduleDto":
        """Create DTO from entity."""
        # Extract task_params from kwargs
        task_params = None
        if entity.kwargs:
            task_params = TaskParamsDto(
                period_type=entity.kwargs.get("period_type", "yesterday"),
                from_date=entity.kwargs.get("from_date"),
                to_date=entity.kwargs.get("to_date"),
                codes=entity.kwargs.get("codes"),
                market=entity.kwargs.get("market"),
            )
        
        return cls(
            id=entity.id,
            name=entity.name,
            task_name=entity.task_name,
            cron_expression=entity.cron_expression,
            enabled=entity.enabled,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            task_params=task_params,
            category=entity.category,
            tags=entity.tags,
            execution_policy=entity.execution_policy,
            auto_generated_name=entity.auto_generated_name,
        )