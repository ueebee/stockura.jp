"""Celery configuration."""
import os
from kombu import Exchange, Queue

from app.core.config import get_settings

settings = get_settings()

# Broker settings
broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

# Task settings
task_serializer = settings.celery_task_serializer
result_serializer = settings.celery_result_serializer
accept_content = settings.celery_accept_content
timezone = settings.celery_timezone
enable_utc = settings.celery_enable_utc

# Task execution settings
task_acks_late = True
task_reject_on_worker_lost = True
task_ignore_result = False

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000
worker_disable_rate_limits = False

# Beat settings
# Default scheduler (file-based)
# beat_scheduler = "celery.beat:PersistentScheduler"
# beat_schedule_filename = "celerybeat-schedule.db"

# Custom scheduler (database-based)
# Option 1: Sync version (stable)
# beat_scheduler = "app.infrastructure.celery.schedulers.database_scheduler_sync:DatabaseScheduler"

# Option 2: Asyncpg version (high performance)
beat_scheduler = "app.infrastructure.celery.schedulers.database_scheduler_asyncpg:DatabaseSchedulerAsyncPG"

# Result backend settings
result_expires = 3600  # 1 hour
result_persistent = True
result_compression = "gzip"

# Routing
task_routes = {
    "app.infrastructure.celery.tasks.listed_info_task.*": {"queue": "default"},
}

# Queue configuration
task_queues = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("priority", Exchange("priority"), routing_key="priority"),
)

# Time limits
task_soft_time_limit = 600  # 10 minutes
task_time_limit = 720  # 12 minutes

# Retry settings
task_autoretry_for = (Exception,)
task_max_retries = 3
task_retry_backoff = True
task_retry_backoff_max = 600
task_retry_jitter = True

# Monitoring
worker_send_task_events = True
task_send_sent_event = True