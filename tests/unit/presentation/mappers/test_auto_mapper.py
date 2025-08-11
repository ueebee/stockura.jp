"""Tests for AutoMapper."""

import dataclasses
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

import pytest
from pydantic import BaseModel

from app.presentation.api.v1.mappers.auto_mapper import AutoMapper


# Test fixtures - Pydantic models
class PydanticTaskParams(BaseModel):
    """Test Pydantic model for task params."""
    period_type: str = "yesterday"
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    codes: Optional[List[str]] = None
    market: Optional[str] = None


class PydanticSchedule(BaseModel):
    """Test Pydantic model for schedule."""
    id: UUID
    name: str
    task_name: str
    enabled: bool = True
    description: Optional[str] = None
    created_at: datetime
    task_params: Optional[PydanticTaskParams] = None
    tags: List[str] = []


# Test fixtures - Dataclasses
@dataclasses.dataclass
class DataclassTaskParams:
    """Test dataclass for task params."""
    period_type: str = "yesterday"
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    codes: Optional[List[str]] = None
    market: Optional[str] = None


@dataclasses.dataclass
class DataclassSchedule:
    """Test dataclass for schedule."""
    id: UUID
    name: str
    task_name: str
    created_at: datetime
    enabled: bool = True
    description: Optional[str] = None
    task_params: Optional[DataclassTaskParams] = None
    tags: List[str] = dataclasses.field(default_factory=list)


class TestAutoMapper:
    """Test cases for AutoMapper."""

    def test_pydantic_to_dataclass_simple(self):
        """Test mapping from Pydantic model to dataclass with simple fields."""
        # Arrange
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        pydantic_obj = PydanticSchedule(
            id=test_uuid,
            name="Test Schedule",
            task_name="test_task",
            created_at=test_datetime,
        )
        
        # Act
        fields = AutoMapper.map_fields(pydantic_obj, DataclassSchedule)
        result = DataclassSchedule(**fields)
        
        # Assert
        assert result.id == test_uuid
        assert result.name == "Test Schedule"
        assert result.task_name == "test_task"
        assert result.created_at == test_datetime
        assert result.enabled is True  # Default value
        assert result.description is None
        assert result.tags == []

    def test_dataclass_to_pydantic_simple(self):
        """Test mapping from dataclass to Pydantic model with simple fields."""
        # Arrange
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        dataclass_obj = DataclassSchedule(
            id=test_uuid,
            name="Test Schedule",
            task_name="test_task",
            created_at=test_datetime,
        )
        
        # Act
        fields = AutoMapper.map_fields(dataclass_obj, PydanticSchedule)
        result = PydanticSchedule(**fields)
        
        # Assert
        assert result.id == test_uuid
        assert result.name == "Test Schedule"
        assert result.task_name == "test_task"
        assert result.created_at == test_datetime
        assert result.enabled is True
        assert result.description is None
        assert result.tags == []

    def test_mapping_with_optional_fields(self):
        """Test mapping with optional fields."""
        # Arrange
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        pydantic_obj = PydanticSchedule(
            id=test_uuid,
            name="Test Schedule",
            task_name="test_task",
            created_at=test_datetime,
            description="Test description",
            tags=["tag1", "tag2"],
        )
        
        # Act
        fields = AutoMapper.map_fields(pydantic_obj, DataclassSchedule)
        result = DataclassSchedule(**fields)
        
        # Assert
        assert result.description == "Test description"
        assert result.tags == ["tag1", "tag2"]

    def test_mapping_with_nested_objects(self):
        """Test mapping with nested objects."""
        # Arrange
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        task_params = PydanticTaskParams(
            period_type="custom",
            from_date="2024-01-01",
            to_date="2024-01-31",
            codes=["1234", "5678"],
            market="TSE",
        )
        pydantic_obj = PydanticSchedule(
            id=test_uuid,
            name="Test Schedule",
            task_name="test_task",
            created_at=test_datetime,
            task_params=task_params,
        )
        
        # Act
        fields = AutoMapper.map_fields(pydantic_obj, DataclassSchedule)
        # Note: Nested objects need custom handling, so task_params will be a dict
        
        # Assert
        assert "task_params" in fields
        assert isinstance(fields["task_params"], dict)
        assert fields["task_params"]["period_type"] == "custom"
        assert fields["task_params"]["from_date"] == "2024-01-01"

    def test_mapping_from_dict(self):
        """Test mapping from dictionary."""
        # Arrange
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        data_dict = {
            "id": test_uuid,
            "name": "Test Schedule",
            "task_name": "test_task",
            "created_at": test_datetime,
            "enabled": False,
        }
        
        # Act
        fields = AutoMapper.map_fields(data_dict, DataclassSchedule)
        result = DataclassSchedule(**fields)
        
        # Assert
        assert result.id == test_uuid
        assert result.name == "Test Schedule"
        assert result.task_name == "test_task"
        assert result.created_at == test_datetime
        assert result.enabled is False

    def test_type_conversion(self):
        """Test automatic type conversion."""
        # Arrange
        data_dict = {
            "id": "12345678-1234-5678-1234-567812345678",  # String UUID
            "name": "Test Schedule",
            "task_name": "test_task",
            "created_at": "2024-01-01T10:00:00",  # ISO format string
            "enabled": "true",  # String boolean
        }
        
        # Act
        fields = AutoMapper.map_fields(data_dict, PydanticSchedule)
        result = PydanticSchedule(**fields)
        
        # Assert
        assert isinstance(result.id, UUID)
        assert str(result.id) == "12345678-1234-5678-1234-567812345678"
        assert isinstance(result.created_at, datetime)
        assert result.enabled is True

    def test_missing_required_fields(self):
        """Test behavior when required fields are missing."""
        # Arrange
        data_dict = {
            "name": "Test Schedule",
            # Missing required fields: id, task_name, created_at
        }
        
        # Act
        fields = AutoMapper.map_fields(data_dict, DataclassSchedule)
        
        # Assert
        assert "name" in fields
        assert "id" not in fields
        assert "task_name" not in fields
        assert "created_at" not in fields

    def test_extra_fields_ignored(self):
        """Test that extra fields in source are ignored."""
        # Arrange
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        data_dict = {
            "id": test_uuid,
            "name": "Test Schedule",
            "task_name": "test_task",
            "created_at": test_datetime,
            "extra_field": "This should be ignored",
            "another_extra": 123,
        }
        
        # Act
        fields = AutoMapper.map_fields(data_dict, DataclassSchedule)
        
        # Assert
        assert "extra_field" not in fields
        assert "another_extra" not in fields
        assert len(fields) == 4  # Only mapped fields

    def test_none_values_handling(self):
        """Test handling of None values."""
        # Arrange
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        test_datetime = datetime.now()
        data_dict = {
            "id": test_uuid,
            "name": "Test Schedule",
            "task_name": "test_task",
            "created_at": test_datetime,
            "description": None,  # Explicitly None
            "task_params": None,  # Explicitly None
        }
        
        # Act
        fields = AutoMapper.map_fields(data_dict, DataclassSchedule)
        result = DataclassSchedule(**fields)
        
        # Assert
        assert result.description is None
        assert result.task_params is None