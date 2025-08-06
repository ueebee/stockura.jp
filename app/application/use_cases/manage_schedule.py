"""Schedule management use case."""
from typing import List, Optional
from uuid import UUID, uuid4

from app.application.dtos.schedule_dto import (
    ScheduleCreateDto,
    ScheduleDto,
    ScheduleUpdateDto,
    TaskParamsDto,
)
from app.domain.entities.schedule import Schedule
from app.domain.repositories.schedule_repository_interface import (
    ScheduleRepositoryInterface,
)


class ManageScheduleUseCase:
    """Use case for managing schedules."""

    def __init__(self, schedule_repository: ScheduleRepositoryInterface):
        """Initialize use case."""
        self._schedule_repository = schedule_repository

    async def create_schedule(self, dto: ScheduleCreateDto) -> ScheduleDto:
        """Create a new schedule."""
        # Convert task params to args/kwargs
        args = []
        kwargs = {}
        
        if dto.task_params:
            kwargs = dto.task_params.to_kwargs()
            
        # Add schedule_id to kwargs
        schedule_id = uuid4()
        kwargs["schedule_id"] = str(schedule_id)
        
        # Generate name if not provided
        name = dto.name
        auto_generated_name = False
        if not name:
            # Simple name generation (will be improved in Phase 2)
            name = f"{dto.task_name}_{schedule_id.hex[:8]}"
            auto_generated_name = True
        
        # Create schedule entity
        schedule = Schedule(
            id=schedule_id,
            name=name,
            task_name=dto.task_name,
            cron_expression=dto.cron_expression,
            enabled=dto.enabled,
            args=args,
            kwargs=kwargs,
            description=dto.description,
            category=dto.category,
            tags=dto.tags or [],
            execution_policy=dto.execution_policy or "allow",
            auto_generated_name=auto_generated_name,
        )
        
        # Save to repository
        created_schedule = await self._schedule_repository.create(schedule)
        
        # Convert to DTO
        return ScheduleDto.from_entity(created_schedule)

    async def get_schedule(self, schedule_id: UUID) -> Optional[ScheduleDto]:
        """Get schedule by ID."""
        schedule = await self._schedule_repository.get_by_id(schedule_id)
        return ScheduleDto.from_entity(schedule) if schedule else None

    async def get_all_schedules(self, enabled_only: bool = False) -> List[ScheduleDto]:
        """Get all schedules."""
        schedules = await self._schedule_repository.get_all(enabled_only=enabled_only)
        return [ScheduleDto.from_entity(s) for s in schedules]

    async def get_filtered_schedules(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[ScheduleDto]:
        """Get schedules with filters."""
        schedules = await self._schedule_repository.get_filtered(
            category=category,
            tags=tags,
            task_name=task_name,
            enabled_only=enabled_only,
        )
        return [ScheduleDto.from_entity(s) for s in schedules]

    async def update_schedule(
        self, schedule_id: UUID, dto: ScheduleUpdateDto
    ) -> Optional[ScheduleDto]:
        """Update schedule."""
        # Get existing schedule
        schedule = await self._schedule_repository.get_by_id(schedule_id)
        if not schedule:
            return None
            
        # Update fields
        if dto.name is not None:
            schedule.name = dto.name
            schedule.auto_generated_name = False  # Name is now manually set
        if dto.cron_expression is not None:
            schedule.cron_expression = dto.cron_expression
        if dto.enabled is not None:
            schedule.enabled = dto.enabled
        if dto.description is not None:
            schedule.description = dto.description
        if dto.category is not None:
            schedule.category = dto.category
        if dto.tags is not None:
            schedule.tags = dto.tags
        if dto.execution_policy is not None:
            schedule.execution_policy = dto.execution_policy
            
        # Update task params
        if dto.task_params is not None:
            schedule.kwargs = dto.task_params.to_kwargs()
            schedule.kwargs["schedule_id"] = str(schedule_id)
            
        # Save updates
        updated_schedule = await self._schedule_repository.update(schedule)
        return ScheduleDto.from_entity(updated_schedule)

    async def delete_schedule(self, schedule_id: UUID) -> bool:
        """Delete schedule."""
        return await self._schedule_repository.delete(schedule_id)

    async def enable_schedule(self, schedule_id: UUID) -> bool:
        """Enable schedule."""
        return await self._schedule_repository.enable(schedule_id)

    async def disable_schedule(self, schedule_id: UUID) -> bool:
        """Disable schedule."""
        return await self._schedule_repository.disable(schedule_id)

    # _to_dto method removed - using ScheduleDto.from_entity instead