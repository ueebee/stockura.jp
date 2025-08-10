#!/bin/bash
# Monitor Redis events using docker compose exec

echo "Starting Redis event monitor..."
docker compose exec app python scripts/monitor_redis_events.py