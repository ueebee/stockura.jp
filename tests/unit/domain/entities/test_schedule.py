"""Schedule エンティティのユニットテスト"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.entities.schedule import Schedule


class TestSchedule:
    """Schedule エンティティのテストクラス"""

    def test_create_minimal(self):
        """最小パラメータでの作成テスト"""
        # Arrange
        schedule_id = uuid4()
        
        # Act
        schedule = Schedule(
            id=schedule_id,
            name="test_schedule",
            task_name="test_task",
            cron_expression="0 0 * * *"
        )
        
        # Assert
        assert schedule.id == schedule_id
        assert schedule.name == "test_schedule"
        assert schedule.task_name == "test_task"
        assert schedule.cron_expression == "0 0 * * *"
        assert schedule.enabled is True
        assert schedule.args == []
        assert schedule.kwargs == {}
        assert schedule.description is None
        assert schedule.created_at is None
        assert schedule.updated_at is None

    def test_create_with_all_fields(self):
        """全フィールド指定での作成テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        args = ["arg1", "arg2"]
        kwargs = {"key1": "value1", "key2": "value2"}
        
        # Act
        schedule = Schedule(
            id=schedule_id,
            name="full_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * 1-5",
            enabled=False,
            args=args,
            kwargs=kwargs,
            description="Complete schedule",
            created_at=now,
            updated_at=now
        )
        
        # Assert
        assert schedule.id == schedule_id
        assert schedule.name == "full_schedule"
        assert schedule.task_name == "fetch_listed_info"
        assert schedule.cron_expression == "0 9 * * 1-5"
        assert schedule.enabled is False
        assert schedule.args == args
        assert schedule.kwargs == kwargs
        assert schedule.description == "Complete schedule"
        assert schedule.created_at == now
        assert schedule.updated_at == now

    def test_post_init_with_none_args_kwargs(self):
        """args/kwargs が None の場合の初期化テスト"""
        # Act
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            args=None,
            kwargs=None
        )
        
        # Assert
        assert schedule.args == []
        assert schedule.kwargs == {}

    def test_post_init_with_existing_args_kwargs(self):
        """args/kwargs が既存の場合の初期化テスト"""
        # Arrange
        existing_args = ["existing"]
        existing_kwargs = {"existing": "value"}
        
        # Act
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            args=existing_args,
            kwargs=existing_kwargs
        )
        
        # Assert
        assert schedule.args == existing_args
        assert schedule.kwargs == existing_kwargs

    def test_to_dict_minimal(self):
        """最小パラメータでの辞書変換テスト"""
        # Arrange
        schedule_id = uuid4()
        schedule = Schedule(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *"
        )
        
        # Act
        result = schedule.to_dict()
        
        # Assert
        assert result == {
            "id": str(schedule_id),
            "name": "test",
            "task_name": "test_task",
            "cron_expression": "0 0 * * *",
            "enabled": True,
            "args": [],
            "kwargs": {},
            "description": None,
            "created_at": None,
            "updated_at": None
        }

    def test_to_dict_with_all_fields(self):
        """全フィールドでの辞書変換テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        schedule = Schedule(
            id=schedule_id,
            name="full_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * *",
            enabled=False,
            args=["arg1", 123],
            kwargs={"key1": "value1", "key2": 456},
            description="Test description",
            created_at=now,
            updated_at=now
        )
        
        # Act
        result = schedule.to_dict()
        
        # Assert
        assert result == {
            "id": str(schedule_id),
            "name": "full_schedule",
            "task_name": "fetch_listed_info",
            "cron_expression": "0 9 * * *",
            "enabled": False,
            "args": ["arg1", 123],
            "kwargs": {"key1": "value1", "key2": 456},
            "description": "Test description",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

    def test_to_dict_preserves_complex_kwargs(self):
        """複雑な kwargs の辞書変換テスト"""
        # Arrange
        complex_kwargs = {
            "codes": ["1301", "1305", "7203"],
            "from_date": "2024-01-01",
            "to_date": "2024-12-31",
            "nested": {
                "level1": {
                    "level2": ["value1", "value2"]
                }
            }
        }
        
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="complex_task",
            cron_expression="0 0 * * *",
            kwargs=complex_kwargs
        )
        
        # Act
        result = schedule.to_dict()
        
        # Assert
        assert result["kwargs"] == complex_kwargs

    def test_equality(self):
        """等価性テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        
        schedule1 = Schedule(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            created_at=now,
            updated_at=now
        )
        
        schedule2 = Schedule(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            created_at=now,
            updated_at=now
        )
        
        schedule3 = Schedule(
            id=uuid4(),  # 異なる ID
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            created_at=now,
            updated_at=now
        )
        
        # Assert
        assert schedule1 == schedule2
        assert schedule1 != schedule3