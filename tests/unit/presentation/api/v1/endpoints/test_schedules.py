"""Schedule API エンドポイントのユニットテスト"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.presentation.api.v1.endpoints.schedules import (
    create_schedule,
    list_schedules,
    get_schedule,
    update_schedule,
    delete_schedule,
    enable_schedule,
    disable_schedule,
    get_manage_schedule_use_case
)
from app.presentation.api.v1.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    TaskParams
)
from app.application.dto.schedule_dto import ScheduleDto, TaskParamsDto
from tests.factories.schedule_factory import ScheduleFactory


class TestScheduleEndpoints:
    """Schedule エンドポイントのテストクラス"""

    @pytest.fixture
    def mock_use_case(self):
        """モック UseCase"""
        use_case = MagicMock()
        use_case.create_schedule = AsyncMock()
        use_case.get_all_schedules = AsyncMock()
        use_case.get_schedule = AsyncMock()
        use_case.update_schedule = AsyncMock()
        use_case.delete_schedule = AsyncMock()
        use_case.enable_schedule = AsyncMock()
        use_case.disable_schedule = AsyncMock()
        return use_case

    @pytest.fixture
    def sample_schedule_dto(self):
        """サンプルの ScheduleDto"""
        return ScheduleDto(
            id=uuid4(),
            name="test_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * *",
            enabled=True,
            description="Test schedule",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            task_params=TaskParamsDto(
                period_type="yesterday",
                codes=["1301", "1305"]
            )
        )

    @pytest.mark.asyncio
    async def test_create_schedule_success(self, mock_use_case, sample_schedule_dto):
        """スケジュール作成成功のテスト"""
        # Arrange
        create_data = ScheduleCreate(
            name="test_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * *",
            enabled=True,
            description="Test schedule",
            task_params=TaskParams(
                period_type="yesterday",
                codes=["1301", "1305"]
            )
        )
        
        mock_use_case.create_schedule.return_value = sample_schedule_dto
        
        # Act
        with patch('app.presentation.api.v1.endpoints.schedules.get_manage_schedule_use_case', return_value=mock_use_case):
            result = await create_schedule(create_data, mock_use_case)
        
        # Assert
        assert result.id == sample_schedule_dto.id
        assert result.name == sample_schedule_dto.name
        assert result.task_name == sample_schedule_dto.task_name
        assert result.task_params.codes == ["1301", "1305"]
        mock_use_case.create_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_schedule_without_task_params(self, mock_use_case):
        """タスクパラメータなしでスケジュール作成のテスト"""
        # Arrange
        create_data = ScheduleCreate(
            name="simple_schedule",
            task_name="simple_task",
            cron_expression="0 0 * * *"
        )
        
        schedule_dto = ScheduleDto(
            id=uuid4(),
            name="simple_schedule",
            task_name="simple_task",
            cron_expression="0 0 * * *",
            enabled=True,
            description=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            task_params=None
        )
        
        mock_use_case.create_schedule.return_value = schedule_dto
        
        # Act
        result = await create_schedule(create_data, mock_use_case)
        
        # Assert
        assert result.name == "simple_schedule"
        assert result.task_params.period_type == "yesterday"  # デフォルト値
        mock_use_case.create_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_schedules_all(self, mock_use_case):
        """全スケジュール一覧取得のテスト"""
        # Arrange
        schedules = [
            ScheduleDto(
                id=uuid4(),
                name=f"schedule_{i}",
                task_name="task",
                cron_expression="0 0 * * *",
                enabled=i % 2 == 0,
                description=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                task_params=None
            )
            for i in range(3)
        ]
        
        mock_use_case.get_all_schedules.return_value = schedules
        
        # Act
        result = await list_schedules(enabled_only=False, use_case=mock_use_case)
        
        # Assert
        assert result.total == 3
        assert len(result.items) == 3
        assert result.items[0].name == "schedule_0"
        mock_use_case.get_all_schedules.assert_called_once_with(enabled_only=False)

    @pytest.mark.asyncio
    async def test_list_schedules_enabled_only(self, mock_use_case):
        """有効なスケジュールのみ一覧取得のテスト"""
        # Arrange
        enabled_schedules = [
            ScheduleDto(
                id=uuid4(),
                name=f"enabled_schedule_{i}",
                task_name="task",
                cron_expression="0 0 * * *",
                enabled=True,
                description=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                task_params=None
            )
            for i in range(2)
        ]
        
        mock_use_case.get_all_schedules.return_value = enabled_schedules
        
        # Act
        result = await list_schedules(enabled_only=True, use_case=mock_use_case)
        
        # Assert
        assert result.total == 2
        assert all(item.enabled for item in result.items)
        mock_use_case.get_all_schedules.assert_called_once_with(enabled_only=True)

    @pytest.mark.asyncio
    async def test_get_schedule_success(self, mock_use_case, sample_schedule_dto):
        """スケジュール取得成功のテスト"""
        # Arrange
        schedule_id = sample_schedule_dto.id
        mock_use_case.get_schedule.return_value = sample_schedule_dto
        
        # Act
        result = await get_schedule(schedule_id, mock_use_case)
        
        # Assert
        assert result.id == schedule_id
        assert result.name == sample_schedule_dto.name
        mock_use_case.get_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール取得のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.get_schedule.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_schedule(schedule_id, mock_use_case)
        
        assert exc_info.value.status_code == 404
        assert f"Schedule {schedule_id} not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_schedule_success(self, mock_use_case, sample_schedule_dto):
        """スケジュール更新成功のテスト"""
        # Arrange
        schedule_id = sample_schedule_dto.id
        update_data = ScheduleUpdate(
            name="updated_schedule",
            cron_expression="0 10 * * *",
            enabled=False
        )
        
        updated_dto = ScheduleDto(
            id=schedule_id,
            name="updated_schedule",
            task_name=sample_schedule_dto.task_name,
            cron_expression="0 10 * * *",
            enabled=False,
            description=sample_schedule_dto.description,
            created_at=sample_schedule_dto.created_at,
            updated_at=datetime.now(),
            task_params=sample_schedule_dto.task_params
        )
        
        mock_use_case.update_schedule.return_value = updated_dto
        
        # Act
        result = await update_schedule(schedule_id, update_data, mock_use_case)
        
        # Assert
        assert result.name == "updated_schedule"
        assert result.cron_expression == "0 10 * * *"
        assert result.enabled is False
        mock_use_case.update_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール更新のテスト"""
        # Arrange
        schedule_id = uuid4()
        update_data = ScheduleUpdate(name="updated")
        mock_use_case.update_schedule.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_schedule(schedule_id, update_data, mock_use_case)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_schedule_success(self, mock_use_case):
        """スケジュール削除成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.delete_schedule.return_value = True
        
        # Act
        result = await delete_schedule(schedule_id, mock_use_case)
        
        # Assert
        assert result is None
        mock_use_case.delete_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_delete_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール削除のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.delete_schedule.return_value = False
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_schedule(schedule_id, mock_use_case)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_enable_schedule_success(self, mock_use_case):
        """スケジュール有効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.enable_schedule.return_value = True
        
        # Act
        result = await enable_schedule(schedule_id, mock_use_case)
        
        # Assert
        assert result.id == schedule_id
        assert result.enabled is True
        assert "enabled successfully" in result.message
        mock_use_case.enable_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_enable_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール有効化のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.enable_schedule.return_value = False
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await enable_schedule(schedule_id, mock_use_case)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_disable_schedule_success(self, mock_use_case):
        """スケジュール無効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.disable_schedule.return_value = True
        
        # Act
        result = await disable_schedule(schedule_id, mock_use_case)
        
        # Assert
        assert result.id == schedule_id
        assert result.enabled is False
        assert "disabled successfully" in result.message
        mock_use_case.disable_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_disable_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール無効化のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.disable_schedule.return_value = False
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await disable_schedule(schedule_id, mock_use_case)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_manage_schedule_use_case(self):
        """UseCase 取得のテスト"""
        # Arrange
        mock_session = AsyncMock()
        
        # Act
        with patch('app.presentation.api.v1.endpoints.schedules.ScheduleRepository') as mock_repo_class:
            mock_repo_class.return_value = MagicMock()
            use_case = await get_manage_schedule_use_case(mock_session)
        
        # Assert
        assert use_case is not None
        mock_repo_class.assert_called_once_with(mock_session)