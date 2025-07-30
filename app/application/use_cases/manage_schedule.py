"""Schedule management use case."""
from typing import List, Optional
from uuid import UUID, uuid4

from app.application.dto.schedule_dto import (
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
        
        # Create schedule entity
        schedule = Schedule(
            id=schedule_id,
            name=dto.name,
            task_name=dto.task_name,
            cron_expression=dto.cron_expression,
            enabled=dto.enabled,
            args=args,
            kwargs=kwargs,
            description=dto.description,
        )
        
        # Save to repository
        created_schedule = await self._schedule_repository.create(schedule)
        
        # Convert to DTO
        return self._to_dto(created_schedule)

    async def get_schedule(self, schedule_id: UUID) -> Optional[ScheduleDto]:
        """Get schedule by ID."""
        schedule = await self._schedule_repository.get_by_id(schedule_id)
        return self._to_dto(schedule) if schedule else None

    async def get_all_schedules(self, enabled_only: bool = False) -> List[ScheduleDto]:
        """Get all schedules."""
        schedules = await self._schedule_repository.get_all(enabled_only=enabled_only)
        return [self._to_dto(s) for s in schedules]

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
        if dto.cron_expression is not None:
            schedule.cron_expression = dto.cron_expression
        if dto.enabled is not None:
            schedule.enabled = dto.enabled
        if dto.description is not None:
            schedule.description = dto.description
            
        # Update task params
        if dto.task_params is not None:
            schedule.kwargs = dto.task_params.to_kwargs()
            schedule.kwargs["schedule_id"] = str(schedule_id)
            
        # Save updates
        updated_schedule = await self._schedule_repository.update(schedule)
        return self._to_dto(updated_schedule)

    async def delete_schedule(self, schedule_id: UUID) -> bool:
        """Delete schedule."""
        return await self._schedule_repository.delete(schedule_id)

    async def enable_schedule(self, schedule_id: UUID) -> bool:
        """Enable schedule."""
        return await self._schedule_repository.enable(schedule_id)

    async def disable_schedule(self, schedule_id: UUID) -> bool:
        """Disable schedule."""
        return await self._schedule_repository.disable(schedule_id)

    def _to_dto(self, schedule: Schedule) -> ScheduleDto:
        """Convert schedule entity to DTO."""
        # Extract task params from kwargs
        task_params = None
        if schedule.kwargs:
            task_params = TaskParamsDto(
                period_type=schedule.kwargs.get("period_type", "yesterday"),
                from_date=schedule.kwargs.get("from_date"),
                to_date=schedule.kwargs.get("to_date"),
                codes=schedule.kwargs.get("codes"),
                market=schedule.kwargs.get("market"),
            )
            
        return ScheduleDto(
            id=schedule.id,
            name=schedule.name,
            task_name=schedule.task_name,
            cron_expression=schedule.cron_expression,
            enabled=schedule.enabled,
            description=schedule.description,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
            task_params=task_params,
        )