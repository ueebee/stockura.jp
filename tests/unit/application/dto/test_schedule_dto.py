"""Schedule DTO のユニットテスト"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.application.dtos.schedule_dto import (
    TaskParamsDto,
    ScheduleCreateDto,
    ScheduleUpdateDto,
    ScheduleDto
)


class TestTaskParamsDto:
    """TaskParamsDto のテストクラス"""

    def test_create_with_defaults(self):
        """デフォルト値での作成テスト"""
        # Act
        params = TaskParamsDto()
        
        # Assert
        assert params.period_type == "yesterday"
        assert params.from_date is None
        assert params.to_date is None
        assert params.codes is None
        assert params.market is None

    def test_create_with_all_params(self):
        """全パラメータ指定での作成テスト"""
        # Act
        params = TaskParamsDto(
            period_type="period",
            from_date="2024-01-01",
            to_date="2024-12-31",
            codes=["1301", "1305"],
            market="prime"
        )
        
        # Assert
        assert params.period_type == "period"
        assert params.from_date == "2024-01-01"
        assert params.to_date == "2024-12-31"
        assert params.codes == ["1301", "1305"]
        assert params.market == "prime"

    def test_to_kwargs_with_defaults(self):
        """デフォルト値での kwargs 変換テスト"""
        # Arrange
        params = TaskParamsDto()
        
        # Act
        kwargs = params.to_kwargs()
        
        # Assert
        assert kwargs == {"period_type": "yesterday"}

    def test_to_kwargs_with_all_params(self):
        """全パラメータでの kwargs 変換テスト"""
        # Arrange
        params = TaskParamsDto(
            period_type="period",
            from_date="2024-01-01",
            to_date="2024-12-31",
            codes=["1301", "1305"],
            market="prime"
        )
        
        # Act
        kwargs = params.to_kwargs()
        
        # Assert
        assert kwargs == {
            "period_type": "period",
            "from_date": "2024-01-01",
            "to_date": "2024-12-31",
            "codes": ["1301", "1305"],
            "market": "prime"
        }

    def test_to_kwargs_with_partial_params(self):
        """部分的なパラメータでの kwargs 変換テスト"""
        # Arrange
        params = TaskParamsDto(
            period_type="yesterday",
            codes=["7203"]
        )
        
        # Act
        kwargs = params.to_kwargs()
        
        # Assert
        assert kwargs == {
            "period_type": "yesterday",
            "codes": ["7203"]
        }

    def test_to_kwargs_with_none_values(self):
        """None 値を持つフィールドの to_kwargs メソッドテスト"""
        # Arrange
        params = TaskParamsDto(
            period_type="today",
            from_date=None,
            to_date=None,
            codes=None,
            market=None
        )
        
        # Act
        kwargs = params.to_kwargs()
        
        # Assert
        assert kwargs == {"period_type": "today"}
        # None 値のフィールドは除外される
        assert len(kwargs) == 1

    def test_to_kwargs_with_empty_codes_list(self):
        """空のコードリストの to_kwargs メソッドテスト"""
        # Arrange
        params = TaskParamsDto(
            period_type="yesterday",
            codes=[]
        )
        
        # Act
        kwargs = params.to_kwargs()
        
        # Assert
        # 空のリストは除外される（if self.codes: により）
        assert kwargs == {
            "period_type": "yesterday"
        }
        assert "codes" not in kwargs

    def test_to_kwargs_preserves_data_types(self):
        """to_kwargs がデータ型を保持することのテスト"""
        # Arrange
        codes_list = ["7203", "6758"]
        params = TaskParamsDto(
            period_type="custom",
            from_date="2024-01-01",
            codes=codes_list,
            market="TSE"
        )
        
        # Act
        kwargs = params.to_kwargs()
        
        # Assert
        assert isinstance(kwargs["period_type"], str)
        assert isinstance(kwargs["from_date"], str)
        assert isinstance(kwargs["codes"], list)
        # 注: 現在の実装では参照が渡される
        assert kwargs["codes"] is codes_list  # 参照として渡される
        assert kwargs["codes"] == codes_list  # 内容は同じ
        assert isinstance(kwargs["market"], str)


class TestScheduleCreateDto:
    """ScheduleCreateDto のテストクラス"""

    def test_create_minimal(self):
        """最小パラメータでの作成テスト"""
        # Act
        dto = ScheduleCreateDto(
            name="test_schedule",
            task_name="test_task",
            cron_expression="0 0 * * *"
        )
        
        # Assert
        assert dto.name == "test_schedule"
        assert dto.task_name == "test_task"
        assert dto.cron_expression == "0 0 * * *"
        assert dto.enabled is True
        assert dto.description is None
        assert dto.task_params is None

    def test_create_with_all_fields(self):
        """全フィールド指定での作成テスト"""
        # Arrange
        task_params = TaskParamsDto(codes=["1301"])
        
        # Act
        dto = ScheduleCreateDto(
            name="full_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * *",
            enabled=False,
            description="Test schedule with all fields",
            task_params=task_params
        )
        
        # Assert
        assert dto.name == "full_schedule"
        assert dto.task_name == "fetch_listed_info"
        assert dto.cron_expression == "0 9 * * *"
        assert dto.enabled is False
        assert dto.description == "Test schedule with all fields"
        assert dto.task_params == task_params


class TestScheduleUpdateDto:
    """ScheduleUpdateDto のテストクラス"""

    def test_create_empty(self):
        """空の更新 DTO 作成テスト"""
        # Act
        dto = ScheduleUpdateDto()
        
        # Assert
        assert dto.name is None
        assert dto.cron_expression is None
        assert dto.enabled is None
        assert dto.description is None
        assert dto.task_params is None

    def test_create_with_partial_fields(self):
        """部分的なフィールド更新テスト"""
        # Act
        dto = ScheduleUpdateDto(
            name="updated_name",
            enabled=False
        )
        
        # Assert
        assert dto.name == "updated_name"
        assert dto.cron_expression is None
        assert dto.enabled is False
        assert dto.description is None
        assert dto.task_params is None

    def test_create_with_all_fields(self):
        """全フィールド更新テスト"""
        # Arrange
        task_params = TaskParamsDto(market="growth")
        
        # Act
        dto = ScheduleUpdateDto(
            name="new_name",
            cron_expression="0 10 * * *",
            enabled=True,
            description="Updated description",
            task_params=task_params
        )
        
        # Assert
        assert dto.name == "new_name"
        assert dto.cron_expression == "0 10 * * *"
        assert dto.enabled is True
        assert dto.description == "Updated description"
        assert dto.task_params == task_params


class TestScheduleDto:
    """ScheduleDto のテストクラス"""

    def test_create_minimal(self):
        """最小パラメータでの作成テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        
        # Act
        dto = ScheduleDto(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            enabled=True,
            description=None,
            created_at=now,
            updated_at=now
        )
        
        # Assert
        assert dto.id == schedule_id
        assert dto.name == "test"
        assert dto.task_name == "test_task"
        assert dto.cron_expression == "0 0 * * *"
        assert dto.enabled is True
        assert dto.description is None
        assert dto.task_params is None
        assert dto.created_at == now
        assert dto.updated_at == now

    def test_create_with_all_fields(self):
        """全フィールド指定での作成テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        task_params = TaskParamsDto(
            period_type="period",
            from_date="2024-01-01",
            to_date="2024-12-31",
            codes=["1301", "1305"],
            market="prime"
        )
        
        # Act
        dto = ScheduleDto(
            id=schedule_id,
            name="full_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * 1-5",
            enabled=False,
            description="Complete schedule DTO",
            created_at=now,
            updated_at=now,
            task_params=task_params
        )
        
        # Assert
        assert dto.id == schedule_id
        assert dto.name == "full_schedule"
        assert dto.task_name == "fetch_listed_info"
        assert dto.cron_expression == "0 9 * * 1-5"
        assert dto.enabled is False
        assert dto.description == "Complete schedule DTO"
        assert dto.task_params == task_params
        assert dto.created_at == now
        assert dto.updated_at == now

    def test_equality(self):
        """等価性テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        
        dto1 = ScheduleDto(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            enabled=True,
            description=None,
            created_at=now,
            updated_at=now
        )
        
        dto2 = ScheduleDto(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            enabled=True,
            description=None,
            created_at=now,
            updated_at=now
        )
        
        # Assert
        assert dto1 == dto2