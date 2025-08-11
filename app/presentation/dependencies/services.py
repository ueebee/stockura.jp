"""Service dependency injection providers."""
import logging
from typing import Optional

from app.core.config import get_settings
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher
from app.infrastructure.redis.redis_client import get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_schedule_event_publisher() -> Optional[ScheduleEventPublisher]:
    """スケジュールイベントパブリッシャーの依存性注入"""
    if not settings.celery_beat_redis_sync_enabled:
        logger.debug("Redis sync is disabled, returning None for ScheduleEventPublisher")
        return None
        
    try:
        redis_client = await get_redis_client()
        return ScheduleEventPublisher(redis_client)
    except Exception as e:
        logger.error(f"Failed to create ScheduleEventPublisher: {e}")
        # Return None instead of raising to maintain backward compatibility
        return None