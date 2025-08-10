"""Database scheduler for Celery Beat with asyncpg support."""
import asyncio
import json
import threading
from datetime import datetime
from typing import Any, Dict, Optional

import redis
from celery import schedules
from celery.beat import ScheduleEntry, Scheduler
from celery.utils.log import get_logger
from croniter import croniter
from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.database.models.schedule import CeleryBeatSchedule

logger = get_logger(__name__)
settings = get_settings()

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
        
        # Get queue from task routing configuration
        queue = None
        if app and hasattr(app, 'conf') and 'task_routes' in app.conf:
            task_routes = app.conf.task_routes
            if schedule_model.task_name in task_routes:
                queue = task_routes[schedule_model.task_name].get('queue', 'default')
        
        # Set options with queue
        options = {}
        if queue:
            options['queue'] = queue
            logger.debug(f"Task {schedule_model.task_name} will be sent to queue: {queue}")
        
        super().__init__(
            name=schedule_model.name,
            task=schedule_model.task_name,
            schedule=schedule,
            args=schedule_model.args or [],
            kwargs=schedule_model.kwargs or {},
            options=options,
            app=app,
        )
        
        # Initialize last_run_at to None to ensure the task runs
        if not hasattr(self, 'last_run_at'):
            self.last_run_at = None

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
        
        result = super().is_due()
        is_due, next_run_seconds = result
        logger.debug(f"Task {self.name} is_due check: is_due={is_due}, "
                    f"next_run_seconds={next_run_seconds}, schedule={self.schedule}, "
                    f"last_run_at={self.last_run_at}")
        return result
    
    def __next__(self):
        """Return a new instance of the same entry."""
        return self.__class__(self.model, app=self.app)
    
    next = __next__  # Python 2/3 compatibility

    def __repr__(self):
        """String representation."""
        return f"<DatabaseScheduleEntry: {self.name} {self.schedule}>"


