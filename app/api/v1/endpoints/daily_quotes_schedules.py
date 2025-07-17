"""
日次株価データ定期実行スケジュールAPIエンドポイント
"""

from datetime import time as datetime_time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.daily_quotes_schedule_service import DailyQuotesScheduleService
from app.schemas.daily_quote_schedule import (
    DailyQuoteScheduleCreate,
    DailyQuoteScheduleUpdate,
    DailyQuoteSchedule as DailyQuoteScheduleSchema,
    DailyQuoteScheduleDetail
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.template_filters import to_jst, to_jst_with_seconds

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# カスタムフィルタを登録
templates.env.filters['to_jst'] = to_jst
templates.env.filters['to_jst_with_seconds'] = to_jst_with_seconds


def get_schedule_service(db: AsyncSession = Depends(get_session)) -> DailyQuotesScheduleService:
    """スケジュールサービスを取得"""
    return DailyQuotesScheduleService(db)


@router.post("/daily-quotes/schedules", response_model=DailyQuoteScheduleSchema)
async def create_schedule(
    schedule_data: DailyQuoteScheduleCreate,
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """定期実行スケジュールを作成"""
    try:
        schedule = await service.create_schedule(
            name=schedule_data.name,
            sync_type=schedule_data.sync_type,
            relative_preset=schedule_data.relative_preset,
            data_source_id=schedule_data.data_source_id,
            schedule_type=schedule_data.schedule_type,
            execution_time=schedule_data.execution_time,
            day_of_week=schedule_data.day_of_week,
            day_of_month=schedule_data.day_of_month,
            description=schedule_data.description,
            is_enabled=schedule_data.is_enabled
        )
        return DailyQuoteScheduleSchema.model_validate(schedule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-quotes/schedules", response_model=List[DailyQuoteScheduleSchema])
async def list_schedules(
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """定期実行スケジュール一覧を取得"""
    schedules = await service.list_schedules()
    return [DailyQuoteScheduleSchema.model_validate(schedule) for schedule in schedules]


@router.get("/daily-quotes/schedules/{schedule_id}", response_model=DailyQuoteScheduleDetail)
async def get_schedule(
    schedule_id: int,
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """定期実行スケジュールの詳細を取得"""
    schedule_info = await service.get_schedule_with_next_run(schedule_id)
    if not schedule_info:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return DailyQuoteScheduleDetail(**schedule_info)


@router.put("/daily-quotes/schedules/{schedule_id}", response_model=DailyQuoteScheduleSchema)
async def update_schedule(
    schedule_id: int,
    schedule_data: DailyQuoteScheduleUpdate,
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """定期実行スケジュールを更新"""
    try:
        # None以外の値のみを含む辞書を作成
        update_data = {k: v for k, v in schedule_data.model_dump().items() if v is not None}
        
        schedule = await service.update_schedule(schedule_id, **update_data)
        return DailyQuoteScheduleSchema.model_validate(schedule)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/daily-quotes/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """定期実行スケジュールを削除"""
    try:
        await service.delete_schedule(schedule_id)
        return {"message": "Schedule deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily-quotes/schedules/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: int,
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """定期実行スケジュールの有効/無効を切り替え"""
    try:
        schedule = await service.toggle_schedule(schedule_id)
        return {
            "id": schedule.id,
            "is_enabled": schedule.is_enabled,
            "message": f"Schedule {'enabled' if schedule.is_enabled else 'disabled'} successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-quotes/schedules/preview/{preset}")
async def preview_date_range(
    preset: str,
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """プリセットの日付範囲をプレビュー"""
    try:
        from_date, to_date = service.calculate_dates_from_preset(preset)
        return {
            "preset": preset,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "days": (to_date - from_date).days + 1
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid preset: {preset}")


@router.get("/daily-quotes/schedules/html/list", response_class=HTMLResponse)
async def get_schedules_html(
    request: Request,
    service: DailyQuotesScheduleService = Depends(get_schedule_service)
):
    """スケジュール一覧をHTMLで取得（HTMX用）"""
    schedules = await service.list_schedules()
    
    # 各スケジュールに次回実行情報を追加
    schedule_details = []
    for schedule in schedules:
        detail = await service.get_schedule_with_next_run(schedule.id)
        schedule_details.append(detail)
    
    context = {
        "request": request,
        "schedules": schedule_details
    }
    
    return templates.TemplateResponse(
        "partials/api_endpoints/daily_quotes_schedule_list.html",
        context
    )