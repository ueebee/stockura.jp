"""
株価データ関連のAPIエンドポイント
"""

import math
import json
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.daily_quote import DailyQuote, DailyQuotesSyncHistory
from app.models.company import Company
from app.schemas.daily_quote import (
    DailyQuote as DailyQuoteSchema,
    DailyQuoteList,
    DailyQuoteSearchRequest,
    DailyQuotesSyncRequest,
    DailyQuotesSyncHistory as DailyQuotesSyncHistorySchema,
    DailyQuotesSyncHistoryList,
    DailyQuotesByCodeRequest,
    DailyQuotesByDateRequest,
    DailyQuoteSyncResponse,
    DailyQuoteSyncStatusResponse,
    PaginationInfo
)
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.daily_quotes_sync_service import DailyQuotesSyncService
from app.tasks.daily_quotes_tasks import sync_daily_quotes_task
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.template_filters import to_jst, to_jst_with_seconds


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# カスタムフィルタを登録
templates.env.filters['to_jst'] = to_jst
templates.env.filters['to_jst_with_seconds'] = to_jst_with_seconds


def get_data_source_service(db: AsyncSession = Depends(get_session)) -> DataSourceService:
    """データソースサービスを取得"""
    return DataSourceService(db)


def get_jquants_client_manager(
    data_source_service: DataSourceService = Depends(get_data_source_service)
) -> JQuantsClientManager:
    """J-Quantsクライアント管理を取得"""
    return JQuantsClientManager(data_source_service)


def get_daily_quotes_sync_service(
    data_source_service: DataSourceService = Depends(get_data_source_service),
    jquants_client_manager: JQuantsClientManager = Depends(get_jquants_client_manager)
) -> DailyQuotesSyncService:
    """株価データ同期サービスを取得"""
    return DailyQuotesSyncService(data_source_service, jquants_client_manager)


# ヘルスチェック用エンドポイント
@router.get("/daily-quotes/health")
async def health_check():
    """
    株価データAPIのヘルスチェック
    """
    return {
        "status": "healthy",
        "service": "daily_quotes",
        "timestamp": datetime.utcnow().isoformat()
    }


