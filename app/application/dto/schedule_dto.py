"""Schedule DTOs."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


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

    name: str
    task_name: str
    cron_expression: str
    enabled: bool = True
    description: Optional[str] = None
    task_params: Optional[TaskParamsDto] = None


@dataclass
class ScheduleUpdateDto:
    """Schedule update DTO."""

    name: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    task_params: Optional[TaskParamsDto] = None


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