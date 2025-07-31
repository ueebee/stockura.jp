"""TaskExecutionLog エンティティのユニットテスト"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.entities.task_log import TaskExecutionLog


class TestTaskExecutionLog:
    """TaskExecutionLog エンティティのテストクラス"""

    def test_create_minimal(self):
        """最小パラメータでの作成テスト"""
        # Arrange
        log_id = uuid4()
        task_name = "test_task"
        started_at = datetime.now()
        
        # Act
        log = TaskExecutionLog(
            id=log_id,
            task_name=task_name,
            started_at=started_at,
            status="running"
        )
        
        # Assert
        assert log.id == log_id
        assert log.task_name == task_name
        assert log.started_at == started_at
        assert log.status == "running"
        assert log.schedule_id is None
        assert log.task_id is None
        assert log.finished_at is None
        assert log.result is None
        assert log.error_message is None
        assert log.created_at is None

    def test_create_with_all_fields(self):
        """全フィールド指定での作成テスト"""
        # Arrange
        log_id = uuid4()
        schedule_id = uuid4()
        task_id = "celery_task_123"
        task_name = "fetch_listed_info"
        started_at = datetime.now()
        finished_at = started_at + timedelta(minutes=5)
        result = {"processed": 100, "failed": 0}
        created_at = started_at - timedelta(seconds=1)
        
        # Act
        log = TaskExecutionLog(
            id=log_id,
            task_name=task_name,
            started_at=started_at,
            status="success",
            schedule_id=schedule_id,
            task_id=task_id,
            finished_at=finished_at,
            result=result,
            error_message=None,
            created_at=created_at
        )
        
        # Assert
        assert log.id == log_id
        assert log.task_name == task_name
        assert log.started_at == started_at
        assert log.status == "success"
        assert log.schedule_id == schedule_id
        assert log.task_id == task_id
        assert log.finished_at == finished_at
        assert log.result == result
        assert log.error_message is None
        assert log.created_at == created_at

    def test_create_failed_task(self):
        """失敗タスクの作成テスト"""
        # Arrange
        log_id = uuid4()
        started_at = datetime.now()
        finished_at = started_at + timedelta(seconds=30)
        error_message = "Connection timeout"
        
        # Act
        log = TaskExecutionLog(
            id=log_id,
            task_name="failed_task",
            started_at=started_at,
            status="failed",
            finished_at=finished_at,
            error_message=error_message
        )
        
        # Assert
        assert log.status == "failed"
        assert log.error_message == error_message
        assert log.result is None

    def test_to_dict_minimal(self):
        """最小パラメータでの辞書変換テスト"""
        # Arrange
        log_id = uuid4()
        started_at = datetime.now()
        log = TaskExecutionLog(
            id=log_id,
            task_name="test_task",
            started_at=started_at,
            status="running"
        )
        
        # Act
        result = log.to_dict()
        
        # Assert
        assert result == {
            "id": str(log_id),
            "schedule_id": None,
            "task_name": "test_task",
            "task_id": None,
            "started_at": started_at.isoformat(),
            "finished_at": None,
            "status": "running",
            "result": None,
            "error_message": None,
            "created_at": None
        }

    def test_to_dict_with_all_fields(self):
        """全フィールドでの辞書変換テスト"""
        # Arrange
        log_id = uuid4()
        schedule_id = uuid4()
        started_at = datetime.now()
        finished_at = started_at + timedelta(minutes=2)
        created_at = started_at - timedelta(seconds=1)
        result_data = {"count": 50, "status": "completed"}
        
        log = TaskExecutionLog(
            id=log_id,
            task_name="complete_task",
            started_at=started_at,
            status="success",
            schedule_id=schedule_id,
            task_id="task_abc123",
            finished_at=finished_at,
            result=result_data,
            created_at=created_at
        )
        
        # Act
        result = log.to_dict()
        
        # Assert
        assert result == {
            "id": str(log_id),
            "schedule_id": str(schedule_id),
            "task_name": "complete_task",
            "task_id": "task_abc123",
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "status": "success",
            "result": result_data,
            "error_message": None,
            "created_at": created_at.isoformat()
        }

    def test_duration_seconds_completed_task(self):
        """完了タスクの実行時間計算テスト"""
        # Arrange
        started_at = datetime.now()
        finished_at = started_at + timedelta(minutes=3, seconds=30)
        
        log = TaskExecutionLog(
            id=uuid4(),
            task_name="test",
            started_at=started_at,
            status="success",
            finished_at=finished_at
        )
        
        # Act
        duration = log.duration_seconds
        
        # Assert
        assert duration == 210.0  # 3 分 30 秒 = 210 秒

    def test_duration_seconds_running_task(self):
        """実行中タスクの実行時間計算テスト"""
        # Arrange
        log = TaskExecutionLog(
            id=uuid4(),
            task_name="running_task",
            started_at=datetime.now(),
            status="running"
        )
        
        # Act
        duration = log.duration_seconds
        
        # Assert
        assert duration is None

    def test_duration_seconds_no_started_at(self):
        """開始時刻なしタスクの実行時間計算テスト"""
        # Arrange
        log = TaskExecutionLog(
            id=uuid4(),
            task_name="test",
            started_at=datetime.now(),
            status="pending"
        )
        log.finished_at = datetime.now()
        log.started_at = None  # 開始時刻を None に設定
        
        # Act
        duration = log.duration_seconds
        
        # Assert
        assert duration is None

    def test_duration_seconds_precise(self):
        """実行時間の精密計算テスト"""
        # Arrange
        started_at = datetime(2024, 1, 1, 10, 0, 0)
        finished_at = datetime(2024, 1, 1, 10, 5, 30, 500000)  # 5 分 30.5 秒後
        
        log = TaskExecutionLog(
            id=uuid4(),
            task_name="precise_task",
            started_at=started_at,
            status="success",
            finished_at=finished_at
        )
        
        # Act
        duration = log.duration_seconds
        
        # Assert
        assert duration == 330.5  # 5 分 30.5 秒

    def test_status_values(self):
        """ステータス値のテスト"""
        # Arrange & Act
        running_log = TaskExecutionLog(
            id=uuid4(),
            task_name="test",
            started_at=datetime.now(),
            status="running"
        )
        
        success_log = TaskExecutionLog(
            id=uuid4(),
            task_name="test",
            started_at=datetime.now(),
            status="success"
        )
        
        failed_log = TaskExecutionLog(
            id=uuid4(),
            task_name="test",
            started_at=datetime.now(),
            status="failed"
        )
        
        # Assert
        assert running_log.status == "running"
        assert success_log.status == "success"
        assert failed_log.status == "failed"

    def test_equality(self):
        """等価性テスト"""
        # Arrange
        log_id = uuid4()
        started_at = datetime.now()
        
        log1 = TaskExecutionLog(
            id=log_id,
            task_name="test",
            started_at=started_at,
            status="running"
        )
        
        log2 = TaskExecutionLog(
            id=log_id,
            task_name="test",
            started_at=started_at,
            status="running"
        )
        
        log3 = TaskExecutionLog(
            id=uuid4(),  # 異なる ID
            task_name="test",
            started_at=started_at,
            status="running"
        )
        
        # Assert
        assert log1 == log2
        assert log1 != log3