# 統計情報取得エンドポイント
@router.get("/daily-quotes/stats")
async def get_daily_quotes_stats(
    db: AsyncSession = Depends(get_session)
):
    """
    株価データの統計情報を取得
    """
    try:
        # 総レコード数
        total_records_result = await db.execute(select(func.count(DailyQuote.id)))
        total_records = total_records_result.scalar()
        
        # ユニーク銘柄数
        unique_codes_result = await db.execute(select(func.count(func.distinct(DailyQuote.code))))
        unique_codes = unique_codes_result.scalar()
        
        # 最新取引日
        latest_date_result = await db.execute(select(func.max(DailyQuote.trade_date)))
        latest_date = latest_date_result.scalar()
        
        # 最古取引日
        earliest_date_result = await db.execute(select(func.min(DailyQuote.trade_date)))
        earliest_date = earliest_date_result.scalar()
        
        return {
            "total_records": total_records,
            "unique_codes": unique_codes,
            "latest_date": latest_date.isoformat() if latest_date else None,
            "earliest_date": earliest_date.isoformat() if earliest_date else None,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計情報の取得に失敗しました: {str(e)}")


@router.get("/daily-quotes/{code}", response_model=DailyQuoteList)
async def get_daily_quotes_by_code(
    code: str = Path(..., description="銘柄コード"),
    from_date: Optional[date] = Query(None, description="期間開始日"),
    to_date: Optional[date] = Query(None, description="期間終了日"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: AsyncSession = Depends(get_session)
):
    """
    特定銘柄の株価データを取得
    """
    # クエリを構築
    stmt = select(DailyQuote).where(DailyQuote.code == code)
    
    # 日付範囲フィルタ
    if from_date:
        stmt = stmt.where(DailyQuote.trade_date >= from_date)
    if to_date:
        stmt = stmt.where(DailyQuote.trade_date <= to_date)
    
    # 総件数を取得
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()
    
    # データを取得（日付降順）
    stmt = stmt.order_by(desc(DailyQuote.trade_date)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    quotes = result.scalars().all()
    
    # レスポンスを構築
    return DailyQuoteList(
        data=[DailyQuoteSchema.model_validate(quote) for quote in quotes],
        pagination=PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
    )


@router.get("/daily-quotes", response_model=DailyQuoteList)
async def get_daily_quotes(
    codes: Optional[str] = Query(None, description="銘柄コードリスト（カンマ区切り）"),
    date: Optional[date] = Query(None, description="取引日"),
    market_code: Optional[str] = Query(None, description="市場区分コード"),
    sector17_code: Optional[str] = Query(None, description="17業種区分コード"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: AsyncSession = Depends(get_session)
):
    """
    複数銘柄の株価データを取得
    """
    # クエリを構築
    stmt = select(DailyQuote)
    
    # フィルタ条件を追加
    filters = []
    
    if codes:
        code_list = [code.strip() for code in codes.split(",") if code.strip()]
        if code_list:
            filters.append(DailyQuote.code.in_(code_list))
    
    if date:
        filters.append(DailyQuote.trade_date == date)
    
    # 市場区分・業種フィルタの場合は企業マスターとJOIN
    if market_code or sector17_code:
        stmt = stmt.join(Company, DailyQuote.code == Company.code)
        if market_code:
            filters.append(Company.market_code == market_code)
        if sector17_code:
            filters.append(Company.sector17_code == sector17_code)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # 総件数を取得
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()
    
    # データを取得
    stmt = stmt.order_by(desc(DailyQuote.trade_date), DailyQuote.code).offset(offset).limit(limit)
    result = await db.execute(stmt)
    quotes = result.scalars().all()
    
    # レスポンスを構築
    return DailyQuoteList(
        data=[DailyQuoteSchema.model_validate(quote) for quote in quotes],
        pagination=PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
    )


@router.get("/daily-quotes/by-date/{trade_date}", response_model=DailyQuoteList)
async def get_daily_quotes_by_date(
    trade_date: date = Path(..., description="取引日"),
    limit: int = Query(1000, ge=1, le=10000, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: AsyncSession = Depends(get_session)
):
    """
    特定日の全銘柄株価データを取得
    """
    # クエリを構築
    stmt = select(DailyQuote).where(DailyQuote.trade_date == trade_date)
    
    # 総件数を取得
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()
    
    # データを取得（銘柄コード順）
    stmt = stmt.order_by(DailyQuote.code).offset(offset).limit(limit)
    result = await db.execute(stmt)
    quotes = result.scalars().all()
    
    # レスポンスを構築
    return DailyQuoteList(
        data=[DailyQuoteSchema.model_validate(quote) for quote in quotes],
        pagination=PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
    )


@router.post("/daily-quotes/sync", response_model=DailyQuoteSyncResponse)
async def sync_daily_quotes(
    request: DailyQuotesSyncRequest,
    background_tasks: BackgroundTasks,
    sync_service: DailyQuotesSyncService = Depends(get_daily_quotes_sync_service)
):
    """
    株価データ同期を実行
    """
    try:
        # バックグラウンドタスクとして同期を実行
        background_tasks.add_task(
            _execute_sync,
            sync_service,
            request.data_source_id,
            request.sync_type,
            request.target_date,
            request.from_date,
            request.to_date,
            request.codes
        )
        
        return DailyQuoteSyncResponse(
            sync_id=0,  # バックグラウンドタスクのため、後で実際のIDを返すように修正が必要
            message=f"株価データ同期を開始しました（タイプ: {request.sync_type}）",
            status="queued"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同期開始に失敗しました: {str(e)}")


async def _execute_sync(
    sync_service: DailyQuotesSyncService,
    data_source_id: int,
    sync_type: str,
    target_date: Optional[date],
    from_date: Optional[date],
    to_date: Optional[date],
    codes: Optional[List[str]]
):
    """
    同期処理を実行（バックグラウンドタスク）
    """
    try:
        await sync_service.sync_daily_quotes(
            data_source_id=data_source_id,
            sync_type=sync_type,
            target_date=target_date,
            from_date=from_date,
            to_date=to_date,
            specific_codes=codes
        )
    except Exception as e:
        # ログに記録（実際の実装では適切なログシステムを使用）
        print(f"Background sync failed: {e}")


@router.get("/daily-quotes/sync/history", response_model=DailyQuotesSyncHistoryList)
async def get_sync_history(
    limit: int = Query(50, ge=1, le=200, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    status: Optional[str] = Query(None, description="ステータスフィルタ"),
    sync_service: DailyQuotesSyncService = Depends(get_daily_quotes_sync_service),
    db: AsyncSession = Depends(get_session)
):
    """
    株価データ同期履歴を取得
    """
    try:
        # 総件数を取得
        count_stmt = select(func.count(DailyQuotesSyncHistory.id))
        if status:
            count_stmt = count_stmt.where(DailyQuotesSyncHistory.status == status)
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 履歴を取得
        histories = await sync_service.get_sync_history(
            limit=limit,
            offset=offset,
            status=status
        )
        
        # ページ数を計算
        pages = math.ceil(total / limit) if limit > 0 else 0
        current_page = (offset // limit) + 1 if limit > 0 else 1
        
        return DailyQuotesSyncHistoryList(
            items=[DailyQuotesSyncHistorySchema.model_validate(history) for history in histories],
            total=total,
            page=current_page,
            per_page=limit,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同期履歴の取得に失敗しました: {str(e)}")


@router.get("/daily-quotes/sync/status/{sync_id}", response_model=DailyQuoteSyncStatusResponse)
async def get_sync_status(
    sync_id: int = Path(..., description="同期履歴ID"),
    sync_service: DailyQuotesSyncService = Depends(get_daily_quotes_sync_service)
):
    """
    特定の同期ステータスを取得
    """
    try:
        sync_history = await sync_service.get_sync_status(sync_id)
        
        if not sync_history:
            raise HTTPException(status_code=404, detail="同期履歴が見つかりません")
        
        # 進捗率を計算
        progress_percentage = None
        if sync_history.status == "completed":
            progress_percentage = 100.0
        elif sync_history.status == "running" and sync_history.total_records:
            processed = (sync_history.new_records or 0) + (sync_history.updated_records or 0) + (sync_history.skipped_records or 0)
            progress_percentage = (processed / sync_history.total_records) * 100
        
        return DailyQuoteSyncStatusResponse(
            sync_history=DailyQuotesSyncHistorySchema.model_validate(sync_history),
            is_running=sync_history.status == "running",
            progress_percentage=progress_percentage,
            estimated_completion=None  # 実装が必要な場合は計算ロジックを追加
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同期ステータスの取得に失敗しました: {str(e)}")


@router.post("/daily-quotes/sync/manual")
async def sync_daily_quotes_manual(
    sync_type: str = Query(..., description="同期タイプ (full/incremental/single_stock)"),
    data_source_id: int = Query(..., description="データソースID"),
    target_date: Optional[date] = Query(None, description="対象日 (incremental時)"),
    from_date: Optional[date] = Query(None, description="開始日 (full時)"),
    to_date: Optional[date] = Query(None, description="終了日 (full時)"),
    codes: Optional[str] = Query(None, description="銘柄コード (single_stock時、カンマ区切り)"),
    db: AsyncSession = Depends(get_session)
):
    """日時株価データを手動で同期"""
    
    # パラメータ検証
    if sync_type == "single_stock" and not codes:
        raise HTTPException(status_code=400, detail="single_stock同期には銘柄コードが必要です")
    
    # 銘柄コードリストに変換
    code_list = None
    if codes:
        code_list = [code.strip() for code in codes.split(",") if code.strip()]
    
    # Celeryタスクを即座に実行
    task = sync_daily_quotes_task.delay(
        data_source_id=data_source_id,
        sync_type=sync_type,
        target_date=target_date.isoformat() if target_date else None,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
        codes=code_list
    )
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": f"日時株価データの{sync_type}同期を開始しました",
        "parameters": {
            "sync_type": sync_type,
            "data_source_id": data_source_id,
            "target_date": target_date.isoformat() if target_date else None,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "codes": code_list
        }
    }


@router.get("/daily-quotes/sync/task/{task_id}")
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
            'status': '処理待機中...',
            'message': '同期処理の準備中です'
        }
    elif result.state == 'PROGRESS':
        response = {
            'state': result.state,
            'current': result.info.get('current', 0),
            'total': result.info.get('total', 1),
            'status': result.info.get('status', '処理中...'),
            'message': result.info.get('message', ''),
            'sync_type': result.info.get('sync_type', ''),
            'processed_dates': result.info.get('processed_dates', 0),
            'new_records': result.info.get('new_records', 0),
            'updated_records': result.info.get('updated_records', 0)
        }
    elif result.state == 'SUCCESS':
        response = {
            'state': result.state,
            'current': 1,
            'total': 1,
            'status': '同期完了',
            'message': '日時株価データの同期が正常に完了しました',
            'result': result.info
        }
    else:  # FAILURE
        response = {
            'state': result.state,
            'current': 1,
            'total': 1,
            'status': f'エラー: {str(result.info)}',
            'error': str(result.info),
            'message': '同期処理中にエラーが発生しました'
        }
    
    return response


@router.get("/daily-quotes/sync/history/html", response_class=HTMLResponse)
async def get_sync_history_html(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="取得件数"),
    sync_service: DailyQuotesSyncService = Depends(get_daily_quotes_sync_service)
):
    """株価データ同期履歴をHTMLで取得（HTMX用）"""
    
    histories = await sync_service.get_sync_history(
        limit=limit,
        offset=0
    )
    
    context = {
        "request": request,
        "histories": histories
    }
    
    return templates.TemplateResponse(
        "partials/api_endpoints/daily_quotes_sync_history_rows.html",
        context
    )


