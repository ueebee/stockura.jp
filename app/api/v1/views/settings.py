"""設定関連のHTMXビューエンドポイント"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    """設定ページ"""
    return templates.TemplateResponse("pages/settings.html", {"request": request})