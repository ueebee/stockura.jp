"""株価分析関連のHTMXビューエンドポイント"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """分析ページ"""
    return templates.TemplateResponse("pages/analysis.html", {"request": request})