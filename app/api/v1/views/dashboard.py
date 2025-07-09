"""ダッシュボード関連のHTMXビューエンドポイント"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """ダッシュボードページ"""
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})


@router.get("/api/v1/dashboard/activities", response_class=HTMLResponse)
async def dashboard_activities(request: Request):
    """ダッシュボードのアクティビティ部分更新"""
    # サンプルデータ（実際はサービスから取得）
    activities = [
        {"time": "10分前", "action": "J-Quantsから企業データを同期", "status": "success"},
        {"time": "30分前", "action": "日次株価データの取得", "status": "success"},
        {"time": "1時間前", "action": "Yahoo Financeからのデータ取得", "status": "error"},
    ]
    return templates.TemplateResponse(
        "partials/dashboard/activity_list.html", 
        {"request": request, "activities": activities}
    )


@router.get("/stats", response_class=HTMLResponse)
async def dashboard_stats(request: Request):
    """ダッシュボードの統計情報部分更新"""
    # 実際はサービスから取得
    stats = {
        "data_sources": {"count": 2, "active": 2},
        "syncs_today": 15,
        "errors": 3,
        "total_records": "1.2M"
    }
    return templates.TemplateResponse(
        "partials/dashboard_stats.html",
        {"request": request, "stats": stats}
    )