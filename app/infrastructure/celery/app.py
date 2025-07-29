"""Celery application configuration."""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

# Create Celery instance
celery_app = Celery("stockura")

# Load configuration
celery_app.config_from_object("app.infrastructure.celery.config")

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.infrastructure.celery.tasks"])