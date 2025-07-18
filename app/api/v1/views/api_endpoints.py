"""
APIエンドポイント管理のビュー
"""
from typing import Dict, Any, Optional
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

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# カスタムフィルタを登録
templates.env.filters['to_jst'] = to_jst
templates.env.filters['to_jst_with_seconds'] = to_jst_with_seconds


def _get_endpoint_schedule_info(db: Session, endpoint: APIEndpoint) -> Optional[Dict[str, Any]]:
    """
    エンドポイントのスケジュール情報を取得する共通関数
    
    Returns:
        Dict with keys:
            - is_enabled: bool - スケジュールが有効かどうか
            - execution_time: time or None - 実行時刻
            - schedule_type: str or None - スケジュールタイプ（daily, weekly, monthly）
    """
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        # 上場企業一覧用のスケジュール
        schedule = db.query(APIEndpointSchedule).filter(
            APIEndpointSchedule.endpoint_id == endpoint.id
        ).first()
        if schedule:
            return {
                "is_enabled": schedule.is_enabled,
                "execution_time": schedule.execution_time,
                "schedule_type": "daily"  # 上場企業一覧は日次のみ
            }
    elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        # 日次株価データ用のスケジュール
        # 有効なスケジュールが1つでもあるかチェック
        active_schedule = db.query(DailyQuoteSchedule).filter(
            DailyQuoteSchedule.data_source_id == endpoint.data_source_id,
            DailyQuoteSchedule.is_enabled == True
        ).first()
        if active_schedule:
            return {
                "is_enabled": True,
                "execution_time": active_schedule.execution_time,
                "schedule_type": active_schedule.schedule_type
            }
    
    return None


def _get_endpoint_execution_stats(db: Session, endpoint: APIEndpoint) -> Dict[str, Any]:
    """
    エンドポイントの実行統計情報を取得する共通関数
    
    Returns:
        Dict with keys:
            - last_execution_at: datetime or None - 最終実行日時
            - last_success_at: datetime or None - 最終成功日時
            - last_error_at: datetime or None - 最終エラー日時
            - total_executions: int - 総実行回数
            - successful_executions: int - 成功した実行回数
            - last_data_count: int or None - 最後のデータ件数
    """
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        # APIEndpointExecutionLogから統計を取得（既存のエンドポイントの値を使用）
        return {
            "last_execution_at": endpoint.last_execution_at,
            "last_success_at": endpoint.last_success_at,
            "last_error_at": endpoint.last_error_at,
            "total_executions": endpoint.total_executions,
            "successful_executions": endpoint.successful_executions,
            "last_data_count": endpoint.last_data_count
        }
    elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        # DailyQuotesSyncHistoryから統計を計算
        # 最新の実行履歴を取得
        latest_history = db.query(DailyQuotesSyncHistory).order_by(
            DailyQuotesSyncHistory.started_at.desc()
        ).first()
        
        # 最後の成功した実行
        latest_success = db.query(DailyQuotesSyncHistory).filter(
            DailyQuotesSyncHistory.status == "completed"
        ).order_by(
            DailyQuotesSyncHistory.started_at.desc()
        ).first()
        
        # 最後のエラー実行
        latest_error = db.query(DailyQuotesSyncHistory).filter(
            DailyQuotesSyncHistory.status == "failed"
        ).order_by(
            DailyQuotesSyncHistory.started_at.desc()
        ).first()
        
        # 統計情報を計算
        total_executions = db.query(DailyQuotesSyncHistory).count()
        successful_executions = db.query(DailyQuotesSyncHistory).filter(
            DailyQuotesSyncHistory.status == "completed"
        ).count()
        
        last_data_count = None
        if latest_history and latest_history.total_records:
            last_data_count = latest_history.total_records
        
        return {
            "last_execution_at": latest_history.started_at if latest_history else None,
            "last_success_at": latest_success.started_at if latest_success else None,
            "last_error_at": latest_error.started_at if latest_error else None,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "last_data_count": last_data_count
        }
    else:
        # その他のエンドポイントタイプ（デフォルト値）
        return {
            "last_execution_at": endpoint.last_execution_at,
            "last_success_at": endpoint.last_success_at,
            "last_error_at": endpoint.last_error_at,
            "total_executions": endpoint.total_executions,
            "successful_executions": endpoint.successful_executions,
            "last_data_count": endpoint.last_data_count
        }


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
        endpoints = _create_initial_endpoints(db, data_source)
    
    # 各エンドポイントのスケジュール情報と実行統計を取得
    endpoint_schedules = {}
    endpoint_stats = {}
    for endpoint in endpoints:
        schedule_info = _get_endpoint_schedule_info(db, endpoint)
        endpoint_schedules[endpoint.id] = schedule_info
        
        # 実行統計情報を取得
        stats = _get_endpoint_execution_stats(db, endpoint)
        endpoint_stats[endpoint.id] = stats
    
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
    
    # 最新の実行ログを取得
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
    schedule_info = _get_endpoint_schedule_info(db, endpoint)
    stats = _get_endpoint_execution_stats(db, endpoint)
    
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
    """エンドポイントを手動実行（HTMX用）"""
    endpoint = db.query(APIEndpoint).filter(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.data_source_id == data_source_id
    ).first()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    if not endpoint.is_enabled:
        raise HTTPException(status_code=400, detail="Endpoint is disabled")
    
    # 実行ログを作成
    execution_log = APIEndpointExecutionLog(
        endpoint_id=endpoint_id,
        execution_type="test" if test_mode else "manual",
        started_at=datetime.utcnow(),
        parameters_used=endpoint.default_parameters or {}
    )
    db.add(execution_log)
    db.commit()
    
    # エンドポイントの種類に応じて適切なタスクを実行
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        # 上場企業一覧の同期タスクを実行
        from app.tasks.company_tasks import sync_listed_companies
        task = sync_listed_companies.delay()
        
        # タスク実行結果を仮で設定（実際には非同期で更新される）
        execution_log.completed_at = datetime.utcnow()
        execution_log.success = True
        execution_log.data_count = 0  # 非同期実行のため、実際の件数は後で更新
        execution_log.response_time_ms = 0
        
        # 実行メッセージをログに記録
        execution_log.parameters_used = {
            "task_id": task.id,
            "message": "同期タスクをバックグラウンドで実行中"
        }
    elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        # 日時株価データの同期タスクを実行（手動同期画面を表示）
        execution_log.completed_at = datetime.utcnow()
        execution_log.success = True
        execution_log.data_count = 0
        execution_log.response_time_ms = 0
        execution_log.parameters_used = {
            "message": "日時株価データの手動同期画面を使用してください"
        }
    else:
        # その他のエンドポイントは仮の成功レスポンス
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


