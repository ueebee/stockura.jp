"""Schedule management endpoints."""
import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.presentation.api.v1.schemas.schedule import (
    ScheduleCreate,
    ScheduleEnableResponse,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
    ScheduleFilter,
    TaskParams,
)
from app.application.dtos.schedule_dto import (
    ScheduleCreateDto,
    ScheduleUpdateDto,
    TaskParamsDto,
)
from app.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.infrastructure.database.connection import get_session
from app.infrastructure.di.providers import get_schedule_event_publisher
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher
from app.infrastructure.repositories.database.schedule_repository import ScheduleRepositoryImpl
from app.infrastructure.repositories.database.task_log_repository import TaskLogRepository

router = APIRouter(prefix="/schedules", tags=["schedules"])


async def get_manage_schedule_use_case(
    session: AsyncSession = Depends(get_session),
    event_publisher: Optional[ScheduleEventPublisher] = Depends(get_schedule_event_publisher),
) -> ManageScheduleUseCase:
    """Get manage schedule use case."""
    repository = ScheduleRepositoryImpl(session)
    return ManageScheduleUseCase(repository, event_publisher=event_publisher)


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> ScheduleResponse:
    """Create a new schedule."""
    # Convert API schema to DTO
    task_params_dto = None
    if schedule_data.task_params:
        task_params_dto = TaskParamsDto(
            period_type=schedule_data.task_params.period_type,
            from_date=schedule_data.task_params.from_date,
            to_date=schedule_data.task_params.to_date,
            codes=schedule_data.task_params.codes,
            market=schedule_data.task_params.market,
        )
    
    dto = ScheduleCreateDto(
        name=schedule_data.name,
        task_name=schedule_data.task_name,
        cron_expression=schedule_data.cron_expression,
        enabled=schedule_data.enabled,
        description=schedule_data.description,
        task_params=task_params_dto,
        category=schedule_data.category,
        tags=schedule_data.tags,
        execution_policy=schedule_data.execution_policy,
    )
    
    # Create schedule
    result = await use_case.create_schedule(dto)
    
    # Convert DTO to API response
    return ScheduleResponse(
        id=result.id,
        name=result.name,
        task_name=result.task_name,
        cron_expression=result.cron_expression,
        enabled=result.enabled,
        description=result.description,
        category=result.category,
        tags=result.tags,
        execution_policy=result.execution_policy,
        auto_generated_name=result.auto_generated_name,
        created_at=result.created_at,
        updated_at=result.updated_at,
        task_params=TaskParams(
            period_type=result.task_params.period_type,
            from_date=result.task_params.from_date,
            to_date=result.task_params.to_date,
            codes=result.task_params.codes,
            market=result.task_params.market,
        ) if result.task_params else TaskParams(),
    )


