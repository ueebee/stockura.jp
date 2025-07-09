"""データソース管理関連のHTMXビューエンドポイント"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.data_source_service import DataSourceService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def data_sources_page(request: Request):
    """データソース管理ページ"""
    return templates.TemplateResponse("pages/data_sources.html", {"request": request})


@router.get("/table", response_class=HTMLResponse)
async def data_sources_table(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """データソーステーブルの部分更新"""
    service = DataSourceService(db)
    data_sources = await service.get_all()
    
    return templates.TemplateResponse(
        "partials/data_source_table.html",
        {"request": request, "data_sources": data_sources}
    )


@router.get("/{data_source_id}/card", response_class=HTMLResponse)
async def data_source_card(
    request: Request,
    data_source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """データソースカードの部分更新"""
    service = DataSourceService(db)
    data_source = await service.get(data_source_id)
    
    return templates.TemplateResponse(
        "partials/data_source_card.html",
        {"request": request, "data_source": data_source}
    )