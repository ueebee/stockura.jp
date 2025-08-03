"""Schedule management endpoints."""
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
from app.application.dto.schedule_dto import (
    ScheduleCreateDto,
    ScheduleUpdateDto,
    TaskParamsDto,
)
from app.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.infrastructure.database.connection import get_session
from app.infrastructure.repositories.schedule_repository import ScheduleRepository

router = APIRouter(prefix="/schedules", tags=["schedules"])


async def get_manage_schedule_use_case(
    session: AsyncSession = Depends(get_session),
) -> ManageScheduleUseCase:
    """Get manage schedule use case."""
    repository = ScheduleRepository(session)
    return ManageScheduleUseCase(repository)


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