@router.get("/", response_model=ScheduleListResponse)
async def list_schedules(
    enabled_only: bool = False,
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    task_name: Optional[str] = None,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> ScheduleListResponse:
    """List all schedules with optional filters."""
    # If any filter is provided, use filtered search
    if category or tags or task_name:
        schedules = await use_case.get_filtered_schedules(
            category=category,
            tags=tags,
            task_name=task_name,
            enabled_only=enabled_only,
        )
    else:
        schedules = await use_case.get_all_schedules(enabled_only=enabled_only)
    
    items = []
    for schedule in schedules:
        try:
            items.append(
            ScheduleResponse(
                id=schedule.id,
                name=schedule.name,
                task_name=schedule.task_name,
                cron_expression=schedule.cron_expression,
                enabled=schedule.enabled,
                description=schedule.description,
                category=schedule.category,
                tags=schedule.tags,
                execution_policy=schedule.execution_policy,
                auto_generated_name=schedule.auto_generated_name,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at,
                task_params=TaskParams(
                    period_type=schedule.task_params.period_type,
                    from_date=schedule.task_params.from_date,
                    to_date=schedule.task_params.to_date,
                    codes=schedule.task_params.codes,
                    market=schedule.task_params.market,
                ) if schedule.task_params else None,
            )
        )
        except Exception as e:
            # Skip schedules that fail to process
            continue
    
    return ScheduleListResponse(items=items, total=len(items))


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> ScheduleResponse:
    """Get schedule by ID."""
    schedule = await use_case.get_schedule(schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        task_name=schedule.task_name,
        cron_expression=schedule.cron_expression,
        enabled=schedule.enabled,
        description=schedule.description,
        category=schedule.category,
        tags=schedule.tags,
        execution_policy=schedule.execution_policy,
        auto_generated_name=schedule.auto_generated_name,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        task_params=TaskParams(
            period_type=schedule.task_params.period_type,
            from_date=schedule.task_params.from_date,
            to_date=schedule.task_params.to_date,
            codes=schedule.task_params.codes,
            market=schedule.task_params.market,
        ) if schedule.task_params else TaskParams(),
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    schedule_data: ScheduleUpdate,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> ScheduleResponse:
    """Update schedule."""
    # Convert API schema to DTO
    task_params_dto = None
    if schedule_data.task_params:
        task_params_dto = TaskParamsDto(
            period_type=schedule_data.task_params.period_type,
            from_date=schedule_data.task_params.from_date,
            to_date=schedule_data.task_params.to_date,
            codes=schedule_data.task_params.codes,
            market=schedule_data.task_params.market,
        )
    
    dto = ScheduleUpdateDto(
        name=schedule_data.name,
        cron_expression=schedule_data.cron_expression,
        enabled=schedule_data.enabled,
        description=schedule_data.description,
        task_params=task_params_dto,
        category=schedule_data.category,
        tags=schedule_data.tags,
        execution_policy=schedule_data.execution_policy,
    )
    
    # Update schedule
    result = await use_case.update_schedule(schedule_id, dto)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    
    return ScheduleResponse(
        id=result.id,
        name=result.name,
        task_name=result.task_name,
        cron_expression=result.cron_expression,
        enabled=result.enabled,
        description=result.description,
        category=result.category,
        tags=result.tags,
        execution_policy=result.execution_policy,
        auto_generated_name=result.auto_generated_name,
        created_at=result.created_at,
        updated_at=result.updated_at,
        task_params=TaskParams(
            period_type=result.task_params.period_type,
            from_date=result.task_params.from_date,
            to_date=result.task_params.to_date,
            codes=result.task_params.codes,
            market=result.task_params.market,
        ) if result.task_params else TaskParams(),
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> None:
    """Delete schedule."""
    success = await use_case.delete_schedule(schedule_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )


@router.post("/{schedule_id}/enable", response_model=ScheduleEnableResponse)
async def enable_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> ScheduleEnableResponse:
    """Enable schedule."""
    success = await use_case.enable_schedule(schedule_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    
    return ScheduleEnableResponse(
        id=schedule_id,
        enabled=True,
        message=f"Schedule {schedule_id} enabled successfully",
    )


@router.post("/{schedule_id}/disable", response_model=ScheduleEnableResponse)
async def disable_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> ScheduleEnableResponse:
    """Disable schedule."""
    success = await use_case.disable_schedule(schedule_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    
    return ScheduleEnableResponse(
        id=schedule_id,
        enabled=False,
        message=f"Schedule {schedule_id} disabled successfully",
    )


@router.post("/trigger/listed-info", response_model=dict)
async def trigger_listed_info_task(
    period_type: str = "yesterday",
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
) -> dict:
    """Manually trigger listed_info task for testing.
    
    Args:
        period_type: Period type for data fetch (yesterday, 7days, 30days, custom)
        codes: Optional list of stock codes to fetch
        market: Optional market code to filter
    
    Returns:
        Task execution information
    """
    from app.infrastructure.celery.tasks.listed_info_task import fetch_listed_info_task
    from datetime import datetime
    
    try:
        # タスクを非同期で実行
        result = fetch_listed_info_task.delay(
            schedule_id=None,  # 手動実行なので None
            from_date=None,
            to_date=None,
            codes=codes,
            market=market,
            period_type=period_type,
        )
        
        return {
            "task_id": result.id,
            "status": "PENDING",
            "message": "Task submitted successfully",
            "parameters": {
                "period_type": period_type,
                "codes": codes,
                "market": market,
            },
            "submitted_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}",
        )


@router.get("/tasks/{task_id}/status", response_model=dict)
async def get_task_status(task_id: str) -> dict:
    """Get status of a Celery task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status information
    """
    from celery.result import AsyncResult
    from app.infrastructure.celery.app import celery_app
    
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
        }
        
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info)
                
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.post("/trigger/listed-info-direct", response_model=dict)
async def trigger_listed_info_direct(
    period_type: str = "yesterday",
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
    schedule_id: Optional[UUID] = None,
) -> dict:
    """Directly execute listed_info task without Celery (for testing).
    
    Args:
        period_type: Period type for data fetch (yesterday, 7days, 30days, custom)
        codes: Optional list of stock codes to fetch
        market: Optional market code to filter
    
    Returns:
        Task execution result
    """
    from app.infrastructure.celery.tasks.listed_info_task import _fetch_listed_info_async
    from datetime import datetime
    from uuid import uuid4
    
    try:
        task_id = str(uuid4())
        log_id = uuid4()
        
        # タスクを直接実行（Celery を経由しない）
        result = await _fetch_listed_info_async(
            task_id=task_id,
            log_id=log_id,
            schedule_id=str(schedule_id) if schedule_id else None,
            from_date=None,
            to_date=None,
            codes=codes,
            market=market,
            period_type=period_type,
        )
        
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "message": "Task executed directly (without Celery)",
            "parameters": {
                "period_type": period_type,
                "codes": codes,
                "market": market,
            },
            "result": result,
            "executed_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task: {str(e)}",
        )


@router.get("/{schedule_id}/history", response_model=dict)
async def get_schedule_history(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get execution history for a schedule.
    
    Args:
        schedule_id: Schedule ID
        
    Returns:
        Schedule execution history
    """
    # Verify schedule exists
    schedule = await use_case.get_schedule(schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    
    # Get task execution logs
    task_log_repo = TaskLogRepository(session)
    logs = await task_log_repo.get_by_schedule_id(schedule_id, limit=100)
    
    # Convert logs to history format expected by test script
    history = []
    for log in logs:
        history_item = {
            "executed_at": log.started_at.isoformat(),
            "status": log.status,
            "result": json.dumps(log.result) if log.result else None,
            "error": log.error_message,
        }
        history.append(history_item)
    
    return {
        "history": history,
    }
