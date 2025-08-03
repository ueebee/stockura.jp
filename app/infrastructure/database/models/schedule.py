"""Schedule model for Celery Beat."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.infrastructure.database.connection import Base


class CeleryBeatSchedule(Base):
    """Schedule model for Celery Beat tasks."""

    __tablename__ = "celery_beat_schedules"
    __table_args__ = (
        CheckConstraint(
            "execution_policy IN ('allow', 'skip', 'queue')",
            name="ck_celery_beat_schedules_execution_policy"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    args = Column(JSONB, default=list, nullable=False)
    kwargs = Column(JSONB, default=dict, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    tags = Column(JSONB, default=list, nullable=False)
    execution_policy = Column(String(20), default="allow", nullable=False)
    auto_generated_name = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<CeleryBeatSchedule(name={self.name}, task={self.task_name}, enabled={self.enabled})>"