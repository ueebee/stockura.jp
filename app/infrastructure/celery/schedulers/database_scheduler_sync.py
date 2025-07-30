"""Synchronous database scheduler for Celery Beat."""
from datetime import datetime
from typing import Any, Dict, Optional

from celery import schedules
from celery.beat import ScheduleEntry, Scheduler
from celery.utils.log import get_logger
from croniter import croniter
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.infrastructure.database.models.schedule import CeleryBeatSchedule

logger = get_logger(__name__)
settings = get_settings()


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


class DatabaseScheduler(Scheduler):
    """Custom scheduler that reads schedules from database using sync connection."""

    Entry = DatabaseScheduleEntry
    
    def __init__(self, *args, **kwargs):
        """Initialize database scheduler."""
        super().__init__(*args, **kwargs)
        self._last_updated = None
        self._schedule_cache = {}
        
        # Create sync database connection
        # Convert async URL to sync URL
        db_url = settings.database_url.replace("+asyncpg", "")
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def setup_schedule(self):
        """Initial schedule setup."""
        self.sync_schedules()
        
    def sync_schedules(self):
        """Sync schedules from database."""
        logger.info("Syncing schedules from database")
        
        try:
            # Load schedules using sync session
            with self.Session() as session:
                result = session.execute(
                    select(CeleryBeatSchedule).where(CeleryBeatSchedule.enabled == True)
                )
                schedules = result.scalars().all()
            
            # Update schedule
            self.schedule.clear()
            
            for schedule in schedules:
                entry = self.Entry(schedule, app=self.app)
                self.schedule[schedule.name] = entry
                
            logger.info(f"Loaded {len(schedules)} schedules from database")
            self._last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to sync schedules: {str(e)}")
    
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
        return "DatabaseScheduler"
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
        super().close()