"""Schedule repository implementation."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from app.domain.entities.schedule import Schedule
from app.domain.repositories.schedule_repository_interface import (
    ScheduleRepositoryInterface,
)
from app.infrastructure.database.models.schedule import CeleryBeatSchedule


class ScheduleRepository(ScheduleRepositoryInterface):
    """Schedule repository implementation."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        self._session = session

    async def create(self, schedule: Schedule) -> Schedule:
        """Create a new schedule."""
        db_schedule = CeleryBeatSchedule(
            id=schedule.id,
            name=schedule.name,
            task_name=schedule.task_name,
            cron_expression=schedule.cron_expression,
            enabled=schedule.enabled,
            args=schedule.args,
            kwargs=schedule.kwargs,
            description=schedule.description,
            category=schedule.category,
            tags=schedule.tags,
            execution_policy=schedule.execution_policy,
            auto_generated_name=schedule.auto_generated_name,
        )
        self._session.add(db_schedule)
        await self._session.commit()
        await self._session.refresh(db_schedule)
        return self._to_entity(db_schedule)

    async def get_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        """Get schedule by ID."""
        result = await self._session.execute(
            select(CeleryBeatSchedule).where(CeleryBeatSchedule.id == schedule_id)
        )
        db_schedule = result.scalar_one_or_none()
        return self._to_entity(db_schedule) if db_schedule else None

    async def get_by_name(self, name: str) -> Optional[Schedule]:
        """Get schedule by name."""
        result = await self._session.execute(
            select(CeleryBeatSchedule).where(CeleryBeatSchedule.name == name)
        )
        db_schedule = result.scalar_one_or_none()
        return self._to_entity(db_schedule) if db_schedule else None

    async def get_all(self, enabled_only: bool = False) -> List[Schedule]:
        """Get all schedules."""
        query = select(CeleryBeatSchedule)
        if enabled_only:
            query = query.where(CeleryBeatSchedule.enabled == True)
        result = await self._session.execute(query)
        return [self._to_entity(s) for s in result.scalars().all()]

    async def update(self, schedule: Schedule) -> Schedule:
        """Update schedule."""
        await self._session.execute(
            update(CeleryBeatSchedule)
            .where(CeleryBeatSchedule.id == schedule.id)
            .values(
                name=schedule.name,
                task_name=schedule.task_name,
                cron_expression=schedule.cron_expression,
                enabled=schedule.enabled,
                args=schedule.args,
                kwargs=schedule.kwargs,
                description=schedule.description,
                category=schedule.category,
                tags=schedule.tags,
                execution_policy=schedule.execution_policy,
                auto_generated_name=schedule.auto_generated_name,
            )
        )
        await self._session.commit()
        return await self.get_by_id(schedule.id)

    async def delete(self, schedule_id: UUID) -> bool:
        """Delete schedule."""
        result = await self._session.execute(
            select(CeleryBeatSchedule).where(CeleryBeatSchedule.id == schedule_id)
        )
        db_schedule = result.scalar_one_or_none()
        if db_schedule:
            await self._session.delete(db_schedule)
            await self._session.commit()
            return True
        return False

    async def enable(self, schedule_id: UUID) -> bool:
        """Enable schedule."""
        result = await self._session.execute(
            update(CeleryBeatSchedule)
            .where(CeleryBeatSchedule.id == schedule_id)
            .values(enabled=True)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def disable(self, schedule_id: UUID) -> bool:
        """Disable schedule."""
        result = await self._session.execute(
            update(CeleryBeatSchedule)
            .where(CeleryBeatSchedule.id == schedule_id)
            .values(enabled=False)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def get_filtered(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[Schedule]:
        """Get schedules with filters."""
        query = select(CeleryBeatSchedule)
        conditions = []
        
        if category:
            conditions.append(CeleryBeatSchedule.category == category)
        
        if tags:
            # Check if all specified tags are present in the schedule's tags
            for tag in tags:
                conditions.append(CeleryBeatSchedule.tags.contains([tag]))
        
        if task_name:
            conditions.append(CeleryBeatSchedule.task_name == task_name)
        
        if enabled_only:
            conditions.append(CeleryBeatSchedule.enabled == True)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self._session.execute(query)
        return [self._to_entity(s) for s in result.scalars().all()]

    def _to_entity(self, db_schedule: CeleryBeatSchedule) -> Schedule:
        """Convert database model to domain entity."""
        return Schedule(
            id=db_schedule.id,
            name=db_schedule.name,
            task_name=db_schedule.task_name,
            cron_expression=db_schedule.cron_expression,
            enabled=db_schedule.enabled,
            args=db_schedule.args,
            kwargs=db_schedule.kwargs,
            description=db_schedule.description,
            category=db_schedule.category,
            tags=db_schedule.tags,
            execution_policy=db_schedule.execution_policy,
            auto_generated_name=db_schedule.auto_generated_name,
            created_at=db_schedule.created_at,
            updated_at=db_schedule.updated_at,
        )