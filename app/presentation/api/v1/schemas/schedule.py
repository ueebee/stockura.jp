"""Schedule API schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from croniter import croniter


class TaskParams(BaseModel):
    """Task parameters schema."""

    period_type: str = Field(
        default="yesterday",
        description="Period type: yesterday, 7days, 30days, custom",
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Start date for custom period (YYYY-MM-DD)",
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date for custom period (YYYY-MM-DD)",
    )
    codes: Optional[List[str]] = Field(
        default=None,
        description="List of stock codes to fetch",
    )
    market: Optional[str] = Field(
        default=None,
        description="Market code to filter",
    )


class ScheduleBase(BaseModel):
    """Base schedule schema."""

    name: str = Field(..., description="Unique schedule name")
    cron_expression: str = Field(
        ..., description="Cron expression (e.g., '0 9 * * *' for daily at 9 AM)"
    )
    enabled: bool = Field(default=True, description="Whether schedule is enabled")
    description: Optional[str] = Field(default=None, description="Schedule description")
    task_params: TaskParams = Field(default_factory=TaskParams, description="Task parameters")

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, v: str) -> str:
        """Validate cron expression."""
        try:
            croniter(v)
            return v
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")


class ScheduleCreate(ScheduleBase):
    """Schedule creation schema."""

    pass


class ScheduleUpdate(BaseModel):
    """Schedule update schema."""

    name: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    task_params: Optional[TaskParams] = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, v: Optional[str]) -> Optional[str]:
        """Validate cron expression if provided."""
        if v is not None:
            try:
                croniter(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {str(e)}")
        return v


class ScheduleResponse(ScheduleBase):
    """Schedule response schema."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ScheduleListResponse(BaseModel):
    """Schedule list response schema."""

    items: List[ScheduleResponse]
    total: int


class ScheduleEnableResponse(BaseModel):
    """Schedule enable/disable response."""

    id: UUID
    enabled: bool
    message: str