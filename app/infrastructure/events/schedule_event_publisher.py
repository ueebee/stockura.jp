"""Schedule event publisher for Redis Pub/Sub."""
import json
import logging
from datetime import datetime
from typing import Optional

from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ScheduleEventPublisher:
    """Publish schedule events to Redis."""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize the publisher.
        
        Args:
            redis_client: Redis client instance. If None, the feature is disabled.
        """
        self.redis = redis_client
        self.channel = settings.celery_beat_redis_channel
        self.enabled = settings.celery_beat_redis_sync_enabled and redis_client is not None
        
        # Log initialization status
        if self.enabled:
            logger.info(f"ScheduleEventPublisher initialized - Channel: {self.channel}")
        else:
            logger.warning("ScheduleEventPublisher disabled - Redis client not available or sync disabled")
        
    async def publish_schedule_created(self, schedule_id: str) -> None:
        """Publish schedule created event.
        
        Args:
            schedule_id: ID of the created schedule
        """
        await self._publish_event("schedule_created", schedule_id)
            
    async def publish_schedule_updated(self, schedule_id: str) -> None:
        """Publish schedule updated event.
        
        Args:
            schedule_id: ID of the updated schedule
        """
        await self._publish_event("schedule_updated", schedule_id)
            
    async def publish_schedule_deleted(self, schedule_id: str) -> None:
        """Publish schedule deleted event.
        
        Args:
            schedule_id: ID of the deleted schedule
        """
        await self._publish_event("schedule_deleted", schedule_id)
    
    async def _publish_event(self, event_type: str, schedule_id: str) -> None:
        """Publish an event to Redis.
        
        Args:
            event_type: Type of the event
            schedule_id: ID of the schedule
        """
        if not self.enabled:
            logger.debug(f"Redis sync is disabled, skipping {event_type} event for {schedule_id}")
            return
            
        try:
            event = {
                "event_type": event_type,
                "schedule_id": schedule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Publishing event to Redis channel '{self.channel}': {event}")
            
            # Publish to Redis channel
            result = await self.redis.publish(self.channel, json.dumps(event))
            
            logger.info(f"✅ Published {event_type} event for schedule {schedule_id} (subscribers: {result})")
            
        except Exception as e:
            # Log error but don't raise - fail silently to maintain backward compatibility
            logger.error(f"❌ Failed to publish {event_type} event: {e}", exc_info=True)