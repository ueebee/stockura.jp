"""Celery worker hooks for managing asyncio event loops."""
import asyncio
import threading
from celery import signals
from celery.utils.log import get_logger

logger = get_logger(__name__)

# Thread-local storage for event loops
_thread_local = threading.local()


def get_or_create_event_loop():
    """Get or create an event loop for the current thread."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, check if we have one stored
        if not hasattr(_thread_local, 'loop') or _thread_local.loop.is_closed():
            _thread_local.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_thread_local.loop)
        loop = _thread_local.loop
    return loop


@signals.worker_process_init.connect
def setup_worker_loop(**kwargs):
    """Initialize event loop when worker process starts."""
    logger.info("Setting up event loop for worker process")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _thread_local.loop = loop


@signals.worker_process_shutdown.connect
def cleanup_worker_loop(**kwargs):
    """Clean up event loop when worker process shuts down."""
    logger.info("Cleaning up event loop for worker process")
    if hasattr(_thread_local, 'loop') and not _thread_local.loop.is_closed():
        _thread_local.loop.close()