#!/usr/bin/env python
"""Test immediate schedule execution with Redis sync."""
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.database.models.schedule import CeleryBeatSchedule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


async def test_immediate_execution():
    """Test if schedule executes immediately with Redis sync."""
    logger.info("=" * 60)
    logger.info("Testing Immediate Schedule Execution with Redis Sync")
    logger.info("=" * 60)
    
    # Create a schedule that should execute every minute
    schedule_name = f"test_immediate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Use */1 for every minute
    cron_expression = "*/1 * * * *"
    
    logger.info(f"Creating schedule: {schedule_name}")
    logger.info(f"Cron expression: {cron_expression} (every minute)")
    
    # Create schedule via API
    response = requests.post(
        "http://localhost:8000/api/v1/schedules",
        json={
            "name": schedule_name,
            "task_name": "fetch_listed_info_task",
            "cron_expression": cron_expression,
            "description": "Test immediate execution",
            "enabled": True,
            "task_params": {
                "period_type": "yesterday",
                "codes": None,
                "market": None
            }
        }
    )
    
    if response.status_code != 201:
        logger.error(f"Failed to create schedule: {response.text}")
        return
        
    schedule_data = response.json()
    schedule_id = schedule_data["id"]
    logger.info(f"✅ Schedule created: {schedule_id}")
    
    # Wait for 10 seconds to see if Redis sync triggers immediate sync
    logger.info("Waiting 10 seconds for Redis sync to propagate...")
    await asyncio.sleep(10)
    
    # Check if schedule exists in database
    async with get_async_session_context() as session:
        result = await session.execute(
            select(CeleryBeatSchedule).where(CeleryBeatSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if schedule:
            logger.info(f"✅ Schedule found in database: {schedule.name}")
        else:
            logger.error("❌ Schedule not found in database")
    
    # Check execution history
    logger.info("Checking execution history...")
    
    # Wait up to 90 seconds for execution
    start_time = asyncio.get_event_loop().time()
    executed = False
    
    while asyncio.get_event_loop().time() - start_time < 90:
        response = requests.get(f"http://localhost:8000/api/v1/schedules/{schedule_id}/history")
        
        if response.status_code == 200:
            history_data = response.json()
            if history_data.get("history"):
                logger.info(f"✅ Task executed! History: {history_data['history'][0]}")
                executed = True
                break
        
        await asyncio.sleep(5)
        logger.info("  Still waiting for execution...")
    
    if not executed:
        logger.warning("❌ Task did not execute within 90 seconds")
    
    # Cleanup
    logger.info("Cleaning up...")
    response = requests.delete(f"http://localhost:8000/api/v1/schedules/{schedule_id}")
    if response.status_code == 204:
        logger.info("✅ Schedule deleted")
    
    logger.info("Test completed")


async def check_celery_beat_logs():
    """Display recent Celery Beat logs."""
    import subprocess
    
    logger.info("\nRecent Celery Beat logs:")
    result = subprocess.run(
        ["docker", "logs", "stockura-celery-beat", "--tail", "50"],
        capture_output=True,
        text=True
    )
    
    for line in result.stdout.split('\n'):
        if any(keyword in line for keyword in ["schedule_created", "Syncing", "due", "Sending"]):
            logger.info(f"  📋 {line}")


if __name__ == "__main__":
    asyncio.run(test_immediate_execution())
    # asyncio.run(check_celery_beat_logs())