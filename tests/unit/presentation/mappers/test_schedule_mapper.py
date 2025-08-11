"""Tests for Schedule Mapper."""

from datetime import datetime
from uuid import UUID

import pytest

from app.application.dtos.schedule_dto import (
    ScheduleCreateDto,
    ScheduleDto,
    TaskParamsDto,
)
from app.presentation.api.v1.mappers.schedule_mapper import (
    ScheduleCreateMapper,
    ScheduleResponseMapper,
    TaskParamsMapper,
)
from app.presentation.api.v1.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    TaskParams,
)


class TestTaskParamsMapper:
    """Test cases for TaskParamsMapper."""

    def test_schema_to_dto(self):
        """Test converting TaskParams schema to DTO."""
        # Arrange
        mapper = TaskParamsMapper()
        schema = TaskParams(
            period_type="custom",
            from_date="2024-01-01",
            to_date="2024-01-31",
            codes=["1234", "5678"],
            market="TSE"
        )
        
        # Act
        dto = mapper.schema_to_dto(schema)
        
        # Assert
        assert isinstance(dto, TaskParamsDto)
        assert dto.period_type == "custom"
        assert dto.from_date == "2024-01-01"
        assert dto.to_date == "2024-01-31"
        assert dto.codes == ["1234", "5678"]
        assert dto.market == "TSE"

    def test_dto_to_schema(self):
        """Test converting TaskParamsDto to schema."""
        # Arrange
        mapper = TaskParamsMapper()
        dto = TaskParamsDto(
            period_type="yesterday",
            codes=["9999"]
        )
        
        # Act
        schema = mapper.dto_to_schema(dto)
        
        # Assert
        assert isinstance(schema, TaskParams)
        assert schema.period_type == "yesterday"
        assert schema.codes == ["9999"]
        assert schema.from_date is None
        assert schema.to_date is None
        assert schema.market is None


class TestScheduleCreateMapper:
    """Test cases for ScheduleCreateMapper."""

    def test_schema_to_dto_basic(self):
        """Test converting ScheduleCreate schema to DTO with basic fields."""
        # Arrange
        mapper = ScheduleCreateMapper()
        schema = ScheduleCreate(
            name="Test Schedule",
            task_name="test_task",
            cron_expression="0 9 * * *",
            enabled=True,
            description="Test description"
        )
        
        # Act
        dto = mapper.schema_to_dto(schema)
        
        # Assert
        assert isinstance(dto, ScheduleCreateDto)
        assert dto.name == "Test Schedule"
        assert dto.task_name == "test_task"
        assert dto.cron_expression == "0 9 * * *"
        assert dto.enabled is True
        assert dto.description == "Test description"
        assert dto.task_params is None

    def test_schema_to_dto_with_task_params(self):
        """Test converting ScheduleCreate schema to DTO with task params."""
        # Arrange
        mapper = ScheduleCreateMapper()
        schema = ScheduleCreate(
            name="Test Schedule",
            task_name="test_task",
            cron_expression="0 9 * * *",
            task_params=TaskParams(
                period_type="7days",
                market="TSE"
            ),
            category="data_fetch",
            tags=["daily", "jquants"],
            execution_policy="skip"
        )
        
        # Act
        dto = mapper.schema_to_dto(schema)
        
        # Assert
        assert isinstance(dto, ScheduleCreateDto)
        assert dto.name == "Test Schedule"
        assert dto.task_params is not None
        assert isinstance(dto.task_params, TaskParamsDto)
        assert dto.task_params.period_type == "7days"
        assert dto.task_params.market == "TSE"
        assert dto.category == "data_fetch"
        assert dto.tags == ["daily", "jquants"]
        assert dto.execution_policy == "skip"


class TestScheduleResponseMapper:
    """Test cases for ScheduleResponseMapper."""

    def test_dto_to_schema_basic(self):
        """Test converting ScheduleDto to ScheduleResponse schema."""
        # Arrange
        mapper = ScheduleResponseMapper()
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        
        dto = ScheduleDto(
            id=test_uuid,
            name="Test Schedule",
            task_name="test_task",
            cron_expression="0 9 * * *",
            enabled=True,
            description="Test description",
            created_at=test_datetime,
            updated_at=test_datetime,
            auto_generated_name=False
        )
        
        # Act
        schema = mapper.dto_to_schema(dto)
        
        # Assert
        assert isinstance(schema, ScheduleResponse)
        assert schema.id == test_uuid
        assert schema.name == "Test Schedule"
        assert schema.task_name == "test_task"
        assert schema.cron_expression == "0 9 * * *"
        assert schema.enabled is True
        assert schema.description == "Test description"
        assert schema.created_at == test_datetime
        assert schema.updated_at == test_datetime
        assert schema.auto_generated_name is False

    def test_dto_to_schema_with_task_params(self):
        """Test converting ScheduleDto to ScheduleResponse with task params."""
        # Arrange
        mapper = ScheduleResponseMapper()
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        
        dto = ScheduleDto(
            id=test_uuid,
            name="Test Schedule",
            task_name="test_task",
            cron_expression="0 9 * * *",
            enabled=True,
            description=None,
            created_at=test_datetime,
            updated_at=test_datetime,
            task_params=TaskParamsDto(
                period_type="custom",
                from_date="2024-01-01",
                to_date="2024-01-31"
            ),
            category="data_fetch",
            tags=["test", "demo"],
            execution_policy="allow"
        )
        
        # Act
        schema = mapper.dto_to_schema(dto)
        
        # Assert
        assert isinstance(schema, ScheduleResponse)
        assert schema.task_params is not None
        assert isinstance(schema.task_params, TaskParams)
        assert schema.task_params.period_type == "custom"
        assert schema.task_params.from_date == "2024-01-01"
        assert schema.task_params.to_date == "2024-01-31"
        assert schema.category == "data_fetch"
        assert schema.tags == ["test", "demo"]
        assert schema.execution_policy == "allow"