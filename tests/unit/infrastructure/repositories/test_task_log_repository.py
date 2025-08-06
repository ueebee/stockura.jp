"""TaskLogRepository のユニットテスト"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.database.task_log_repository import TaskLogRepository
from app.infrastructure.database.models.task_log import TaskExecutionLog as DBTaskLog
from app.domain.entities.task_log import TaskExecutionLog
from tests.factories.task_log_factory import TaskLogFactory


class TestTaskLogRepository:
    """TaskLogRepository のテストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """テスト対象のリポジトリ"""
        return TaskLogRepository(mock_session)

    @pytest.fixture
    def sample_task_log_entity(self):
        """サンプルのタスクログエンティティ"""
        return TaskLogFactory.create_running_task_log(
            task_name="fetch_listed_info"
        )

    @pytest.fixture
    def sample_db_model(self, sample_task_log_entity):
        """サンプルの DB モデル"""
        return DBTaskLog(
            id=sample_task_log_entity.id,
            schedule_id=sample_task_log_entity.schedule_id,
            task_name=sample_task_log_entity.task_name,
            task_id=sample_task_log_entity.task_id,
            started_at=sample_task_log_entity.started_at,
            finished_at=sample_task_log_entity.finished_at,
            status=sample_task_log_entity.status,
            result=sample_task_log_entity.result,
            error_message=sample_task_log_entity.error_message,
            created_at=sample_task_log_entity.created_at
        )

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session, sample_task_log_entity):
        """タスクログ作成成功のテスト"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Act
        result = await repository.create(sample_task_log_entity)
        
        # Assert
        assert result.id == sample_task_log_entity.id
        assert result.task_name == sample_task_log_entity.task_name
        assert result.status == sample_task_log_entity.status
        
        # セッションのメソッドが呼ばれたことを確認
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_session, sample_db_model):
        """ID でタスクログ取得（見つかる場合）のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_by_id(sample_db_model.id)
        
        # Assert
        assert result is not None
        assert result.id == sample_db_model.id
        assert result.task_name == sample_db_model.task_name
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """ID でタスクログ取得（見つからない場合）のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_by_id(uuid4())
        
        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_task_id_found(self, repository, mock_session, sample_db_model):
        """Celery タスク ID でタスクログ取得（見つかる場合）のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_by_task_id(sample_db_model.task_id)
        
        # Assert
        assert result is not None
        assert result.task_id == sample_db_model.task_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_schedule_id(self, repository, mock_session):
        """スケジュール ID でタスクログ取得のテスト"""
        # Arrange
        schedule_id = uuid4()
        db_logs = [
            DBTaskLog(
                id=uuid4(),
                schedule_id=schedule_id,
                task_name="fetch_listed_info",
                task_id=f"task_{i}",
                started_at=datetime.now() - timedelta(hours=i),
                status="SUCCESS"
            )
            for i in range(3)
        ]
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = db_logs
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_by_schedule_id(schedule_id, limit=10)
        
        # Assert
        assert len(result) == 3
        assert all(isinstance(log, TaskExecutionLog) for log in result)
        assert all(log.schedule_id == schedule_id for log in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_logs_no_filter(self, repository, mock_session):
        """最近のタスクログ取得（フィルタなし）のテスト"""
        # Arrange
        db_logs = [
            DBTaskLog(
                id=uuid4(),
                schedule_id=uuid4(),
                task_name=f"task_{i}",
                task_id=f"task_id_{i}",
                started_at=datetime.now() - timedelta(hours=i),
                status=["SUCCESS", "FAILURE"][i % 2]
            )
            for i in range(5)
        ]
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = db_logs
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_recent_logs(limit=50)
        
        # Assert
        assert len(result) == 5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_logs_with_status_filter(self, repository, mock_session):
        """最近のタスクログ取得（ステータスフィルタあり）のテスト"""
        # Arrange
        success_logs = [
            DBTaskLog(
                id=uuid4(),
                schedule_id=uuid4(),
                task_name=f"task_{i}",
                task_id=f"task_id_{i}",
                started_at=datetime.now() - timedelta(hours=i),
                status="SUCCESS"
            )
            for i in range(3)
        ]
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = success_logs
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_recent_logs(
            limit=10, 
            status="SUCCESS"
        )
        
        # Assert
        assert len(result) == 3
        assert all(log.status == "SUCCESS" for log in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_logs_with_since_filter(self, repository, mock_session):
        """最近のタスクログ取得（日時フィルタあり）のテスト"""
        # Arrange
        since_date = datetime.now() - timedelta(hours=6)
        recent_logs = [
            DBTaskLog(
                id=uuid4(),
                schedule_id=uuid4(),
                task_name=f"task_{i}",
                task_id=f"task_id_{i}",
                started_at=datetime.now() - timedelta(hours=i),
                status="SUCCESS"
            )
            for i in range(3)  # 0, 1, 2 時間前
        ]
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = recent_logs
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_recent_logs(
            limit=20, 
            since=since_date
        )
        
        # Assert
        assert len(result) == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_success(self, repository, mock_session):
        """タスクステータス更新成功のテスト"""
        # Arrange
        log_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.update_status(
            log_id=log_id,
            status="SUCCESS",
            finished_at=datetime.now(),
            result={"message": "Task completed"}
        )
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_with_error(self, repository, mock_session):
        """エラー付きタスクステータス更新のテスト"""
        # Arrange
        log_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.update_status(
            log_id=log_id,
            status="FAILURE",
            finished_at=datetime.now(),
            error_message="Task failed with error"
        )
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, repository, mock_session):
        """存在しないタスクのステータス更新のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.update_status(
            log_id=uuid4(),
            status="SUCCESS"
        )
        
        # Assert
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_partial_update(self, repository, mock_session):
        """部分的なステータス更新のテスト"""
        # Arrange
        log_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act - ステータスのみ更新
        result = await repository.update_status(
            log_id=log_id,
            status="RUNNING"
        )
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()