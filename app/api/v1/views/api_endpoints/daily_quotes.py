"""
日次株価データ関連APIエンドポイントの処理
"""
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.db.session import get_db
from app.models import APIEndpoint, APIEndpointExecutionLog, EndpointDataType
from app.core.template_filters import to_jst, to_jst_with_seconds
from .base import get_endpoint_schedule_info, get_endpoint_execution_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# カスタムフィルタを登録
templates.env.filters['to_jst'] = to_jst
templates.env.filters['to_jst_with_seconds'] = to_jst_with_seconds


@router.post("/data-sources/{data_source_id}/endpoints/{endpoint_id}/execute-daily-quotes", response_class=HTMLResponse)
async def execute_daily_quotes_endpoint(
    request: Request,
    data_source_id: int,
    endpoint_id: int,
    test_mode: bool = Form(False),
    db: Session = Depends(get_db),
):
    """日次株価データエンドポイントを手動実行（HTMX用）"""
    endpoint = db.query(APIEndpoint).filter(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.data_source_id == data_source_id,
        APIEndpoint.data_type == EndpointDataType.DAILY_QUOTES
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
    
    # 日次株価データの同期タスクを実行（手動同期画面を表示）
    execution_log.completed_at = datetime.utcnow()
    execution_log.success = True
    execution_log.data_count = 0
    execution_log.response_time_ms = 0
    execution_log.parameters_used = {
        "message": "日次株価データの手動同期画面を使用してください"
    }
    
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