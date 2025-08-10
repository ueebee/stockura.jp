#!/usr/bin/env python
"""Test Redis sync functionality."""
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import get_settings
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher
from app.infrastructure.redis.redis_client import get_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


async def test_publish_event():
    """Test publishing schedule event."""
    logger.info("Testing Redis sync functionality...")
    
    # Get Redis client
    redis_client = await get_redis_client()
    
    # Create event publisher
    publisher = ScheduleEventPublisher(redis_client)
    
    # Publish test event
    test_schedule_id = "test-schedule-123"
    logger.info(f"Publishing schedule_created event for {test_schedule_id}")
    await publisher.publish_schedule_created(test_schedule_id)
    
    logger.info("Event published successfully")
    

def test_subscribe_event():
    """Test subscribing to schedule events."""
    logger.info("Starting Redis subscriber test...")
    
    # Create sync Redis client for subscriber
    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(settings.celery_beat_redis_channel)
    
    logger.info(f"Subscribed to channel: {settings.celery_beat_redis_channel}")
    logger.info("Waiting for events (press Ctrl+C to stop)...")
    
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                logger.info(f"Received event: {data}")
    except KeyboardInterrupt:
        logger.info("Stopping subscriber...")
    finally:
        pubsub.close()
        redis_client.close()


async def main():
    """Main test function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "subscribe":
        # Run subscriber
        test_subscribe_event()
    else:
        # Run publisher
        await test_publish_event()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "subscribe":
        # Run sync subscriber
        test_subscribe_event()
    else:
        # Run async publisher
        asyncio.run(main())