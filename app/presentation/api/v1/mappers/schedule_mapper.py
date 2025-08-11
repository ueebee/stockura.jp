"""Mapper for schedule-related conversions."""

from typing import List, Optional

from app.application.dtos.schedule_dto import (
    ScheduleCreateDto,
    ScheduleDto,
    ScheduleUpdateDto,
    TaskParamsDto,
)
from app.presentation.api.v1.mappers.auto_mapper import AutoMapper
from app.presentation.api.v1.mappers.base import BaseMapper
from app.presentation.api.v1.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
    TaskParams,
)


class TaskParamsMapper(BaseMapper[TaskParams, TaskParamsDto]):
    """Mapper for TaskParams conversions."""

    def schema_to_dto(self, schema: TaskParams) -> TaskParamsDto:
        """Convert TaskParams schema to DTO."""
        fields = AutoMapper.map_fields(schema, TaskParamsDto)
        return TaskParamsDto(**fields)

    def dto_to_schema(self, dto: TaskParamsDto) -> TaskParams:
        """Convert TaskParamsDto to schema."""
        fields = AutoMapper.map_fields(dto, TaskParams)
        return TaskParams(**fields)


class ScheduleCreateMapper(BaseMapper[ScheduleCreate, ScheduleCreateDto]):
    """Mapper for ScheduleCreate conversions."""

    def __init__(self):
        self.task_params_mapper = TaskParamsMapper()

    def schema_to_dto(self, schema: ScheduleCreate) -> ScheduleCreateDto:
        """Convert ScheduleCreate schema to DTO."""
        # Use auto mapper for most fields
        fields = AutoMapper.map_fields(schema, ScheduleCreateDto)
        
        # Handle nested task_params if present
        if schema.task_params:
            fields["task_params"] = self.task_params_mapper.schema_to_dto(schema.task_params)
        
        return ScheduleCreateDto(**fields)

    def dto_to_schema(self, dto: ScheduleCreateDto) -> ScheduleCreate:
        """Convert ScheduleCreateDto to schema."""
        # This conversion is not typically needed for create operations
        fields = AutoMapper.map_fields(dto, ScheduleCreate)
        
        if dto.task_params:
            fields["task_params"] = self.task_params_mapper.dto_to_schema(dto.task_params)
        
        return ScheduleCreate(**fields)


class ScheduleUpdateMapper(BaseMapper[ScheduleUpdate, ScheduleUpdateDto]):
    """Mapper for ScheduleUpdate conversions."""

    def __init__(self):
        self.task_params_mapper = TaskParamsMapper()

    def schema_to_dto(self, schema: ScheduleUpdate) -> ScheduleUpdateDto:
        """Convert ScheduleUpdate schema to DTO."""
        # Use auto mapper for most fields
        fields = AutoMapper.map_fields(schema, ScheduleUpdateDto)
        
        # Handle nested task_params if present
        if schema.task_params is not None:
            fields["task_params"] = self.task_params_mapper.schema_to_dto(schema.task_params)
        
        return ScheduleUpdateDto(**fields)

    def dto_to_schema(self, dto: ScheduleUpdateDto) -> ScheduleUpdate:
        """Convert ScheduleUpdateDto to schema."""
        # This conversion is not typically needed for update operations
        fields = AutoMapper.map_fields(dto, ScheduleUpdate)
        
        if dto.task_params is not None:
            fields["task_params"] = self.task_params_mapper.dto_to_schema(dto.task_params)
        
        return ScheduleUpdate(**fields)


class ScheduleResponseMapper(BaseMapper[ScheduleResponse, ScheduleDto]):
    """Mapper for ScheduleResponse conversions."""

    def __init__(self):
        self.task_params_mapper = TaskParamsMapper()

    def schema_to_dto(self, schema: ScheduleResponse) -> ScheduleDto:
        """Convert ScheduleResponse schema to DTO."""
        # This conversion is not typically needed
        fields = AutoMapper.map_fields(schema, ScheduleDto)
        
        if schema.task_params:
            fields["task_params"] = self.task_params_mapper.schema_to_dto(schema.task_params)
        
        return ScheduleDto(**fields)

    def dto_to_schema(self, dto: ScheduleDto) -> ScheduleResponse:
        """Convert ScheduleDto to ScheduleResponse schema."""
        # Use auto mapper for most fields
        fields = AutoMapper.map_fields(dto, ScheduleResponse)
        
        # Handle nested task_params if present
        if dto.task_params:
            fields["task_params"] = self.task_params_mapper.dto_to_schema(dto.task_params)
        
        return ScheduleResponse(**fields)


class ScheduleListResponseMapper:
    """Mapper for list of schedules."""

    def __init__(self):
        self.response_mapper = ScheduleResponseMapper()

    def dto_list_to_schema_list(self, dtos: List[ScheduleDto]) -> List[ScheduleResponse]:
        """Convert list of ScheduleDto to list of ScheduleResponse."""
        return [self.response_mapper.dto_to_schema(dto) for dto in dtos]