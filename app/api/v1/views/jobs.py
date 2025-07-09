"""ジョブ管理関連のHTMXビューエンドポイント"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """ジョブ管理ページ"""
    return templates.TemplateResponse("pages/jobs.html", {"request": request})


@router.get("/list", response_class=HTMLResponse)
async def jobs_list(request: Request):
    """ジョブリストの部分更新"""
    # TODO: Celeryから実際のジョブ情報を取得
    jobs = []
    return templates.TemplateResponse(
        "partials/job_list.html",
        {"request": request, "jobs": jobs}
    )