"""
APIエンドポイント管理のビュー
"""
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from fastapi.templating import Jinja2Templates

from app.db.session import get_db
from app.models import DataSource, APIEndpoint, APIEndpointExecutionLog, APIEndpointSchedule, EndpointDataType, ExecutionMode
from app.models.daily_quote_schedule import DailyQuoteSchedule
from app.models.daily_quote import DailyQuotesSyncHistory
from app.core.template_filters import to_jst, to_jst_with_seconds

# 分離したモジュールからインポート
from .api_endpoints.base import (
    get_endpoint_schedule_info,
    get_endpoint_execution_stats,
    create_initial_endpoints
)
from .api_endpoints.query_optimizer import (
    get_batch_schedule_info,
    get_batch_execution_stats
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# カスタムフィルタを登録
templates.env.filters['to_jst'] = to_jst
templates.env.filters['to_jst_with_seconds'] = to_jst_with_seconds


@router.get("/data-sources/{data_source_id}/endpoints", response_class=HTMLResponse)
async def get_endpoints(
    request: Request,
    data_source_id: int,
    db: Session = Depends(get_db)
):
    """APIエンドポイント管理画面を表示"""
    # データソースを取得
    data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # エンドポイント一覧を取得（データ種別で並び替え）
    endpoints = db.query(APIEndpoint).filter(
        APIEndpoint.data_source_id == data_source_id
    ).order_by(
        APIEndpoint.data_type,
        APIEndpoint.id
    ).all()
    
    # エンドポイントがない場合は初期データを作成
    if not endpoints:
        endpoints = create_initial_endpoints(db, data_source)
    
    # バッチクエリで各エンドポイントのスケジュール情報と実行統計を取得（N+1問題を回避）
    endpoint_schedules = get_batch_schedule_info(db, endpoints)
    endpoint_stats = get_batch_execution_stats(db, endpoints)
    
    context = {
        "request": request,
        "data_source": data_source,
        "endpoints": endpoints,
        "endpoint_schedules": endpoint_schedules,
        "endpoint_stats": endpoint_stats,
        "data_types": EndpointDataType,
        "execution_modes": ExecutionMode
    }
    
    return templates.TemplateResponse("pages/api_endpoints.html", context)


@router.get("/data-sources/{data_source_id}/endpoints/{endpoint_id}/details", response_class=HTMLResponse)
async def get_endpoint_details(
    request: Request,
    data_source_id: int,
    endpoint_id: int,
    db: Session = Depends(get_db),
):
    """エンドポイント詳細を取得（HTMX用）"""
    endpoint = db.query(APIEndpoint).filter(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.data_source_id == data_source_id
    ).first()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    # 最新の実行ログを取得
    recent_logs = db.query(APIEndpointExecutionLog).filter(
        APIEndpointExecutionLog.endpoint_id == endpoint_id
    ).order_by(APIEndpointExecutionLog.started_at.desc()).limit(5).all()
    
    # スケジュール情報を取得（上場企業一覧の場合）
    schedule = None
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        schedule = db.query(APIEndpointSchedule).filter(
            APIEndpointSchedule.endpoint_id == endpoint_id
        ).first()
    
    # 日時株価データの場合、データソース一覧を取得
    data_sources = []
    if endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        data_sources = db.query(DataSource).filter(
            DataSource.provider_type == 'jquants',
            DataSource.is_enabled == True
        ).all()
    
    context = {
        "request": request,
        "endpoint": endpoint,
        "recent_logs": recent_logs,
        "execution_logs": recent_logs,  # テンプレート互換性のため
        "schedule": schedule,
        "data_types": EndpointDataType,
        "execution_modes": ExecutionMode,
        "data_sources": data_sources  # 日時株価データ用
    }
    
    # データ種別に応じた詳細テンプレートを選択
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        template_name = "partials/api_endpoints/endpoint_details_companies.html"
    elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        template_name = "partials/api_endpoints/endpoint_details_daily_quotes.html"
    else:
        template_name = "partials/api_endpoints/endpoint_details.html"
    
    return templates.TemplateResponse(template_name, context)


@router.get("/data-sources/{data_source_id}/endpoints/{endpoint_id}/execution-history", response_class=HTMLResponse)
async def get_endpoint_execution_history(
    request: Request,
    data_source_id: int,
    endpoint_id: int,
    db: Session = Depends(get_db),
):
    """エンドポイントの実行履歴のみを取得（HTMX用）"""
    endpoint = db.query(APIEndpoint).filter(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.data_source_id == data_source_id
    ).first()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    # エンドポイントタイプによって異なる履歴を取得
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        # 企業データ同期履歴を取得
        from app.models.company import CompanySyncHistory
        histories = db.query(CompanySyncHistory).order_by(
            CompanySyncHistory.started_at.desc()
        ).limit(10).all()
        
        context = {
            "request": request,
            "histories": histories
        }
        
        return templates.TemplateResponse(
            "partials/api_endpoints/companies_sync_history_rows.html", 
            context
        )
    else:
        # 通常の実行ログを取得
        execution_logs = db.query(APIEndpointExecutionLog).filter(
            APIEndpointExecutionLog.endpoint_id == endpoint_id
        ).order_by(APIEndpointExecutionLog.started_at.desc()).limit(5).all()
        
        context = {
            "request": request,
            "endpoint": endpoint,
            "execution_logs": execution_logs
        }
        
        return templates.TemplateResponse(
            "partials/api_endpoints/execution_history_rows.html", 
            context
        )


@router.post("/data-sources/{data_source_id}/endpoints/{endpoint_id}/toggle", response_class=HTMLResponse)
async def toggle_endpoint(
    request: Request,
    data_source_id: int,
    endpoint_id: int,
    db: Session = Depends(get_db),
):
    """エンドポイントの有効/無効を切り替え（HTMX用）"""
    endpoint = db.query(APIEndpoint).filter(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.data_source_id == data_source_id
    ).first()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    # 有効/無効を切り替え
    endpoint.is_enabled = not endpoint.is_enabled
    endpoint.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(endpoint)
    
    # スケジュール情報と実行統計を取得
    schedule_info = get_endpoint_schedule_info(db, endpoint)
    stats = get_endpoint_execution_stats(db, endpoint)
    
    context = {
        "request": request,
        "endpoint": endpoint,
        "endpoint_schedules": {endpoint.id: schedule_info},
        "endpoint_stats": {endpoint.id: stats}
    }
    
    return templates.TemplateResponse("partials/api_endpoints/endpoint_row.html", context)


@router.post("/data-sources/{data_source_id}/endpoints/{endpoint_id}/execute", response_class=HTMLResponse)
async def execute_endpoint(
    request: Request,
    data_source_id: int,
    endpoint_id: int,
    test_mode: bool = Form(False),
    db: Session = Depends(get_db),
):
    """エンドポイントを手動実行（HTMX用） - 各エンドポイントタイプに応じた処理を振り分け"""
    endpoint = db.query(APIEndpoint).filter(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.data_source_id == data_source_id
    ).first()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    if not endpoint.is_enabled:
        raise HTTPException(status_code=400, detail="Endpoint is disabled")
    
    # エンドポイントのタイプに応じて適切なハンドラーにリダイレクト
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        # 企業一覧用のエンドポイントハンドラーを呼び出す
        from app.api.v1.views.api_endpoints.companies import execute_companies_endpoint
        return await execute_companies_endpoint(request, data_source_id, endpoint_id, test_mode, db)
    elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        # 日次株価用のエンドポイントハンドラーを呼び出す
        from app.api.v1.views.api_endpoints.daily_quotes import execute_daily_quotes_endpoint
        return await execute_daily_quotes_endpoint(request, data_source_id, endpoint_id, test_mode, db)
    else:
        # その他のエンドポイントは汎用的な処理
        execution_log = APIEndpointExecutionLog(
            endpoint_id=endpoint_id,
            execution_type="test" if test_mode else "manual",
            started_at=datetime.utcnow(),
            parameters_used=endpoint.default_parameters or {}
        )
        db.add(execution_log)
        db.commit()
        
        # 仮の成功レスポンス
        execution_log.completed_at = datetime.utcnow()
        execution_log.success = True
        execution_log.data_count = 100 if not test_mode else 10
        execution_log.response_time_ms = 1234
        
        db.commit()
        
        # エンドポイントの統計を更新
        endpoint.last_execution_at = execution_log.started_at
        endpoint.last_success_at = execution_log.completed_at
        endpoint.total_executions += 1
        endpoint.successful_executions += 1
        endpoint.last_data_count = execution_log.data_count
        db.commit()
        
        context = {
            "request": request,
            "execution_log": execution_log,
            "test_mode": test_mode
        }
        
        return templates.TemplateResponse("partials/api_endpoints/execution_result.html", context)


