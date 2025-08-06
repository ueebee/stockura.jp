"""Listed info Celery task (Synchronous version)."""
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.infrastructure.celery.app import celery_app
from app.infrastructure.repositories.database.task_log_repository import TaskLogRepository as TaskLogRepositorySync

logger = get_task_logger(__name__)
settings = get_settings()


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


# Create sync database connection
def get_sync_session():
    """Get synchronous database session for Celery tasks."""
    # Convert async URL to sync URL
    db_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


@celery_app.task(bind=True, base=FetchListedInfoTask, name="fetch_listed_info_task_sync")
def fetch_listed_info_task_sync(
    self,
    schedule_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
    period_type: Optional[str] = "yesterday",  # "yesterday", "7days", "30days", "custom"
):
    """
    Fetch listed info data from J-Quants API (Synchronous version).

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
        f"Starting fetch_listed_info_task_sync - task_id: {task_id}, "
        f"schedule_id: {schedule_id}, period_type: {period_type}"
    )

    # Use synchronous implementation
    return _fetch_listed_info_sync(
        task_id=task_id,
        log_id=log_id,
        schedule_id=schedule_id,
        from_date=from_date,
        to_date=to_date,
        codes=codes,
        market=market,
        period_type=period_type,
    )


def _fetch_listed_info_sync(
    task_id: str,
    log_id: UUID,
    schedule_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
    period_type: Optional[str] = "yesterday",
):
    """Synchronous implementation of fetch_listed_info task."""
    from app.application.use_cases.fetch_listed_info_sync import FetchListedInfoUseCaseSync
    from app.infrastructure.external.jquants.jquants_client_sync import JQuantsClientSync
    from app.infrastructure.repositories.database.listed_info_repository_sync import (
        ListedInfoRepositorySync,
    )
    from app.core.logging import get_logger
    from app.domain.entities.task_log import TaskExecutionLog

    session = get_sync_session()
    
    try:
        # Initialize task log
        task_log_repo = TaskLogRepositorySync(session)
        
        # Create task log entry
        task_log = TaskExecutionLog(
            id=log_id,
            schedule_id=UUID(schedule_id) if schedule_id else None,
            task_name="fetch_listed_info_task_sync",
            task_id=task_id,
            started_at=datetime.utcnow(),
            status="running",
        )
        
        task_log_repo.create(task_log)
        session.commit()
        
        try:
            # Calculate date range based on period_type
            target_dates = _calculate_date_range(
                period_type, from_date, to_date
            )
            
            logger.info(f"Processing dates: {target_dates}")
            
            # Initialize dependencies (synchronous versions)
            jquants_client = JQuantsClientSync()
            listed_info_repo = ListedInfoRepositorySync(session)
            app_logger = get_logger(__name__)
            
            use_case = FetchListedInfoUseCaseSync(
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
                        result = use_case.fetch_by_code(
                            code=code, target_date=target_date
                        )
                        if result.success:
                            total_fetched += result.fetched_count
                            total_saved += result.saved_count
                        else:
                            errors.append(f"Code {code}: {result.error_message}")
                else:
                    # Process all codes
                    result = use_case.fetch_and_update_all(
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
            
            task_log_repo.update_status(
                log_id=log_id,
                status=status,
                finished_at=datetime.utcnow(),
                result=result_data,
                error_message="\n".join(errors) if errors else None,
            )
            session.commit()
            
            logger.info(
                f"Task completed - status: {status}, "
                f"fetched: {total_fetched}, saved: {total_saved}"
            )
            
            return result_data
            
        except Exception as e:
            logger.error(f"Task failed with error: {str(e)}")
            
            # Update task log with error
            task_log_repo.update_status(
                log_id=log_id,
                status="failed",
                finished_at=datetime.utcnow(),
                error_message=str(e),
            )
            session.commit()
            
            raise
    finally:
        session.close()


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