class DatabaseSchedulerAsyncPG(Scheduler):
    """Custom scheduler that reads schedules from database using asyncpg."""

    Entry = DatabaseScheduleEntry
    
    def __init__(self, *args, **kwargs):
        """Initialize database scheduler."""
        # Initialize attributes before calling super()
        self._last_updated = None
        self._last_sync_time = None
        self._schedule_cache = {}
        self._event_loop = None
        self._redis_subscriber_thread = None
        self._redis_client = None
        self._shutdown_event = threading.Event()
        
        # Log environment variables for debugging
        logger.info("=" * 60)
        logger.info("DatabaseSchedulerAsyncPG Initialization")
        logger.info("=" * 60)
        logger.info(f"Redis Sync Enabled: {settings.celery_beat_redis_sync_enabled}")
        logger.info(f"Min Sync Interval: {settings.celery_beat_min_sync_interval}")
        logger.info(f"Redis Channel: {settings.celery_beat_redis_channel}")
        logger.info(f"Redis URL: {settings.redis_url}")
        logger.info("=" * 60)
        
        # Call parent constructor
        super().__init__(*args, **kwargs)
        
        # Setup event loop after parent init
        self._setup_event_loop()
        
        # Start Redis subscriber if enabled
        if settings.celery_beat_redis_sync_enabled:
            logger.info("Redis Sync is ENABLED - Starting Redis subscriber thread")
            self._start_redis_subscriber()
        else:
            logger.warning("Redis Sync is DISABLED - Scheduler will sync every 60 seconds")
        
    def _setup_event_loop(self):
        """Setup event loop for scheduler."""
        self._event_loop = get_or_create_event_loop()
        logger.info("Event loop setup for database scheduler")
    
    def _start_redis_subscriber(self):
        """Start Redis event listener in a separate thread."""
        try:
            self._redis_subscriber_thread = threading.Thread(
                target=self._redis_subscriber_worker,
                daemon=True,
                name="CeleryBeatRedisSubscriber"
            )
            self._redis_subscriber_thread.start()
            logger.info("Redis subscriber thread started for schedule updates")
        except Exception as e:
            logger.error(f"Failed to start Redis subscriber: {e}")
    
    def _redis_subscriber_worker(self):
        """Redis event listener worker thread."""
        try:
            # Create Redis client for this thread
            logger.info(f"Creating Redis client for subscriber thread with URL: {settings.redis_url}")
            self._redis_client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
            
            # Test connection
            self._redis_client.ping()
            logger.info("Redis connection successful for subscriber thread")
            
            pubsub = self._redis_client.pubsub()
            pubsub.subscribe(settings.celery_beat_redis_channel)
            
            logger.info(f"✅ Subscribed to Redis channel: {settings.celery_beat_redis_channel}")
            
            # Listen for messages
            for message in pubsub.listen():
                if self._shutdown_event.is_set():
                    logger.info("Shutdown event detected, stopping Redis subscriber")
                    break
                    
                if message['type'] == 'message':
                    try:
                        logger.info(f"Received Redis message: {message['data']}")
                        self._handle_schedule_event(message['data'])
                    except Exception as e:
                        logger.error(f"Error handling schedule event: {e}", exc_info=True)
                        
        except Exception as e:
            logger.error(f"Redis subscriber error: {e}", exc_info=True)
        finally:
            logger.info("Cleaning up Redis subscriber")
            if self._redis_client:
                self._redis_client.close()
                
    def _handle_schedule_event(self, data: str):
        """Handle schedule event from Redis.
        
        Args:
            data: JSON string containing event data
        """
        try:
            event = json.loads(data)
            event_type = event.get('event_type')
            schedule_id = event.get('schedule_id')
            
            logger.info(f"🔔 Received schedule event: {event_type} for schedule {schedule_id}")
            
            # Check minimum sync interval
            if self._last_sync_time:
                elapsed = (datetime.utcnow() - self._last_sync_time).total_seconds()
                if elapsed < settings.celery_beat_min_sync_interval:
                    logger.debug(
                        f"Skipping sync - last sync was {elapsed:.1f}s ago "
                        f"(min interval: {settings.celery_beat_min_sync_interval}s)"
                    )
                    return
                    
            # Trigger immediate sync
            logger.info("⚡ Triggering immediate schedule sync due to Redis event")
            self.sync_schedules()
            logger.info("✅ Schedule sync completed successfully")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schedule event: {e}")
        except Exception as e:
            logger.error(f"Error processing schedule event: {e}", exc_info=True)
        
    def setup_schedule(self):
        """Initial schedule setup."""
        # Ensure event loop is set up
        if not hasattr(self, '_event_loop') or self._event_loop is None:
            self._setup_event_loop()
        self.sync_schedules()
        
    def sync_schedules(self):
        """Sync schedules from database."""
        logger.info("Syncing schedules from database")
        
        try:
            # Use a separate event loop for database operations to avoid conflicts
            # with the Redis subscriber thread's event loop
            db_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(db_loop)
            
            try:
                logger.info("Using dedicated event loop for database operations")
                schedules = db_loop.run_until_complete(
                    self._load_schedules_from_db()
                )
                logger.info(f"Successfully loaded {len(schedules)} schedules")
            finally:
                db_loop.close()
                # Reset the event loop to None to avoid interference
                asyncio.set_event_loop(None)
            
            # Update schedule
            self.schedule.clear()
            
            for schedule in schedules:
                entry = self.Entry(schedule, app=self.app)
                self.schedule[schedule.name] = entry
                
            logger.info(f"Updated scheduler with {len(schedules)} schedules")
            self._last_updated = datetime.utcnow()
            self._last_sync_time = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to sync schedules: {str(e)}", exc_info=True)
    
    async def _load_schedules_from_db(self):
        """Load schedules from database."""
        logger.info("Starting to load schedules from database")
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info("Getting async session...")
            async with get_async_session_context() as session:
                session_time = asyncio.get_event_loop().time()
                logger.info(f"Got session in {session_time - start_time:.2f}s")
                
                logger.info("Executing query...")
                result = await session.execute(
                    select(CeleryBeatSchedule).where(CeleryBeatSchedule.enabled == True)
                )
                query_time = asyncio.get_event_loop().time()
                logger.info(f"Query executed in {query_time - session_time:.2f}s")
                
                schedules = result.scalars().all()
                logger.info(f"Loaded {len(schedules)} schedules in total {asyncio.get_event_loop().time() - start_time:.2f}s")
                return schedules
        except Exception as e:
            logger.error(f"Error loading schedules from database: {e}", exc_info=True)
            raise
    
    def tick(self):
        """Run one iteration of the scheduler."""
        # Reload schedules every 60 seconds
        if self._should_reload_schedules():
            self.sync_schedules()
        
        # Calculate minimum interval until next run
        min_interval = self.max_interval
        
        # Process each schedule entry
        for entry in self.schedule.values():
            is_due, next_run_seconds = entry.is_due()
            
            if is_due:
                logger.info(f"Task {entry.name} is due, applying entry")
                try:
                    self.apply_entry(entry)
                except Exception as e:
                    logger.error(f"Failed to apply entry {entry.name}: {e}", exc_info=True)
            
            # Update minimum interval
            min_interval = min(min_interval, next_run_seconds)
        
        return min_interval
    
    def apply_entry(self, entry, producer=None):
        """Apply schedule entry - send task to worker."""
        logger.info(f"Applying entry: {entry.name}, task: {entry.task}, "
                    f"args: {entry.args}, kwargs: {entry.kwargs}")
        
        try:
            # Call parent class apply_entry to send the task
            result = super().apply_entry(entry, producer)
            logger.info(f"Task {entry.name} sent successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to send task {entry.name}: {e}", exc_info=True)
            raise
    
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
        # Signal shutdown to Redis subscriber
        self._shutdown_event.set()
        
        # Wait for Redis subscriber to finish
        if self._redis_subscriber_thread and self._redis_subscriber_thread.is_alive():
            self._redis_subscriber_thread.join(timeout=5)
            
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