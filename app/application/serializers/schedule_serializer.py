"""Schedule entity serializer."""
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from app.domain.entities.schedule import Schedule


class ScheduleSerializer:
    """Schedule エンティティのシリアライザー"""

    @staticmethod
    def to_dict(schedule: Schedule) -> Dict[str, Any]:
        """Schedule エンティティを Dict に変換"""
        return {
            "id": str(schedule.id),
            "name": schedule.name,
            "task_name": schedule.task_name,
            "cron_expression": schedule.cron_expression,
            "enabled": schedule.enabled,
            "args": schedule.args,
            "kwargs": schedule.kwargs,
            "description": schedule.description,
            "category": schedule.category,
            "tags": schedule.tags,
            "execution_policy": schedule.execution_policy,
            "auto_generated_name": schedule.auto_generated_name,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Schedule:
        """Dict から Schedule エンティティを生成"""
        return Schedule(
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            name=data["name"],
            task_name=data["task_name"],
            cron_expression=data["cron_expression"],
            enabled=data.get("enabled", True),
            args=data.get("args", []),
            kwargs=data.get("kwargs", {}),
            description=data.get("description"),
            category=data.get("category"),
            tags=data.get("tags", []),
            execution_policy=data.get("execution_policy", "allow"),
            auto_generated_name=data.get("auto_generated_name", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )