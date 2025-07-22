"""
企業関連APIエンドポイントの処理
"""
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.db.session import get_db
from app.models import APIEndpoint, APIEndpointExecutionLog, APIEndpointSchedule, EndpointDataType
from app.core.template_filters import to_jst, to_jst_with_seconds
from .base import get_endpoint_schedule_info, get_endpoint_execution_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# カスタムフィルタを登録
templates.env.filters['to_jst'] = to_jst
templates.env.filters['to_jst_with_seconds'] = to_jst_with_seconds


@router.post("/data-sources/{data_source_id}/endpoints/{endpoint_id}/execute-companies", response_class=HTMLResponse)
async def execute_companies_endpoint(
    request: Request,
    data_source_id: int,
    endpoint_id: int,
    test_mode: bool = Form(False),
    db: Session = Depends(get_db),
):
    """上場企業一覧エンドポイントを手動実行（HTMX用）"""
    endpoint = db.query(APIEndpoint).filter(
        APIEndpoint.id == endpoint_id,
        APIEndpoint.data_source_id == data_source_id,
        APIEndpoint.data_type == EndpointDataType.LISTED_COMPANIES
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