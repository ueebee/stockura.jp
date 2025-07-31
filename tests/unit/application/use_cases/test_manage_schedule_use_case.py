"""ManageScheduleUseCase のユニットテスト"""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.application.dto.schedule_dto import (
    ScheduleCreateDto,
    ScheduleUpdateDto,
    TaskParamsDto
)
from app.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.domain.entities.schedule import Schedule
from tests.factories.schedule_factory import ScheduleFactory
from tests.utils.mock_helpers import MockRepositoryHelpers


class TestManageScheduleUseCase:
    """ManageScheduleUseCase のテストクラス"""

    @pytest.fixture
    def mock_schedule_repository(self):
        """スケジュールリポジトリのモック"""
        return MockRepositoryHelpers.create_mock_schedule_repository()

    @pytest.fixture
    def use_case(self, mock_schedule_repository):
        """テスト対象のユースケース"""
        return ManageScheduleUseCase(schedule_repository=mock_schedule_repository)

    @pytest.mark.asyncio
    async def test_create_schedule_success(self, use_case, mock_schedule_repository):
        """スケジュール作成成功のテスト"""
        # Arrange
        create_dto = ScheduleFactory.create_schedule_create_dto(
            name="test_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * *"
        )
        
        expected_schedule = ScheduleFactory.create_schedule_entity(
            name=create_dto.name,
            task_name=create_dto.task_name,
            cron_expression=create_dto.cron_expression
        )
        
        mock_schedule_repository.create.return_value = expected_schedule
        
        # Act
        result = await use_case.create_schedule(create_dto)
        
        # Assert
        assert result.name == create_dto.name
        assert result.task_name == create_dto.task_name
        assert result.cron_expression == create_dto.cron_expression
        assert result.enabled == create_dto.enabled
        
        # リポジトリが呼ばれたことを確認
        mock_schedule_repository.create.assert_called_once()
        created_schedule_arg = mock_schedule_repository.create.call_args[0][0]
        assert isinstance(created_schedule_arg, Schedule)
        assert created_schedule_arg.name == create_dto.name

    @pytest.mark.asyncio
    async def test_create_schedule_with_task_params(self, use_case, mock_schedule_repository):
        """タスクパラメータ付きスケジュール作成のテスト"""
        # Arrange
        task_params = TaskParamsDto(
            codes=["1301", "1305"],
            from_date="2024-01-01",
            to_date="2024-12-31"
        )
        
        create_dto = ScheduleFactory.create_schedule_create_dto(
            name="test_schedule_with_params",
            task_name="fetch_listed_info",
            task_params=task_params
        )
        
        expected_schedule = ScheduleFactory.create_schedule_entity(
            name=create_dto.name,
            task_name=create_dto.task_name
        )
        
        mock_schedule_repository.create.return_value = expected_schedule
        
        # Act
        result = await use_case.create_schedule(create_dto)
        
        # Assert
        mock_schedule_repository.create.assert_called_once()
        created_schedule_arg = mock_schedule_repository.create.call_args[0][0]
        
        # kwargs にタスクパラメータが含まれていることを確認
        assert "codes" in created_schedule_arg.kwargs
        assert created_schedule_arg.kwargs["codes"] == ["1301", "1305"]
        assert created_schedule_arg.kwargs["from_date"] == "2024-01-01"
        assert created_schedule_arg.kwargs["to_date"] == "2024-12-31"
        assert "schedule_id" in created_schedule_arg.kwargs

    @pytest.mark.asyncio
    async def test_get_schedule_success(self, use_case, mock_schedule_repository):
        """スケジュール取得成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        expected_schedule = ScheduleFactory.create_schedule_entity(
            id=schedule_id,
            name="test_schedule"
        )
        
        mock_schedule_repository.get_by_id.return_value = expected_schedule
        
        # Act
        result = await use_case.get_schedule(schedule_id)
        
        # Assert
        assert result is not None
        assert result.id == schedule_id
        assert result.name == expected_schedule.name
        mock_schedule_repository.get_by_id.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, use_case, mock_schedule_repository):
        """存在しないスケジュール取得のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_schedule_repository.get_by_id.return_value = None
        
        # Act
        result = await use_case.get_schedule(schedule_id)
        
        # Assert
        assert result is None
        mock_schedule_repository.get_by_id.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_get_all_schedules(self, use_case, mock_schedule_repository):
        """全スケジュール取得のテスト"""
        # Arrange
        schedules = [
            ScheduleFactory.create_schedule_entity(name="schedule1"),
            ScheduleFactory.create_schedule_entity(name="schedule2"),
            ScheduleFactory.create_schedule_entity(name="schedule3", enabled=False)
        ]
        
        mock_schedule_repository.get_all.return_value = schedules
        
        # Act
        result = await use_case.get_all_schedules(enabled_only=False)
        
        # Assert
        assert len(result) == 3
        assert result[0].name == "schedule1"
        assert result[1].name == "schedule2"
        assert result[2].name == "schedule3"
        mock_schedule_repository.get_all.assert_called_once_with(enabled_only=False)

    @pytest.mark.asyncio
    async def test_get_all_schedules_enabled_only(self, use_case, mock_schedule_repository):
        """有効なスケジュールのみ取得のテスト"""
        # Arrange
        enabled_schedules = [
            ScheduleFactory.create_schedule_entity(name="schedule1", enabled=True),
            ScheduleFactory.create_schedule_entity(name="schedule2", enabled=True)
        ]
        
        mock_schedule_repository.get_all.return_value = enabled_schedules
        
        # Act
        result = await use_case.get_all_schedules(enabled_only=True)
        
        # Assert
        assert len(result) == 2
        assert all(schedule.enabled for schedule in result)
        mock_schedule_repository.get_all.assert_called_once_with(enabled_only=True)

    @pytest.mark.asyncio
    async def test_update_schedule_success(self, use_case, mock_schedule_repository):
        """スケジュール更新成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        existing_schedule = ScheduleFactory.create_schedule_entity(
            id=schedule_id,
            name="old_name",
            cron_expression="0 0 * * *"
        )
        
        update_dto = ScheduleUpdateDto(
            name="new_name",
            cron_expression="0 9 * * *"
        )
        
        updated_schedule = ScheduleFactory.create_schedule_entity(
            id=schedule_id,
            name="new_name",
            cron_expression="0 9 * * *"
        )
        
        mock_schedule_repository.get_by_id.return_value = existing_schedule
        mock_schedule_repository.update.return_value = updated_schedule
        
        # Act
        result = await use_case.update_schedule(schedule_id, update_dto)
        
        # Assert
        assert result is not None
        assert result.name == "new_name"
        assert result.cron_expression == "0 9 * * *"
        
        mock_schedule_repository.get_by_id.assert_called_once_with(schedule_id)
        mock_schedule_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_schedule_not_found(self, use_case, mock_schedule_repository):
        """存在しないスケジュール更新のテスト"""
        # Arrange
        schedule_id = uuid4()
        update_dto = ScheduleUpdateDto(name="new_name")
        
        mock_schedule_repository.get_by_id.return_value = None
        
        # Act
        result = await use_case.update_schedule(schedule_id, update_dto)
        
        # Assert
        assert result is None
        mock_schedule_repository.get_by_id.assert_called_once_with(schedule_id)
        mock_schedule_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_schedule_success(self, use_case, mock_schedule_repository):
        """スケジュール削除成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_schedule_repository.delete.return_value = True
        
        # Act
        result = await use_case.delete_schedule(schedule_id)
        
        # Assert
        assert result is True
        mock_schedule_repository.delete.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_delete_schedule_not_found(self, use_case, mock_schedule_repository):
        """存在しないスケジュール削除のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_schedule_repository.delete.return_value = False
        
        # Act
        result = await use_case.delete_schedule(schedule_id)
        
        # Assert
        assert result is False
        mock_schedule_repository.delete.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_enable_schedule_success(self, use_case, mock_schedule_repository):
        """スケジュール有効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_schedule_repository.enable.return_value = True
        
        # Act
        result = await use_case.enable_schedule(schedule_id)
        
        # Assert
        assert result is True
        mock_schedule_repository.enable.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_disable_schedule_success(self, use_case, mock_schedule_repository):
        """スケジュール無効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_schedule_repository.disable.return_value = True
        
        # Act
        result = await use_case.disable_schedule(schedule_id)
        
        # Assert
        assert result is True
        mock_schedule_repository.disable.assert_called_once_with(schedule_id)