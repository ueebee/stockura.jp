"""Schedule management endpoints."""
import json
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.presentation.api.v1.schemas.schedule import (
    ScheduleCreate,
    ScheduleEnableResponse,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
    ScheduleFilter,
    TaskParams,
)
from app.presentation.schemas import SuccessResponse, PaginatedResponse
from app.application.dtos.schedule_dto import (
    ScheduleCreateDto,
    ScheduleUpdateDto,
    TaskParamsDto,
)
from app.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.presentation.dependencies.use_cases import get_manage_schedule_use_case
from app.presentation.dependencies.repositories import get_task_log_repository
from app.presentation.validators.decorators import validate_query_params
from app.domain.repositories.task_log_repository_interface import TaskLogRepositoryInterface

router = APIRouter(prefix="/schedules", tags=["schedules"])
from app.presentation.dependencies.mappers import (
    get_schedule_create_mapper,
    get_schedule_response_mapper,
    get_schedule_update_mapper,
    get_schedule_list_response_mapper,
)
from app.presentation.api.v1.mappers.schedule_mapper import (
    ScheduleCreateMapper,
    ScheduleResponseMapper,
    ScheduleUpdateMapper,
    ScheduleListResponseMapper,
)


# get_manage_schedule_use_case 関数は削除（dependencies モジュールのものを使用）


@router.post("/", response_model=SuccessResponse[ScheduleResponse], status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
    mapper: ScheduleCreateMapper = Depends(get_schedule_create_mapper),
    response_mapper: ScheduleResponseMapper = Depends(get_schedule_response_mapper),
) -> SuccessResponse[ScheduleResponse]:
    """Create a new schedule."""
    # Convert API schema to DTO using mapper
    dto = mapper.schema_to_dto(schedule_data)
    
    # Create schedule
    result = await use_case.create_schedule(dto)
    
    # Convert DTO to API response using mapper
    schedule_response = response_mapper.dto_to_schema(result)
    
    return SuccessResponse(data=schedule_response)


@router.get("/", response_model=PaginatedResponse[ScheduleResponse])
async def list_schedules(
    enabled_only: bool = False,
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    task_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
    list_mapper: ScheduleListResponseMapper = Depends(get_schedule_list_response_mapper),
) -> PaginatedResponse[ScheduleResponse]:
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
    
    # Convert DTOs to API response using mapper
    items = list_mapper.dto_list_to_schema_list(schedules)
    
    # ページネーション処理（簡易版）
    # TODO: 実際のページネーションは UseCase 層で実装する必要がある
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = items[start:end]
    
    return PaginatedResponse.from_data(
        data=paginated_items,
        page=page,
        per_page=per_page,
        total=total
    )


@router.get("/{schedule_id}", response_model=SuccessResponse[ScheduleResponse])
async def get_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
    response_mapper: ScheduleResponseMapper = Depends(get_schedule_response_mapper),
) -> SuccessResponse[ScheduleResponse]:
    """Get schedule by ID."""
    schedule = await use_case.get_schedule(schedule_id)
    
    if not schedule:
        from app.presentation.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Schedule", str(schedule_id))
    
    # Convert DTO to API response using mapper
    schedule_response = response_mapper.dto_to_schema(schedule)
    
    return SuccessResponse(data=schedule_response)


@router.put("/{schedule_id}", response_model=SuccessResponse[ScheduleResponse])
async def update_schedule(
    schedule_id: UUID,
    schedule_data: ScheduleUpdate,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
    mapper: ScheduleUpdateMapper = Depends(get_schedule_update_mapper),
    response_mapper: ScheduleResponseMapper = Depends(get_schedule_response_mapper),
) -> SuccessResponse[ScheduleResponse]:
    """Update schedule."""
    # Convert API schema to DTO using mapper
    dto = mapper.schema_to_dto(schedule_data)
    
    # Update schedule
    result = await use_case.update_schedule(schedule_id, dto)
    
    if not result:
        from app.presentation.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Schedule", str(schedule_id))
    
    # Convert DTO to API response using mapper
    schedule_response = response_mapper.dto_to_schema(result)
    
    return SuccessResponse(data=schedule_response)


