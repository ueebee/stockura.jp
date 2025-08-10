"""Schedule API エンドポイントのユニットテスト"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.presentation.api.v1.endpoints import schedules as schedules_module
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
from app.application.dtos.schedule_dto import ScheduleDto, TaskParamsDto
from tests.factories.schedule_factory import ScheduleFactory


class TestScheduleEndpoints:
    """Schedule エンドポイントのテストクラス"""

    @pytest.fixture
    def mock_use_case(self):
        """モック UseCase"""
        use_case = MagicMock()
        use_case.create_schedule = AsyncMock()
        use_case.get_all_schedules = AsyncMock()
        use_case.get_filtered_schedules = AsyncMock()
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
        create_data = {
            "name": "test_schedule",
            "task_name": "fetch_listed_info",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "description": "Test schedule",
            "task_params": {
                "period_type": "yesterday",
                "codes": ["1301", "1305"]
            }
        }
        
        mock_use_case.create_schedule.return_value = sample_schedule_dto
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.post("/schedules/", json=create_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(sample_schedule_dto.id)
        assert data["name"] == sample_schedule_dto.name
        assert data["task_name"] == sample_schedule_dto.task_name
        assert data["task_params"]["codes"] == ["1301", "1305"]
        mock_use_case.create_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_schedule_without_task_params(self, mock_use_case):
        """タスクパラメータなしでスケジュール作成のテスト"""
        # Arrange
        create_data = {
            "name": "simple_schedule",
            "task_name": "simple_task",
            "cron_expression": "0 0 * * *"
        }
        
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
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.post("/schedules/", json=create_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "simple_schedule"
        assert data["task_params"]["period_type"] == "yesterday"  # デフォルト値
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
                category=None,
                tags=[],
                execution_policy="allow",
                auto_generated_name=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                task_params=None
            )
            for i in range(3)
        ]
        
        # AsyncMock を使用
        mock_use_case.get_all_schedules = AsyncMock(return_value=schedules)
        
        # Act
        # FastAPI の override_dependency を使用
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        # TestClient で呼び出す
        with TestClient(app) as client:
            response = client.get("/schedules?enabled_only=false")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["items"][0]["name"] == "schedule_0"
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
                category=None,
                tags=[],
                execution_policy="allow",
                auto_generated_name=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                task_params=None
            )
            for i in range(2)
        ]
        
        # AsyncMock を使用
        mock_use_case.get_all_schedules = AsyncMock(return_value=enabled_schedules)
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.get("/schedules?enabled_only=true")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["enabled"] for item in data["items"])
        mock_use_case.get_all_schedules.assert_called_once_with(enabled_only=True)

    @pytest.mark.asyncio
    async def test_get_schedule_success(self, mock_use_case, sample_schedule_dto):
        """スケジュール取得成功のテスト"""
        # Arrange
        schedule_id = sample_schedule_dto.id
        mock_use_case.get_schedule.return_value = sample_schedule_dto
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.get(f"/schedules/{schedule_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(schedule_id)
        assert data["name"] == sample_schedule_dto.name
        mock_use_case.get_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール取得のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.get_schedule.return_value = None
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.get(f"/schedules/{schedule_id}")
        
        # Assert
        assert response.status_code == 404
        assert f"Schedule {schedule_id} not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_schedule_success(self, mock_use_case, sample_schedule_dto):
        """スケジュール更新成功のテスト"""
        # Arrange
        schedule_id = sample_schedule_dto.id
        update_data = {
            "name": "updated_schedule",
            "cron_expression": "0 10 * * *",
            "enabled": False
        }
        
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
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.put(f"/schedules/{schedule_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated_schedule"
        assert data["cron_expression"] == "0 10 * * *"
        assert data["enabled"] is False
        mock_use_case.update_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール更新のテスト"""
        # Arrange
        schedule_id = uuid4()
        update_data = {
            "name": "updated"
        }
        mock_use_case.update_schedule.return_value = None
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.put(f"/schedules/{schedule_id}", json=update_data)
        
        # Assert
        assert response.status_code == 404
        assert f"Schedule {schedule_id} not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_schedule_success(self, mock_use_case):
        """スケジュール削除成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.delete_schedule.return_value = True
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.delete(f"/schedules/{schedule_id}")
        
        # Assert
        assert response.status_code == 204
        mock_use_case.delete_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_delete_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール削除のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.delete_schedule.return_value = False
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.delete(f"/schedules/{schedule_id}")
        
        # Assert
        assert response.status_code == 404
        assert f"Schedule {schedule_id} not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_enable_schedule_success(self, mock_use_case):
        """スケジュール有効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.enable_schedule.return_value = True
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.post(f"/schedules/{schedule_id}/enable")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(schedule_id)
        assert data["enabled"] is True
        assert "enabled successfully" in data["message"]
        mock_use_case.enable_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_enable_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール有効化のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.enable_schedule.return_value = False
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.post(f"/schedules/{schedule_id}/enable")
        
        # Assert
        assert response.status_code == 404
        assert f"Schedule {schedule_id} not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_disable_schedule_success(self, mock_use_case):
        """スケジュール無効化成功のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.disable_schedule.return_value = True
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.post(f"/schedules/{schedule_id}/disable")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(schedule_id)
        assert data["enabled"] is False
        assert "disabled successfully" in data["message"]
        mock_use_case.disable_schedule.assert_called_once_with(schedule_id)

    @pytest.mark.asyncio
    async def test_disable_schedule_not_found(self, mock_use_case):
        """存在しないスケジュール無効化のテスト"""
        # Arrange
        schedule_id = uuid4()
        mock_use_case.disable_schedule.return_value = False
        
        # Act
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(schedules_module.router)
        app.dependency_overrides[get_manage_schedule_use_case] = lambda: mock_use_case
        
        with TestClient(app) as client:
            response = client.post(f"/schedules/{schedule_id}/disable")
        
        # Assert
        assert response.status_code == 404
        assert f"Schedule {schedule_id} not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_manage_schedule_use_case(self):
        """UseCase 取得のテスト"""
        # Arrange
        mock_session = AsyncMock()
        
        # Act
        with patch('app.presentation.api.v1.endpoints.schedules.ScheduleRepositoryImpl') as mock_repo_class:
            mock_repo_class.return_value = MagicMock()
            use_case = await get_manage_schedule_use_case(mock_session)
        
        # Assert
        assert use_case is not None
        mock_repo_class.assert_called_once_with(mock_session)