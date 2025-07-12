"""
企業関連のAPIエンドポイント
"""

import math
from datetime import datetime, date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.company import Company, CompanySyncHistory, Sector17Master, Sector33Master, MarketMaster
from app.schemas.company import (
    Company as CompanySchema,
    CompanyList,
    CompanySyncRequest,
    CompanySyncHistory as CompanySyncHistorySchema,
    CompanySyncHistoryList,
    CompanySearchRequest,
    Sector17Master as Sector17MasterSchema,
    Sector33Master as Sector33MasterSchema,
    MarketMaster as MarketMasterSchema
)
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.company_sync_service import CompanySyncService
from app.services.schedule_service import ScheduleService
from app.tasks.company_tasks import sync_listed_companies


router = APIRouter()


def get_data_source_service(db: AsyncSession = Depends(get_session)) -> DataSourceService:
    """データソースサービスを取得"""
    return DataSourceService(db)


def get_jquants_client_manager(
    data_source_service: DataSourceService = Depends(get_data_source_service)
) -> JQuantsClientManager:
    """J-Quantsクライアント管理を取得"""
    return JQuantsClientManager(data_source_service)


def get_company_sync_service(
    db: AsyncSession = Depends(get_session),
    data_source_service: DataSourceService = Depends(get_data_source_service),
    jquants_client_manager: JQuantsClientManager = Depends(get_jquants_client_manager)
) -> CompanySyncService:
    """企業同期サービスを取得"""
    return CompanySyncService(db, data_source_service, jquants_client_manager)


def get_schedule_service(
    db: AsyncSession = Depends(get_session)
) -> ScheduleService:
    """スケジュール管理サービスを取得"""
    return ScheduleService(db)