@router.delete("/{schedule_id}", response_model=SuccessResponse[Dict[str, str]])
async def delete_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> SuccessResponse[Dict[str, str]]:
    """Delete schedule."""
    success = await use_case.delete_schedule(schedule_id)
    
    if not success:
        from app.presentation.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Schedule", str(schedule_id))
    
    return SuccessResponse(data={"message": f"Schedule {schedule_id} deleted successfully"})


@router.post("/{schedule_id}/enable", response_model=SuccessResponse[ScheduleEnableResponse])
async def enable_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> SuccessResponse[ScheduleEnableResponse]:
    """Enable schedule."""
    success = await use_case.enable_schedule(schedule_id)
    
    if not success:
        from app.presentation.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Schedule", str(schedule_id))
    
    enable_response = ScheduleEnableResponse(
        id=schedule_id,
        enabled=True,
        message=f"Schedule {schedule_id} enabled successfully",
    )
    
    return SuccessResponse(data=enable_response)


@router.post("/{schedule_id}/disable", response_model=SuccessResponse[ScheduleEnableResponse])
async def disable_schedule(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> SuccessResponse[ScheduleEnableResponse]:
    """Disable schedule."""
    success = await use_case.disable_schedule(schedule_id)
    
    if not success:
        from app.presentation.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Schedule", str(schedule_id))
    
    enable_response = ScheduleEnableResponse(
        id=schedule_id,
        enabled=False,
        message=f"Schedule {schedule_id} disabled successfully",
    )
    
    return SuccessResponse(data=enable_response)


@router.post("/trigger/listed-info", response_model=SuccessResponse[Dict[str, Any]])
async def trigger_listed_info_task(
    period_type: str = "yesterday",
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
) -> SuccessResponse[Dict[str, Any]]:
    """Manually trigger listed_info task for testing.
    
    Args:
        period_type: Period type for data fetch (yesterday, 7days, 30days, custom)
        codes: Optional list of stock codes to fetch
        market: Optional market code to filter
    
    Returns:
        Task execution information
    """
    from datetime import datetime
    
    try:
        # 動的インポートで Celery タスクを取得
        from app.infrastructure.celery.tasks.jquants_listed_info_task import fetch_listed_info_task
        
        # タスクを非同期で実行
        result = fetch_listed_info_task.delay(
            schedule_id=None,  # 手動実行なので None
            from_date=None,
            to_date=None,
            codes=codes,
            market=market,
            period_type=period_type,
        )
        
        task_info = {
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
        
        return SuccessResponse(data=task_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}",
        )


@router.get("/tasks/{task_id}/status", response_model=SuccessResponse[Dict[str, Any]])
async def get_task_status(task_id: str) -> SuccessResponse[Dict[str, Any]]:
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
        
        task_status = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
        }
        
        if result.ready():
            if result.successful():
                task_status["result"] = result.result
            else:
                task_status["error"] = str(result.info)
                
        return SuccessResponse(data=task_status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.post("/trigger/listed-info-direct", response_model=SuccessResponse[Dict[str, Any]])
async def trigger_listed_info_direct(
    period_type: str = "yesterday",
    codes: Optional[List[str]] = None,
    market: Optional[str] = None,
    schedule_id: Optional[UUID] = None,
) -> SuccessResponse[Dict[str, Any]]:
    """Directly execute listed_info task without Celery (for testing).
    
    Args:
        period_type: Period type for data fetch (yesterday, 7days, 30days, custom)
        codes: Optional list of stock codes to fetch
        market: Optional market code to filter
    
    Returns:
        Task execution result
    """
    from app.infrastructure.celery.tasks.jquants_listed_info_task import _fetch_listed_info_async
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
        
        task_result = {
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
        
        return SuccessResponse(data=task_result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task: {str(e)}",
        )


@router.get("/{schedule_id}/history", response_model=SuccessResponse[Dict[str, Any]])
async def get_schedule_history(
    schedule_id: UUID,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
    task_log_repo: TaskLogRepositoryInterface = Depends(get_task_log_repository),
) -> SuccessResponse[Dict[str, Any]]:
    """Get execution history for a schedule.
    
    Args:
        schedule_id: Schedule ID
        
    Returns:
        Schedule execution history
    """
    # Verify schedule exists
    schedule = await use_case.get_schedule(schedule_id)
    
    if not schedule:
        from app.presentation.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Schedule", str(schedule_id))
    
    # Get task execution logs
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
    
    history_data = {
        "history": history,
    }
    
    return SuccessResponse(data=history_data)
