#!/usr/bin/env python
"""Manual test for schedule sync without Celery Beat."""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.database.models.schedule import CeleryBeatSchedule
from app.infrastructure.di.providers import get_schedule_event_publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


async def create_test_schedule():
    """Create a test schedule in the database."""
    async with get_async_session_context() as session:
        # Create test schedule
        schedule = CeleryBeatSchedule(
            id=uuid4(),
            name=f"test_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            task_name="fetch_listed_info_task",
            cron_expression="*/5 * * * *",  # Every 5 minutes
            enabled=True,
            kwargs={
                "period_type": "yesterday",
                "codes": [],
                "market": None
            }
        )
        
        session.add(schedule)
        await session.commit()
        
        logger.info(f"Created test schedule: {schedule.name} (ID: {schedule.id})")
        return schedule.id


async def test_schedule_sync():
    """Test schedule sync with Redis notification."""
    logger.info("=" * 60)
    logger.info("Testing Schedule Sync with Redis Notification")
    logger.info("=" * 60)
    
    # Check Redis sync configuration
    logger.info(f"Redis sync enabled: {settings.celery_beat_redis_sync_enabled}")
    logger.info(f"Redis channel: {settings.celery_beat_redis_channel}")
    logger.info(f"Min sync interval: {settings.celery_beat_min_sync_interval}s")
    
    # Create test schedule
    schedule_id = await create_test_schedule()
    
    # Get event publisher
    event_publisher = await get_schedule_event_publisher()
    
    if event_publisher:
        logger.info("Publishing schedule_created event...")
        await event_publisher.publish_schedule_created(str(schedule_id))
        logger.info("Event published successfully!")
    else:
        logger.warning("Event publisher is not available")
    
    # List all schedules
    logger.info("\nCurrent schedules in database:")
    async with get_async_session_context() as session:
        result = await session.execute(
            select(CeleryBeatSchedule).where(CeleryBeatSchedule.enabled == True)
        )
        schedules = result.scalars().all()
        
        for schedule in schedules:
            logger.info(f"  - {schedule.name} ({schedule.cron_expression})")
    
    logger.info("\n✅ Test completed")
    logger.info("If Celery Beat is running with Redis sync enabled, it should have received the notification")


async def cleanup_test_schedules():
    """Clean up test schedules."""
    async with get_async_session_context() as session:
        result = await session.execute(
            select(CeleryBeatSchedule).where(
                CeleryBeatSchedule.name.like("test_%")
            )
        )
        schedules = result.scalars().all()
        
        for schedule in schedules:
            await session.delete(schedule)
        
        await session.commit()
        logger.info(f"Cleaned up {len(schedules)} test schedules")


async def main():
    """Main function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        await cleanup_test_schedules()
    else:
        await test_schedule_sync()


if __name__ == "__main__":
    asyncio.run(main())