def _create_initial_endpoints(db: Session, data_source: DataSource) -> list[APIEndpoint]:
    """データソース用の初期エンドポイントを作成"""
    endpoints = []
    
    if data_source.provider_type == "jquants":
        # J-Quants用エンドポイント
        jquants_endpoints = [
            {
                "name": "上場企業一覧",
                "description": "全上場企業の基本情報を取得",
                "endpoint_path": "/listed/info",
                "http_method": "GET",
                "data_type": EndpointDataType.LISTED_COMPANIES,
                "required_parameters": ["idtoken"],
                "optional_parameters": ["date", "includeDetails"],
                "default_parameters": {"includeDetails": "true"},
                "rate_limit_per_minute": 60
            },
            {
                "name": "日次株価データ",
                "description": "指定期間の日次株価データを取得",
                "endpoint_path": "/prices/daily_quotes",
                "http_method": "GET",
                "data_type": EndpointDataType.DAILY_QUOTES,
                "required_parameters": ["idtoken"],
                "optional_parameters": ["code", "from", "to", "date"],
                "default_parameters": {"code": "*"},
                "batch_size": 1000,
                "rate_limit_per_minute": 300
            }
        ]
        
        for ep_data in jquants_endpoints:
            endpoint = APIEndpoint(
                data_source_id=data_source.id,
                **ep_data
            )
            db.add(endpoint)
            endpoints.append(endpoint)
    
    elif data_source.provider_type == "yfinance":
        # Yahoo Finance用エンドポイント
        yfinance_endpoints = [
            {
                "name": "リアルタイム株価",
                "description": "現在の株価情報を取得",
                "endpoint_path": "/quote",
                "http_method": "GET",
                "data_type": EndpointDataType.REALTIME_QUOTES,
                "required_parameters": ["symbol"],
                "rate_limit_per_minute": 2000
            },
            {
                "name": "ヒストリカルデータ",
                "description": "過去の株価データを取得",
                "endpoint_path": "/history",
                "http_method": "GET",
                "data_type": EndpointDataType.HISTORICAL_DATA,
                "required_parameters": ["symbol"],
                "optional_parameters": ["period", "interval", "start", "end"],
                "default_parameters": {"period": "1mo", "interval": "1d"},
                "rate_limit_per_minute": 1000
            },
            {
                "name": "企業プロファイル",
                "description": "企業の基本情報を取得",
                "endpoint_path": "/info",
                "http_method": "GET",
                "data_type": EndpointDataType.COMPANY_PROFILE,
                "required_parameters": ["symbol"],
                "rate_limit_per_minute": 500
            }
        ]
        
        for ep_data in yfinance_endpoints:
            endpoint = APIEndpoint(
                data_source_id=data_source.id,
                **ep_data
            )
            db.add(endpoint)
            endpoints.append(endpoint)
    
    db.commit()
    
    # リフレッシュして返す
    for endpoint in endpoints:
        db.refresh(endpoint)
    
    return endpoints