@router.get("/", response_model=CompanyList)
async def get_companies(
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(50, ge=1, le=1000, description="1ページあたりの件数"),
    code: Optional[str] = Query(None, description="銘柄コード（部分一致）"),
    company_name: Optional[str] = Query(None, description="会社名（部分一致）"),
    sector17_code: Optional[str] = Query(None, description="17業種区分コード"),
    sector33_code: Optional[str] = Query(None, description="33業種区分コード"),
    market_code: Optional[str] = Query(None, description="市場区分コード"),
    is_active: Optional[bool] = Query(None, description="アクティブフラグ"),
    db: AsyncSession = Depends(get_session)
):
    """企業一覧を取得"""
    
    # クエリを構築
    query = select(Company)
    
    # フィルタリング条件を追加
    filters = []
    
    if code:
        filters.append(Company.code.ilike(f"%{code}%"))
    if company_name:
        filters.append(Company.company_name.ilike(f"%{company_name}%"))
    if sector17_code:
        filters.append(Company.sector17_code == sector17_code)
    if sector33_code:
        filters.append(Company.sector33_code == sector33_code)
    if market_code:
        filters.append(Company.market_code == market_code)
    if is_active is not None:
        filters.append(Company.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
    
    # 総件数を取得
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # ページネーション
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    query = query.order_by(Company.code)
    
    # データを取得
    result = await db.execute(query)
    companies = result.scalars().all()
    
    # ページ数を計算
    pages = math.ceil(total / per_page) if total > 0 else 1
    
    return CompanyList(
        items=[CompanySchema.model_validate(company) for company in companies],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{code}", response_model=CompanySchema)
async def get_company(
    code: str,
    db: AsyncSession = Depends(get_session)
):
    """特定の企業情報を取得"""
    
    query = select(Company).where(Company.code == code)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return CompanySchema.model_validate(company)


@router.post("/sync", response_model=CompanySyncHistorySchema)
async def sync_companies(
    request: CompanySyncRequest,
    background_tasks: BackgroundTasks,
    company_sync_service: CompanySyncService = Depends(get_company_sync_service)
):
    """企業データの同期を実行"""
    
    try:
        # バックグラウンドで同期を実行
        sync_history = await company_sync_service.sync_companies(
            data_source_id=request.data_source_id,
            sync_type=request.sync_type
        )
        
        return CompanySyncHistorySchema.model_validate(sync_history)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sync/history", response_model=CompanySyncHistoryList)
async def get_sync_history(
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    status: Optional[str] = Query(None, description="ステータスフィルタ"),
    company_sync_service: CompanySyncService = Depends(get_company_sync_service)
):
    """同期履歴を取得"""
    
    offset = (page - 1) * per_page
    histories, total = await company_sync_service.get_sync_history(
        limit=per_page,
        offset=offset,
        status=status
    )
    
    pages = math.ceil(total / per_page) if total > 0 else 1
    
    return CompanySyncHistoryList(
        items=[CompanySyncHistorySchema.model_validate(history) for history in histories],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/sync/status", response_model=Optional[CompanySyncHistorySchema])
async def get_latest_sync_status(
    company_sync_service: CompanySyncService = Depends(get_company_sync_service)
):
    """最新の同期ステータスを取得"""
    
    latest_sync = await company_sync_service.get_latest_sync_status()
    
    if latest_sync:
        return CompanySyncHistorySchema.model_validate(latest_sync)
    else:
        return None


@router.get("/masters/sectors17", response_model=List[Sector17MasterSchema])
async def get_sector17_masters(
    is_active: Optional[bool] = Query(None, description="アクティブフラグ"),
    db: AsyncSession = Depends(get_session)
):
    """17業種区分マスターを取得"""
    
    query = select(Sector17Master)
    
    if is_active is not None:
        query = query.where(Sector17Master.is_active == is_active)
    
    query = query.order_by(Sector17Master.display_order, Sector17Master.code)
    
    result = await db.execute(query)
    sectors = result.scalars().all()
    
    return [Sector17MasterSchema.model_validate(sector) for sector in sectors]


@router.get("/masters/sectors33", response_model=List[Sector33MasterSchema])
async def get_sector33_masters(
    sector17_code: Optional[str] = Query(None, description="17業種区分コード"),
    is_active: Optional[bool] = Query(None, description="アクティブフラグ"),
    db: AsyncSession = Depends(get_session)
):
    """33業種区分マスターを取得"""
    
    query = select(Sector33Master)
    
    filters = []
    if sector17_code:
        filters.append(Sector33Master.sector17_code == sector17_code)
    if is_active is not None:
        filters.append(Sector33Master.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Sector33Master.display_order, Sector33Master.code)
    
    result = await db.execute(query)
    sectors = result.scalars().all()
    
    return [Sector33MasterSchema.model_validate(sector) for sector in sectors]


@router.get("/masters/markets", response_model=List[MarketMasterSchema])
async def get_market_masters(
    is_active: Optional[bool] = Query(None, description="アクティブフラグ"),
    db: AsyncSession = Depends(get_session)
):
    """市場区分マスターを取得"""
    
    query = select(MarketMaster)
    
    if is_active is not None:
        query = query.where(MarketMaster.is_active == is_active)
    
    query = query.order_by(MarketMaster.display_order, MarketMaster.code)
    
    result = await db.execute(query)
    markets = result.scalars().all()
    
    return [MarketMasterSchema.model_validate(market) for market in markets]


@router.post("/search", response_model=CompanyList)
async def search_companies(
    request: CompanySearchRequest,
    db: AsyncSession = Depends(get_session)
):
    """企業検索（POSTバージョン）"""
    
    # GETエンドポイントのロジックを再利用
    return await get_companies(
        page=request.page,
        per_page=request.per_page,
        code=request.code,
        company_name=request.company_name,
        sector17_code=request.sector17_code,
        sector33_code=request.sector33_code,
        market_code=request.market_code,
        is_active=request.is_active,
        db=db
    )


@router.post("/sync/manual")
async def sync_companies_manual(
    db: AsyncSession = Depends(get_session)
):
    """上場企業一覧を手動で同期"""
    # Celeryタスクを即座に実行（execution_type="manual"を指定）
    task = sync_listed_companies.delay("manual")
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": "同期処理を開始しました"
    }


@router.get("/sync/task/{task_id}")
async def get_sync_task_status(
    task_id: str
):
    """同期タスクの状態を取得"""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    if result.state == 'PENDING':
        response = {
            'state': result.state,
            'current': 0,
            'total': 1,
            'status': '処理待機中...'
        }
    elif result.state == 'PROGRESS':
        response = {
            'state': result.state,
            'current': result.info.get('current', 0),
            'total': result.info.get('total', 1),
            'status': result.info.get('message', '処理中...')
        }
    elif result.state == 'SUCCESS':
        response = {
            'state': result.state,
            'current': 1,
            'total': 1,
            'status': '同期完了',
            'result': result.info
        }
    else:  # FAILURE
        response = {
            'state': result.state,
            'current': 1,
            'total': 1,
            'status': f'エラー: {str(result.info)}',
            'error': str(result.info)
        }
    
    return response


@router.get("/sync/schedule")
async def get_company_sync_schedule(
    schedule_service: ScheduleService = Depends(get_schedule_service),
    db: AsyncSession = Depends(get_session)
):
    """同期スケジュールの状態を取得"""
    # 上場企業一覧エンドポイントのIDを取得
    from app.models.api_endpoint import APIEndpoint
    result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.data_type == "listed_companies")
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Listed companies endpoint not found")
    
    status = await schedule_service.get_schedule_status(endpoint.id)
    return status


@router.post("/sync/schedule")
async def create_company_sync_schedule(
    hour: int = Form(..., ge=0, le=23),
    minute: int = Form(..., ge=0, le=59),
    schedule_service: ScheduleService = Depends(get_schedule_service),
    db: AsyncSession = Depends(get_session)
):
    """同期スケジュールを作成"""
    # 上場企業一覧エンドポイントのIDを取得
    from app.models.api_endpoint import APIEndpoint
    result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.data_type == "listed_companies")
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Listed companies endpoint not found")
    
    try:
        execution_time = time(hour=hour, minute=minute)
        created_schedule = await schedule_service.create_schedule(
            endpoint_id=endpoint.id,
            execution_time=execution_time
        )
        
        return {
            "status": "success",
            "execution_time": created_schedule.execution_time.strftime("%H:%M"),
            "timezone": created_schedule.timezone,
            "message": f"スケジュールを {execution_time.strftime('%H:%M')} で作成しました"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sync/schedule")
async def update_company_sync_schedule(
    hour: int = Form(..., ge=0, le=23),
    minute: int = Form(..., ge=0, le=59),
    schedule_service: ScheduleService = Depends(get_schedule_service),
    db: AsyncSession = Depends(get_session)
):
    """同期スケジュールを更新"""
    # 上場企業一覧エンドポイントのIDを取得
    from app.models.api_endpoint import APIEndpoint
    result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.data_type == "listed_companies")
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Listed companies endpoint not found")
    
    try:
        execution_time = time(hour=hour, minute=minute)
        updated_schedule = await schedule_service.update_schedule_time(
            endpoint_id=endpoint.id,
            execution_time=execution_time
        )
        
        return {
            "status": "success",
            "execution_time": updated_schedule.execution_time.strftime("%H:%M"),
            "timezone": updated_schedule.timezone,
            "message": f"スケジュールを {execution_time.strftime('%H:%M')} に更新しました"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))