"""Schedule repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.schedule import Schedule


class ScheduleRepositoryInterface(ABC):
    """Schedule repository interface."""

    @abstractmethod
    async def create(self, schedule: Schedule) -> Schedule:
        """Create a new schedule."""
        pass

    @abstractmethod
    async def get_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        """Get schedule by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Schedule]:
        """Get schedule by name."""
        pass

    @abstractmethod
    async def get_all(self, enabled_only: bool = False) -> List[Schedule]:
        """Get all schedules."""
        pass

    @abstractmethod
    async def get_filtered(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[Schedule]:
        """Get schedules with filters."""
        pass

    @abstractmethod
    async def update(self, schedule: Schedule) -> Schedule:
        """Update schedule."""
        pass

    @abstractmethod
    async def delete(self, schedule_id: UUID) -> bool:
        """Delete schedule."""
        pass

    @abstractmethod
    async def enable(self, schedule_id: UUID) -> bool:
        """Enable schedule."""
        pass

    @abstractmethod
    async def disable(self, schedule_id: UUID) -> bool:
        """Disable schedule."""
        pass