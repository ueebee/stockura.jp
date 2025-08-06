"""ScheduleRepository のユニットテスト"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Result

from app.infrastructure.repositories.database.schedule_repository import ScheduleRepository
from app.infrastructure.database.models.schedule import CeleryBeatSchedule
from app.domain.entities.schedule import Schedule
from tests.factories.schedule_factory import ScheduleFactory


class TestScheduleRepository:
    """ScheduleRepository のテストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """テスト対象のリポジトリ"""
        return ScheduleRepository(mock_session)

    @pytest.fixture
    def sample_schedule_entity(self):
        """サンプルのスケジュールエンティティ"""
        return ScheduleFactory.create_schedule_entity(
            name="test_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * *"
        )

    @pytest.fixture
    def sample_db_model(self, sample_schedule_entity):
        """サンプルの DB モデル"""
        return CeleryBeatSchedule(
            id=sample_schedule_entity.id,
            name=sample_schedule_entity.name,
            task_name=sample_schedule_entity.task_name,
            cron_expression=sample_schedule_entity.cron_expression,
            enabled=sample_schedule_entity.enabled,
            args=sample_schedule_entity.args,
            kwargs=sample_schedule_entity.kwargs,
            description=sample_schedule_entity.description,
            created_at=sample_schedule_entity.created_at,
            updated_at=sample_schedule_entity.updated_at
        )

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session, sample_schedule_entity, sample_db_model):
        """スケジュール作成成功のテスト"""
        # Arrange
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Act
        result = await repository.create(sample_schedule_entity)
        
        # Assert
        assert result.id == sample_schedule_entity.id
        assert result.name == sample_schedule_entity.name
        assert result.task_name == sample_schedule_entity.task_name
        
        # セッションのメソッドが呼ばれたことを確認
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_session, sample_db_model):
        """ID でスケジュール取得（見つかる場合）のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_by_id(sample_db_model.id)
        
        # Assert
        assert result is not None
        assert result.id == sample_db_model.id
        assert result.name == sample_db_model.name
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """ID でスケジュール取得（見つからない場合）のテスト"""
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
    async def test_get_by_name_found(self, repository, mock_session, sample_db_model):
        """名前でスケジュール取得（見つかる場合）のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_by_name(sample_db_model.name)
        
        # Assert
        assert result is not None
        assert result.name == sample_db_model.name
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_without_filter(self, repository, mock_session):
        """全スケジュール取得（フィルタなし）のテスト"""
        # Arrange
        db_models = [
            CeleryBeatSchedule(
                id=uuid4(),
                name=f"schedule_{i}",
                task_name="task",
                cron_expression="0 0 * * *",
                enabled=i % 2 == 0
            )
            for i in range(3)
        ]
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = db_models
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_all(enabled_only=False)
        
        # Assert
        assert len(result) == 3
        assert all(isinstance(s, Schedule) for s in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_enabled_only(self, repository, mock_session):
        """有効なスケジュールのみ取得のテスト"""
        # Arrange
        enabled_models = [
            CeleryBeatSchedule(
                id=uuid4(),
                name=f"enabled_schedule_{i}",
                task_name="task",
                cron_expression="0 0 * * *",
                enabled=True
            )
            for i in range(2)
        ]
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = enabled_models
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.get_all(enabled_only=True)
        
        # Assert
        assert len(result) == 2
        assert all(s.enabled for s in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_session, sample_schedule_entity):
        """スケジュール更新成功のテスト"""
        # Arrange
        updated_entity = Schedule(
            id=sample_schedule_entity.id,
            name="updated_name",
            task_name=sample_schedule_entity.task_name,
            cron_expression="0 10 * * *",
            enabled=False,
            args=sample_schedule_entity.args,
            kwargs=sample_schedule_entity.kwargs,
            description="Updated description"
        )
        
        # update の実行結果をモック
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        
        # get_by_id の呼び出しをモック
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = CeleryBeatSchedule(
            id=updated_entity.id,
            name=updated_entity.name,
            task_name=updated_entity.task_name,
            cron_expression=updated_entity.cron_expression,
            enabled=updated_entity.enabled,
            args=updated_entity.args,
            kwargs=updated_entity.kwargs,
            description=updated_entity.description
        )
        # 2 回目の execute 呼び出し（get_by_id）
        mock_session.execute.side_effect = [None, mock_result]
        
        # Act
        result = await repository.update(updated_entity)
        
        # Assert
        assert result.name == "updated_name"
        assert result.cron_expression == "0 10 * * *"
        assert result.enabled is False
        assert mock_session.execute.call_count == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self, repository, mock_session, sample_db_model):
        """スケジュール削除成功のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.delete(sample_db_model.id)
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.delete.assert_called_once_with(sample_db_model)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_session):
        """存在しないスケジュール削除のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repository.delete(uuid4())
        
        # Assert
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_enable_success(self, repository, mock_session):
        """スケジュール有効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.enable(schedule_id)
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_not_found(self, repository, mock_session):
        """存在しないスケジュール有効化のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.enable(uuid4())
        
        # Assert
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_success(self, repository, mock_session):
        """スケジュール無効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.disable(schedule_id)
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_not_found(self, repository, mock_session):
        """存在しないスケジュール無効化のテスト"""
        # Arrange
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        # Act
        result = await repository.disable(uuid4())
        
        # Assert
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()