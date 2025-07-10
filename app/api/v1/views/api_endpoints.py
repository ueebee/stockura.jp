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
from app.models import DataSource, APIEndpoint, APIEndpointExecutionLog, EndpointDataType, ExecutionMode

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
    
    # エンドポイント一覧を取得
    endpoints = db.query(APIEndpoint).filter(
        APIEndpoint.data_source_id == data_source_id
    ).all()
    
    # エンドポイントがない場合は初期データを作成
    if not endpoints:
        endpoints = _create_initial_endpoints(db, data_source)
    
    context = {
        "request": request,
        "data_source": data_source,
        "endpoints": endpoints,
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
    
    context = {
        "request": request,
        "endpoint": endpoint,
        "recent_logs": recent_logs,
        "data_types": EndpointDataType,
        "execution_modes": ExecutionMode
    }
    
    return templates.TemplateResponse("partials/api_endpoints/endpoint_details.html", context)


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
    
    context = {
        "request": request,
        "endpoint": endpoint
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
    
    # TODO: 実際のAPI呼び出し処理を実装
    # ここでは仮の成功レスポンスを返す
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
                "name": "認証トークン取得",
                "description": "リフレッシュトークンからIDトークンを取得",
                "endpoint_path": "/idtoken",
                "http_method": "POST",
                "data_type": EndpointDataType.AUTHENTICATION,
                "required_parameters": ["refresh_token"],
                "rate_limit_per_minute": 10
            },
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
            },
            {
                "name": "財務諸表",
                "description": "企業の財務諸表データを取得",
                "endpoint_path": "/fins/statements",
                "http_method": "GET",
                "data_type": EndpointDataType.FINANCIAL_STATEMENTS,
                "required_parameters": ["idtoken"],
                "optional_parameters": ["code", "date"],
                "rate_limit_per_minute": 60
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