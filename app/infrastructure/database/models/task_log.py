"""Task execution log model."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.database.connection import Base


class TaskExecutionLog(Base):
    """Task execution log model."""

    __tablename__ = "task_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("celery_beat_schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_name = Column(String(255), nullable=False, index=True)
    task_id = Column(String(255), nullable=True, index=True)  # Celery task ID
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        String(50), nullable=False, index=True
    )  # 'running', 'success', 'failed'
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    schedule = relationship(
        "CeleryBeatSchedule",
        backref="execution_logs",
        foreign_keys=[schedule_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaskExecutionLog(task={self.task_name}, status={self.status}, started_at={self.started_at})>"