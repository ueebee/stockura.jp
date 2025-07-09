"""データソース管理関連のHTMXビューエンドポイント"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.data_source_service import DataSourceService
from app.schemas.data_source import DataSourceUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def data_sources_page(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """データソース管理ページ"""
    service = DataSourceService(db)
    data_sources = await service.list_data_sources()
    
    return templates.TemplateResponse(
        "pages/data_sources.html", 
        {"request": request, "data_sources": data_sources.items}
    )


@router.get("/table", response_class=HTMLResponse)
async def data_sources_table(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """データソーステーブルの部分更新"""
    service = DataSourceService(db)
    data_sources = await service.list_data_sources()
    
    return templates.TemplateResponse(
        "partials/data_sources/data_source_table.html",
        {"request": request, "data_sources": data_sources.items}
    )


@router.get("/{data_source_id}/card", response_class=HTMLResponse)
async def data_source_card(
    request: Request,
    data_source_id: int,
    db: AsyncSession = Depends(get_session)
):
    """データソースカードの部分更新"""
    service = DataSourceService(db)
    data_source = await service.get_data_source(data_source_id)
    
    return templates.TemplateResponse(
        "partials/data_sources/data_source_card.html",
        {"request": request, "data_source": data_source}
    )


@router.post("/{data_source_id}/toggle", response_class=HTMLResponse)
async def toggle_data_source(
    request: Request,
    data_source_id: int,
    db: AsyncSession = Depends(get_session)
):
    """データソースの有効/無効を切り替え"""
    service = DataSourceService(db)
    data_source = await service.get_data_source(data_source_id)
    
    # 有効/無効を切り替え
    update_data = DataSourceUpdate(is_enabled=not data_source.is_enabled)
    updated_source = await service.update_data_source(data_source_id, update_data)
    
    return templates.TemplateResponse(
        "partials/data_sources/data_source_row.html",
        {"request": request, "data_source": updated_source}
    )