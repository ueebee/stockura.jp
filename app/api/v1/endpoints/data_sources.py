from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_source_service import DataSourceService
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    DataSourceListResponse,
    TokenResponse
)
from app.db.session import get_session

router = APIRouter()


@router.post("/", response_model=DataSourceResponse)
async def create_data_source_endpoint(
    data_source: DataSourceCreate,
    db: AsyncSession = Depends(get_session)
):
    """データソースを作成します。"""
    service = DataSourceService(db)
    return await service.create_data_source(data_source)


@router.get("/", response_model=DataSourceListResponse)
async def get_data_sources_endpoint(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する件数"),
    is_enabled: Optional[bool] = Query(None, description="有効/無効でフィルタリング"),
    db: AsyncSession = Depends(get_session)
):
    """データソースの一覧を取得します。"""
    service = DataSourceService(db)
    data_sources, total = await service.list_data_sources(
        skip=skip,
        limit=limit,
        is_enabled=is_enabled
    )
    
    return DataSourceListResponse(
        data_sources=data_sources,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit
    )


@router.get("/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source_endpoint(
    data_source_id: int,
    db: AsyncSession = Depends(get_session)
):
    """データソースを取得します。"""
    service = DataSourceService(db)
    data_source = await service.get_data_source(data_source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_source


@router.put("/{data_source_id}", response_model=DataSourceResponse)
async def update_data_source_endpoint(
    data_source_id: int,
    data_source: DataSourceUpdate,
    db: AsyncSession = Depends(get_session)
):
    """データソースを更新します。"""
    service = DataSourceService(db)
    updated_data_source = await service.update_data_source(data_source_id, data_source)
    if not updated_data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return updated_data_source


@router.delete("/{data_source_id}")
async def delete_data_source_endpoint(
    data_source_id: int,
    db: AsyncSession = Depends(get_session)
):
    """データソースを削除します。"""
    service = DataSourceService(db)
    if not await service.delete_data_source(data_source_id):
        raise HTTPException(status_code=404, detail="Data source not found")
    return {"message": "Data source deleted successfully"}


@router.post("/{data_source_id}/refresh-token", response_model=TokenResponse)
async def get_refresh_token_endpoint(
    data_source_id: int,
    db: AsyncSession = Depends(get_session)
):
    """リフレッシュトークンを取得します。"""
    service = DataSourceService(db)
    token_response = await service.get_refresh_token(data_source_id)
    if not token_response:
        raise HTTPException(status_code=404, detail="Data source not found or token retrieval failed")
    return token_response


@router.post("/{data_source_id}/id-token", response_model=TokenResponse)
async def get_id_token_endpoint(
    data_source_id: int,
    refresh_token: str = Query(..., description="リフレッシュトークン"),
    db: AsyncSession = Depends(get_session)
):
    """IDトークンを取得します。"""
    service = DataSourceService(db)
    token_response = await service.get_id_token(data_source_id, refresh_token)
    if not token_response:
        raise HTTPException(status_code=404, detail="Data source not found or token retrieval failed")
    return token_response 