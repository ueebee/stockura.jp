"""Listed info Celery task with proper async handling."""
import asyncio
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from celery import Task
from celery.utils.log import get_task_logger

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.worker_hooks import get_or_create_event_loop
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.repositories.task_log_repository import TaskLogRepository

logger = get_task_logger(__name__)


class FetchListedInfoTask(Task):
    """Base task class for listed info fetching."""

    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retry due to: {exc}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(bind=True, base=FetchListedInfoTask, name="fetch_listed_info_task_asyncpg")
def fetch_listed_info_task_asyncpg(
    self,
    schedule_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
    period_type: Optional[str] = "yesterday",  # "yesterday", "7days", "30days", "custom"
):
    """
    Fetch listed info data from J-Quants API with proper async handling.

    Args:
        schedule_id: Schedule ID if triggered by schedule
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        codes: List of stock codes to fetch
        market: Market code to filter
        period_type: Period type for date range calculation
    """
    task_id = self.request.id
    log_id = uuid4()
    
    logger.info(
        f"Starting fetch_listed_info_task - task_id: {task_id}, "
        f"schedule_id: {schedule_id}, period_type: {period_type}"
    )

    # Get or create event loop for this worker
    loop = get_or_create_event_loop()
    
    # Run async code in the worker's event loop
    return loop.run_until_complete(
        _fetch_listed_info_async(
            task_id=task_id,
            log_id=log_id,
            schedule_id=schedule_id,
            from_date=from_date,
            to_date=to_date,
            codes=codes,
            market=market,
            period_type=period_type,
        )
    )


async def _fetch_listed_info_async(
    task_id: str,
    log_id: UUID,
    schedule_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
    period_type: Optional[str] = "yesterday",
):
    """Async implementation of fetch_listed_info task."""
    from app.application.use_cases.fetch_listed_info import FetchListedInfoUseCase
    from app.infrastructure.external.jquants.jquants_client import JQuantsClient
    from app.infrastructure.repositories.listed_info_repository_impl import (
        ListedInfoRepositoryImpl,
    )
    from app.core.logging import get_logger

    async with get_async_session_context() as session:
        # Initialize task log
        task_log_repo = TaskLogRepository(session)
        
        # Create task log entry
        from app.domain.entities.task_log import TaskExecutionLog
        
        task_log = TaskExecutionLog(
            id=log_id,
            schedule_id=UUID(schedule_id) if schedule_id else None,
            task_name="fetch_listed_info_task",
            task_id=task_id,
            started_at=datetime.utcnow(),
            status="running",
        )
        
        await task_log_repo.create(task_log)
        
        try:
            # Calculate date range based on period_type
            target_dates = _calculate_date_range(
                period_type, from_date, to_date
            )
            
            logger.info(f"Processing dates: {target_dates}")
            
            # Initialize dependencies
            jquants_client = JQuantsClient()
            listed_info_repo = ListedInfoRepositoryImpl(session)
            app_logger = get_logger(__name__)
            
            use_case = FetchListedInfoUseCase(
                jquants_client=jquants_client,
                listed_info_repository=listed_info_repo,
                logger=app_logger,
            )
            
            # Process each date
            total_fetched = 0
            total_saved = 0
            errors = []
            
            for target_date in target_dates:
                logger.info(f"Processing date: {target_date}")
                
                if codes:
                    # Process specific codes
                    for code in codes:
                        result = await use_case.fetch_by_code(
                            code=code, target_date=target_date
                        )
                        if result.success:
                            total_fetched += result.fetched_count
                            total_saved += result.saved_count
                        else:
                            errors.append(f"Code {code}: {result.error_message}")
                else:
                    # Process all codes
                    result = await use_case.fetch_and_update_all(
                        target_date=target_date
                    )
                    if result.success:
                        total_fetched += result.fetched_count
                        total_saved += result.saved_count
                    else:
                        errors.append(f"Date {target_date}: {result.error_message}")
            
            # Update task log with results
            status = "success" if not errors else "failed"
            result_data = {
                "total_fetched": total_fetched,
                "total_saved": total_saved,
                "dates_processed": [d.isoformat() for d in target_dates],
                "codes": codes,
                "market": market,
                "errors": errors,
            }
            
            await task_log_repo.update_status(
                log_id=log_id,
                status=status,
                finished_at=datetime.utcnow(),
                result=result_data,
                error_message="\n".join(errors) if errors else None,
            )
            
            logger.info(
                f"Task completed - status: {status}, "
                f"fetched: {total_fetched}, saved: {total_saved}"
            )
            
            return result_data
            
        except Exception as e:
            logger.error(f"Task failed with error: {str(e)}")
            
            # Update task log with error
            await task_log_repo.update_status(
                log_id=log_id,
                status="failed",
                finished_at=datetime.utcnow(),
                error_message=str(e),
            )
            
            raise


def _calculate_date_range(
    period_type: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> List[date]:
    """Calculate date range based on period type."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    if period_type == "yesterday":
        return [yesterday]
    elif period_type == "7days":
        return [yesterday - timedelta(days=i) for i in range(7)]
    elif period_type == "30days":
        return [yesterday - timedelta(days=i) for i in range(30)]
    elif period_type == "custom":
        if not from_date or not to_date:
            raise ValueError("from_date and to_date are required for custom period")
        
        start = datetime.strptime(from_date, "%Y-%m-%d").date()
        end = datetime.strptime(to_date, "%Y-%m-%d").date()
        
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
    else:
        raise ValueError(f"Invalid period_type: {period_type}")