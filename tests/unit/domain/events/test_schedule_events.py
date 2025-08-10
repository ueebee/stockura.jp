"""Tests for schedule domain events."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.events.schedule_events import (
    ScheduleCreated,
    ScheduleUpdated,
    ScheduleDeleted,
    ScheduleEnabled,
    ScheduleDisabled,
    ScheduleExecuted,
    ScheduleExecutionFailed,
    ScheduleBulkCreated,
)


class TestScheduleEvents:
    """Schedule events tests."""
    
    def test_schedule_created_event(self):
        """ScheduleCreated イベントのテスト"""
        aggregate_id = uuid4()
        event = ScheduleCreated(
            aggregate_id=aggregate_id,
            schedule_name="test_schedule",
            task_name="test_task",
            cron_expression="0 9 * * *",
            enabled=True,
            category="test",
            tags=["tag1", "tag2"]
        )
        
        assert event.event_type == "schedule.created"
        assert event.aggregate_id == aggregate_id
        assert event.schedule_name == "test_schedule"
        assert event.task_name == "test_task"
        assert event.cron_expression == "0 9 * * *"
        assert event.enabled is True
        assert event.category == "test"
        assert event.tags == ["tag1", "tag2"]
        
        # to_dict のテスト
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "schedule.created"
        assert event_dict["schedule_name"] == "test_schedule"
        assert event_dict["task_name"] == "test_task"
        assert event_dict["tags"] == ["tag1", "tag2"]
    
    def test_schedule_updated_event(self):
        """ScheduleUpdated イベントのテスト"""
        changes = {
            "cron_expression": "0 10 * * *",
            "enabled": False
        }
        event = ScheduleUpdated(
            aggregate_id=uuid4(),
            schedule_name="test_schedule",
            changes=changes
        )
        
        assert event.event_type == "schedule.updated"
        assert event.schedule_name == "test_schedule"
        assert event.changes == changes
        
        event_dict = event.to_dict()
        assert event_dict["changes"] == changes
    
    def test_schedule_deleted_event(self):
        """ScheduleDeleted イベントのテスト"""
        event = ScheduleDeleted(
            aggregate_id=uuid4(),
            schedule_name="test_schedule"
        )
        
        assert event.event_type == "schedule.deleted"
        assert event.schedule_name == "test_schedule"
    
    def test_schedule_enabled_event(self):
        """ScheduleEnabled イベントのテスト"""
        event = ScheduleEnabled(
            aggregate_id=uuid4(),
            schedule_name="test_schedule"
        )
        
        assert event.event_type == "schedule.enabled"
        assert event.schedule_name == "test_schedule"
    
    def test_schedule_disabled_event(self):
        """ScheduleDisabled イベントのテスト"""
        event = ScheduleDisabled(
            aggregate_id=uuid4(),
            schedule_name="test_schedule",
            reason="Maintenance"
        )
        
        assert event.event_type == "schedule.disabled"
        assert event.schedule_name == "test_schedule"
        assert event.reason == "Maintenance"
    
    def test_schedule_executed_event(self):
        """ScheduleExecuted イベントのテスト"""
        exec_time = datetime.now()
        event = ScheduleExecuted(
            aggregate_id=uuid4(),
            schedule_name="test_schedule",
            task_name="test_task",
            execution_time=exec_time,
            task_id="task-123"
        )
        
        assert event.event_type == "schedule.executed"
        assert event.schedule_name == "test_schedule"
        assert event.task_name == "test_task"
        assert event.execution_time == exec_time
        assert event.task_id == "task-123"
        
        event_dict = event.to_dict()
        assert event_dict["execution_time"] == exec_time.isoformat()
    
    def test_schedule_execution_failed_event(self):
        """ScheduleExecutionFailed イベントのテスト"""
        exec_time = datetime.now()
        event = ScheduleExecutionFailed(
            aggregate_id=uuid4(),
            schedule_name="test_schedule",
            task_name="test_task",
            error_message="Connection timeout",
            execution_time=exec_time,
            task_id="task-123"
        )
        
        assert event.event_type == "schedule.execution_failed"
        assert event.schedule_name == "test_schedule"
        assert event.task_name == "test_task"
        assert event.error_message == "Connection timeout"
        assert event.execution_time == exec_time
        assert event.task_id == "task-123"
    
    def test_schedule_bulk_created_event(self):
        """ScheduleBulkCreated イベントのテスト"""
        schedule_names = ["schedule1", "schedule2", "schedule3"]
        event = ScheduleBulkCreated(
            aggregate_id=uuid4(),
            schedule_names=schedule_names,
            task_name="bulk_task",
            count=3
        )
        
        assert event.event_type == "schedule.bulk_created"
        assert event.schedule_names == schedule_names
        assert event.task_name == "bulk_task"
        assert event.count == 3
    
    def test_event_immutability(self):
        """イベントの不変性テスト"""
        event = ScheduleCreated(
            aggregate_id=uuid4(),
            schedule_name="test_schedule",
            task_name="test_task",
            cron_expression="0 9 * * *",
            tags=["tag1"]
        )
        
        # frozen=True により属性変更は不可
        with pytest.raises(AttributeError):
            event.schedule_name = "new_name"
        
        # リストも変更不可（frozen は浅いコピー）
        with pytest.raises(AttributeError):
            event.tags = ["new_tag"]