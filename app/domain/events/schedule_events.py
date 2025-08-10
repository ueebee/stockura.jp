"""Schedule domain events."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class ScheduleCreated(DomainEvent):
    """スケジュール作成イベント"""
    
    schedule_name: str
    task_name: str
    cron_expression: str
    enabled: bool = True
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def event_type(self) -> str:
        return "schedule.created"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_name": self.schedule_name,
            "task_name": self.task_name,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "category": self.category,
            "tags": self.tags,
        })
        return base_dict


@dataclass(frozen=True)
class ScheduleUpdated(DomainEvent):
    """スケジュール更新イベント"""
    
    schedule_name: str
    changes: Dict[str, Any]
    
    @property
    def event_type(self) -> str:
        return "schedule.updated"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_name": self.schedule_name,
            "changes": self.changes,
        })
        return base_dict


@dataclass(frozen=True)
class ScheduleDeleted(DomainEvent):
    """スケジュール削除イベント"""
    
    schedule_name: str
    
    @property
    def event_type(self) -> str:
        return "schedule.deleted"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_name": self.schedule_name,
        })
        return base_dict


@dataclass(frozen=True)
class ScheduleEnabled(DomainEvent):
    """スケジュール有効化イベント"""
    
    schedule_name: str
    
    @property
    def event_type(self) -> str:
        return "schedule.enabled"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_name": self.schedule_name,
        })
        return base_dict


@dataclass(frozen=True)
class ScheduleDisabled(DomainEvent):
    """スケジュール無効化イベント"""
    
    schedule_name: str
    reason: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "schedule.disabled"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_name": self.schedule_name,
            "reason": self.reason,
        })
        return base_dict


@dataclass(frozen=True)
class ScheduleExecuted(DomainEvent):
    """スケジュール実行イベント"""
    
    schedule_name: str
    task_name: str
    execution_time: datetime
    task_id: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "schedule.executed"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_name": self.schedule_name,
            "task_name": self.task_name,
            "execution_time": self.execution_time.isoformat(),
            "task_id": self.task_id,
        })
        return base_dict


@dataclass(frozen=True)
class ScheduleExecutionFailed(DomainEvent):
    """スケジュール実行失敗イベント"""
    
    schedule_name: str
    task_name: str
    error_message: str
    execution_time: datetime
    task_id: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "schedule.execution_failed"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_name": self.schedule_name,
            "task_name": self.task_name,
            "error_message": self.error_message,
            "execution_time": self.execution_time.isoformat(),
            "task_id": self.task_id,
        })
        return base_dict


@dataclass(frozen=True)
class ScheduleBulkCreated(DomainEvent):
    """スケジュール一括作成イベント"""
    
    schedule_names: List[str]
    task_name: str
    count: int
    
    @property
    def event_type(self) -> str:
        return "schedule.bulk_created"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "schedule_names": self.schedule_names,
            "task_name": self.task_name,
            "count": self.count,
        })
        return base_dict