"""Tests for ScheduleSerializer."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from app.application.serializers.schedule_serializer import ScheduleSerializer
from app.domain.entities.schedule import Schedule


class TestScheduleSerializer:
    """ScheduleSerializer tests."""

    def test_to_dict_complete_schedule(self):
        """to_dict メソッドが完全な Schedule エンティティを正しく変換することを確認"""
        schedule_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()
        
        schedule = Schedule(
            id=schedule_id,
            name="test_schedule",
            task_name="app.tasks.test_task",
            cron_expression="0 * * * *",
            enabled=True,
            args=["arg1", "arg2"],
            kwargs={"key1": "value1", "key2": "value2"},
            description="Test schedule description",
            category="test_category",
            tags=["tag1", "tag2"],
            execution_policy="allow",
            auto_generated_name=False,
            created_at=created_at,
            updated_at=updated_at,
        )

        result = ScheduleSerializer.to_dict(schedule)

        assert result["id"] == str(schedule_id)
        assert result["name"] == "test_schedule"
        assert result["task_name"] == "app.tasks.test_task"
        assert result["cron_expression"] == "0 * * * *"
        assert result["enabled"] is True
        assert result["args"] == ["arg1", "arg2"]
        assert result["kwargs"] == {"key1": "value1", "key2": "value2"}
        assert result["description"] == "Test schedule description"
        assert result["category"] == "test_category"
        assert result["tags"] == ["tag1", "tag2"]
        assert result["execution_policy"] == "allow"
        assert result["auto_generated_name"] is False
        assert result["created_at"] == created_at.isoformat()
        assert result["updated_at"] == updated_at.isoformat()

    def test_to_dict_minimal_schedule(self):
        """to_dict メソッドが最小限の Schedule エンティティを正しく変換することを確認"""
        schedule_id = uuid4()
        
        schedule = Schedule(
            id=schedule_id,
            name="minimal_schedule",
            task_name="app.tasks.minimal_task",
            cron_expression="0 0 * * *",
        )

        result = ScheduleSerializer.to_dict(schedule)

        assert result["id"] == str(schedule_id)
        assert result["name"] == "minimal_schedule"
        assert result["task_name"] == "app.tasks.minimal_task"
        assert result["cron_expression"] == "0 0 * * *"
        assert result["enabled"] is True
        assert result["args"] == []
        assert result["kwargs"] == {}
        assert result["description"] is None
        assert result["category"] is None
        assert result["tags"] == []
        assert result["execution_policy"] == "allow"
        assert result["auto_generated_name"] is False
        assert result["created_at"] is None
        assert result["updated_at"] is None

    def test_from_dict_complete_data(self):
        """from_dict メソッドが完全なデータから Schedule エンティティを正しく生成することを確認"""
        schedule_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()
        
        data = {
            "id": str(schedule_id),
            "name": "test_schedule",
            "task_name": "app.tasks.test_task",
            "cron_expression": "0 * * * *",
            "enabled": True,
            "args": ["arg1", "arg2"],
            "kwargs": {"key1": "value1", "key2": "value2"},
            "description": "Test schedule description",
            "category": "test_category",
            "tags": ["tag1", "tag2"],
            "execution_policy": "allow",
            "auto_generated_name": False,
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
        }

        schedule = ScheduleSerializer.from_dict(data)

        assert schedule.id == schedule_id
        assert schedule.name == "test_schedule"
        assert schedule.task_name == "app.tasks.test_task"
        assert schedule.cron_expression == "0 * * * *"
        assert schedule.enabled is True
        assert schedule.args == ["arg1", "arg2"]
        assert schedule.kwargs == {"key1": "value1", "key2": "value2"}
        assert schedule.description == "Test schedule description"
        assert schedule.category == "test_category"
        assert schedule.tags == ["tag1", "tag2"]
        assert schedule.execution_policy == "allow"
        assert schedule.auto_generated_name is False
        assert schedule.created_at == created_at
        assert schedule.updated_at == updated_at

    def test_from_dict_minimal_data(self):
        """from_dict メソッドが最小限のデータから Schedule エンティティを正しく生成することを確認"""
        schedule_id = uuid4()
        
        data = {
            "id": str(schedule_id),
            "name": "minimal_schedule",
            "task_name": "app.tasks.minimal_task",
            "cron_expression": "0 0 * * *",
        }

        schedule = ScheduleSerializer.from_dict(data)

        assert schedule.id == schedule_id
        assert schedule.name == "minimal_schedule"
        assert schedule.task_name == "app.tasks.minimal_task"
        assert schedule.cron_expression == "0 0 * * *"
        assert schedule.enabled is True
        assert schedule.args == []
        assert schedule.kwargs == {}
        assert schedule.description is None
        assert schedule.category is None
        assert schedule.tags == []
        assert schedule.execution_policy == "allow"
        assert schedule.auto_generated_name is False
        assert schedule.created_at is None
        assert schedule.updated_at is None

    def test_from_dict_with_uuid_object(self):
        """from_dict メソッドが UUID オブジェクトを含むデータを正しく処理することを確認"""
        schedule_id = uuid4()
        
        data = {
            "id": schedule_id,  # UUID object instead of string
            "name": "test_schedule",
            "task_name": "app.tasks.test_task",
            "cron_expression": "0 * * * *",
        }

        schedule = ScheduleSerializer.from_dict(data)

        assert schedule.id == schedule_id

    def test_roundtrip_conversion(self):
        """to_dict と from_dict の往復変換が正しく動作することを確認"""
        original_schedule = Schedule(
            id=uuid4(),
            name="roundtrip_schedule",
            task_name="app.tasks.roundtrip_task",
            cron_expression="*/5 * * * *",
            enabled=False,
            args=["test"],
            kwargs={"test": True},
            description="Roundtrip test",
            category="test",
            tags=["roundtrip"],
            execution_policy="deny",
            auto_generated_name=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Schedule -> dict -> Schedule
        dict_data = ScheduleSerializer.to_dict(original_schedule)
        restored_schedule = ScheduleSerializer.from_dict(dict_data)

        assert restored_schedule.id == original_schedule.id
        assert restored_schedule.name == original_schedule.name
        assert restored_schedule.task_name == original_schedule.task_name
        assert restored_schedule.cron_expression == original_schedule.cron_expression
        assert restored_schedule.enabled == original_schedule.enabled
        assert restored_schedule.args == original_schedule.args
        assert restored_schedule.kwargs == original_schedule.kwargs
        assert restored_schedule.description == original_schedule.description
        assert restored_schedule.category == original_schedule.category
        assert restored_schedule.tags == original_schedule.tags
        assert restored_schedule.execution_policy == original_schedule.execution_policy
        assert restored_schedule.auto_generated_name == original_schedule.auto_generated_name
        # 時刻の比較は秒単位で行う（マイクロ秒の誤差を許容）
        assert abs((restored_schedule.created_at - original_schedule.created_at).total_seconds()) < 0.001
        assert abs((restored_schedule.updated_at - original_schedule.updated_at).total_seconds()) < 0.001