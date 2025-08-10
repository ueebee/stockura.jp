"""listed_info スケジュール管理 API エンドポイント"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.listed_info_schedule_dto import (
    CreateListedInfoScheduleDTO,
    ListedInfoScheduleDTO,
    ListedInfoScheduleListDTO,
    ScheduleHistoryDTO,
    UpdateListedInfoScheduleDTO,
)
from app.application.use_cases.manage_listed_info_schedule import (
    ManageListedInfoScheduleUseCase,
)
from app.domain.entities.schedule import Schedule
from app.domain.exceptions.schedule_exceptions import (
    ScheduleConflictException,
    ScheduleNotFoundException,
    ScheduleValidationException,
)
from app.infrastructure.database.connection import get_db_session as get_db
from app.infrastructure.repositories.database.schedule_repository_impl import (
    ScheduleRepositoryImpl,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules/listed-info", tags=["listed_info_schedules"])


def get_use_case(db: AsyncSession = Depends(get_db)) -> ManageListedInfoScheduleUseCase:
    """ユースケースの依存性注入"""
    schedule_repository = ScheduleRepositoryImpl(db)
    return ManageListedInfoScheduleUseCase(schedule_repository)


def schedule_to_dto(schedule: Schedule) -> ListedInfoScheduleDTO:
    """Schedule エンティティを DTO に変換"""
    return ListedInfoScheduleDTO(
        id=schedule.id,
        name=schedule.name,
        task_name=schedule.task_name,
        cron_expression=schedule.cron_expression,
        enabled=schedule.enabled,
        kwargs=schedule.kwargs,
        description=schedule.description,
        category=schedule.category,
        tags=schedule.tags,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        next_run_at=getattr(schedule, "next_run_at", None),
        last_run_at=getattr(schedule, "last_run_at", None),
    )


@router.post(
    "/",
    response_model=ListedInfoScheduleDTO,
    status_code=status.HTTP_201_CREATED,
    summary="listed_info スケジュールを作成",
    description="新しい listed_info データ取得スケジュールを作成します。",
)
async def create_listed_info_schedule(
    request: CreateListedInfoScheduleDTO,
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case),
) -> ListedInfoScheduleDTO:
    """
    listed_info スケジュールを作成する
    
    - **name**: スケジュール名（一意である必要があります）
    - **cron_expression**: cron 形式の実行スケジュール（例: "0 9 * * *"）
    - **period_type**: データ取得期間（yesterday, 7days, 30days, custom）
    - **preset_name**: プリセット名（指定時は cron_expression より優先）
    """
    try:
        schedule = await use_case.create_schedule(
            name=request.name,
            cron_expression=request.cron_expression,
            period_type=request.period_type,
            description=request.description,
            enabled=request.enabled,
            codes=request.codes,
            market=request.market,
            preset_name=request.preset_name,
            from_date=request.from_date,
            to_date=request.to_date,
        )
        return schedule_to_dto(schedule)
    except ScheduleConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ScheduleValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("スケジュール作成中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="スケジュールの作成に失敗しました",
        )


@router.get(
    "/",
    response_model=ListedInfoScheduleListDTO,
    summary="listed_info スケジュール一覧を取得",
    description="登録されている listed_info スケジュールの一覧を取得します。",
)
async def list_listed_info_schedules(
    enabled_only: bool = Query(False, description="有効なスケジュールのみ取得"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数上限"),
    offset: int = Query(0, ge=0, description="オフセット"),
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case),
) -> ListedInfoScheduleListDTO:
    """
    listed_info スケジュール一覧を取得する
    
    - **enabled_only**: True の場合、有効なスケジュールのみ返します
    - **limit**: 取得件数の上限（1-1000）
    - **offset**: ページネーション用のオフセット
    """
    try:
        schedules = await use_case.list_schedules(
            category="listed_info",
            enabled_only=enabled_only,
            limit=limit,
            offset=offset,
        )
        
        # 総件数を取得（簡易実装）
        total = len(schedules)
        
        return ListedInfoScheduleListDTO(
            schedules=[schedule_to_dto(s) for s in schedules],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.exception("スケジュール一覧取得中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="スケジュール一覧の取得に失敗しました",
        )


@router.get(
    "/{schedule_id}",
    response_model=ListedInfoScheduleDTO,
    summary="listed_info スケジュールの詳細を取得",
    description="指定された ID の listed_info スケジュールの詳細を取得します。",
)
async def get_listed_info_schedule(
    schedule_id: UUID,
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case),
) -> ListedInfoScheduleDTO:
    """
    指定された ID の listed_info スケジュールを取得する
    """
    try:
        schedule = await use_case.get_schedule(schedule_id)
        return schedule_to_dto(schedule)
    except ScheduleNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("スケジュール取得中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="スケジュールの取得に失敗しました",
        )


@router.put(
    "/{schedule_id}",
    response_model=ListedInfoScheduleDTO,
    summary="listed_info スケジュールを更新",
    description="指定された ID の listed_info スケジュールを更新します。",
)
async def update_listed_info_schedule(
    schedule_id: UUID,
    request: UpdateListedInfoScheduleDTO,
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case),
) -> ListedInfoScheduleDTO:
    """
    listed_info スケジュールを更新する
    
    指定されたフィールドのみが更新されます。
    """
    try:
        schedule = await use_case.update_schedule(
            schedule_id=schedule_id,
            name=request.name,
            cron_expression=request.cron_expression,
            period_type=request.period_type,
            description=request.description,
            enabled=request.enabled,
            codes=request.codes,
            market=request.market,
        )
        return schedule_to_dto(schedule)
    except ScheduleNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ScheduleConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ScheduleValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("スケジュール更新中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="スケジュールの更新に失敗しました",
        )


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="listed_info スケジュールを削除",
    description="指定された ID の listed_info スケジュールを削除します。",
)
async def delete_listed_info_schedule(
    schedule_id: UUID,
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case),
) -> None:
    """
    listed_info スケジュールを削除する
    """
    try:
        await use_case.delete_schedule(schedule_id)
    except ScheduleNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("スケジュール削除中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="スケジュールの削除に失敗しました",
        )


@router.post(
    "/{schedule_id}/toggle",
    response_model=ListedInfoScheduleDTO,
    summary="listed_info スケジュールの有効/無効を切り替え",
    description="指定された ID の listed_info スケジュールの有効/無効を切り替えます。",
)
async def toggle_listed_info_schedule(
    schedule_id: UUID,
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case),
) -> ListedInfoScheduleDTO:
    """
    listed_info スケジュールの有効/無効を切り替える
    """
    try:
        schedule = await use_case.toggle_schedule(schedule_id)
        return schedule_to_dto(schedule)
    except ScheduleNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("スケジュール切り替え中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="スケジュールの切り替えに失敗しました",
        )


@router.get(
    "/{schedule_id}/history",
    response_model=ScheduleHistoryDTO,
    summary="listed_info スケジュールの実行履歴を取得",
    description="指定された ID の listed_info スケジュールの実行履歴を取得します。",
)
async def get_listed_info_schedule_history(
    schedule_id: UUID,
    limit: int = Query(100, ge=1, le=1000, description="取得件数上限"),
    offset: int = Query(0, ge=0, description="オフセット"),
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case),
) -> ScheduleHistoryDTO:
    """
    listed_info スケジュールの実行履歴を取得する
    """
    try:
        history = await use_case.get_schedule_history(
            schedule_id=schedule_id,
            limit=limit,
            offset=offset,
        )
        
        return ScheduleHistoryDTO(
            schedule_id=schedule_id,
            history=history,
            total=len(history),
            limit=limit,
            offset=offset,
        )
    except ScheduleNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("実行履歴取得中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="実行履歴の取得に失敗しました",
        )


@router.get(
    "/presets/list",
    summary="利用可能なプリセット一覧を取得",
    description="利用可能な cron 式プリセットの一覧を取得します。",
)
async def list_schedule_presets() -> dict:
    """
    利用可能なスケジュールプリセット一覧を取得する
    """
    from app.domain.helpers.schedule_presets import list_presets
    
    try:
        return {
            "presets": list_presets()
        }
    except Exception as e:
        logger.exception("プリセット一覧取得中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プリセット一覧の取得に失敗しました",
        )