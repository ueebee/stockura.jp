"""Database scheduler for Celery Beat with asyncpg support."""
import asyncio
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from celery import schedules
from celery.beat import ScheduleEntry, Scheduler
from celery.utils.log import get_logger
from croniter import croniter
from sqlalchemy import select

from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.database.models.schedule import CeleryBeatSchedule

logger = get_logger(__name__)

# Thread-local storage for event loop
_thread_local = threading.local()


def get_or_create_event_loop():
    """Get or create event loop for the current thread."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        if not hasattr(_thread_local, 'loop') or _thread_local.loop.is_closed():
            _thread_local.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_thread_local.loop)
        return _thread_local.loop


class DatabaseScheduleEntry(ScheduleEntry):
    """Schedule entry that reads from database."""

    def __init__(self, schedule_model: CeleryBeatSchedule, app=None):
        """Initialize schedule entry from database model."""
        self.model = schedule_model
        
        # Convert cron expression to celery schedule
        schedule = self._cron_to_schedule(schedule_model.cron_expression)
        
        super().__init__(
            name=schedule_model.name,
            task=schedule_model.task_name,
            schedule=schedule,
            args=schedule_model.args or [],
            kwargs=schedule_model.kwargs or {},
            options={},
            app=app,
        )

    def _cron_to_schedule(self, cron_expression: str) -> schedules.crontab:
        """Convert cron expression to celery crontab schedule."""
        # Parse cron expression (minute hour day month day_of_week)
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")
        
        minute, hour, day, month, day_of_week = parts
        
        return schedules.crontab(
            minute=minute,
            hour=hour,
            day_of_month=day,
            month_of_year=month,
            day_of_week=day_of_week,
        )

    def is_due(self):
        """Check if the task is due."""
        if not self.model.enabled:
            return False, 60.0  # Check again in 60 seconds
        
        return super().is_due()

    def __repr__(self):
        """String representation."""
        return f"<DatabaseScheduleEntry: {self.name} {self.schedule}>"


class DatabaseSchedulerAsyncPG(Scheduler):
    """Custom scheduler that reads schedules from database using asyncpg."""

    Entry = DatabaseScheduleEntry
    
    def __init__(self, *args, **kwargs):
        """Initialize database scheduler."""
        super().__init__(*args, **kwargs)
        self._last_updated = None
        self._schedule_cache = {}
        self._event_loop = None
        self._setup_event_loop()
        
    def _setup_event_loop(self):
        """Setup event loop for scheduler."""
        self._event_loop = get_or_create_event_loop()
        logger.info("Event loop setup for database scheduler")
        
    def setup_schedule(self):
        """Initial schedule setup."""
        self.sync_schedules()
        
    def sync_schedules(self):
        """Sync schedules from database."""
        logger.info("Syncing schedules from database")
        
        try:
            # Ensure we have an event loop
            if self._event_loop is None or self._event_loop.is_closed():
                self._setup_event_loop()
                
            # Run async code in the scheduler's event loop
            schedules = self._event_loop.run_until_complete(
                self._load_schedules_from_db()
            )
            
            # Update schedule
            self.schedule.clear()
            
            for schedule in schedules:
                entry = self.Entry(schedule, app=self.app)
                self.schedule[schedule.name] = entry
                
            logger.info(f"Loaded {len(schedules)} schedules from database")
            self._last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to sync schedules: {str(e)}", exc_info=True)
    
    async def _load_schedules_from_db(self):
        """Load schedules from database."""
        async with get_async_session_context() as session:
            result = await session.execute(
                select(CeleryBeatSchedule).where(CeleryBeatSchedule.enabled == True)
            )
            return result.scalars().all()
    
    def tick(self):
        """Run one iteration of the scheduler."""
        # Reload schedules every 60 seconds
        if self._should_reload_schedules():
            self.sync_schedules()
            
        return super().tick()
    
    def _should_reload_schedules(self) -> bool:
        """Check if schedules should be reloaded."""
        if self._last_updated is None:
            return True
            
        # Reload every 60 seconds
        elapsed = (datetime.utcnow() - self._last_updated).total_seconds()
        return elapsed > 60
    
    @property
    def info(self) -> str:
        """Return scheduler info."""
        return "DatabaseSchedulerAsyncPG"
    
    def close(self):
        """Clean up resources."""
        if self._event_loop and not self._event_loop.is_closed():
            # Schedule cleanup in the event loop
            asyncio.run_coroutine_threadsafe(
                self._cleanup_async(), self._event_loop
            ).result()
            self._event_loop.close()
        super().close()
        
    async def _cleanup_async(self):
        """Async cleanup tasks."""
        # Add any async cleanup here if needed
        pass