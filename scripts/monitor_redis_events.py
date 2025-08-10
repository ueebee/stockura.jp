#!/usr/bin/env python
"""Monitor Redis events for schedule updates."""
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Redis URL from environment
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CHANNEL = os.environ.get("CELERY_BEAT_REDIS_CHANNEL", "celery_beat_schedule_updates")

def monitor_events():
    """Monitor Redis events."""
    logger.info(f"Connecting to Redis: {REDIS_URL}")
    logger.info(f"Subscribing to channel: {CHANNEL}")
    
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    pubsub.subscribe(CHANNEL)
    
    logger.info("Listening for events... (Press Ctrl+C to stop)")
    
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    logger.info(f"📨 Received event: {data}")
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON: {message['data']}")
    except KeyboardInterrupt:
        logger.info("Stopping monitor...")
    finally:
        pubsub.close()
        client.close()


if __name__ == "__main__":
    monitor_events()