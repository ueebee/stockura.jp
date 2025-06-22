from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class DataSourceBase(BaseModel):
    """データソースの基本スキーマ"""
    name: str = Field(..., description="データソース名")
    description: Optional[str] = Field(None, description="説明")
    provider_type: str = Field(..., description="プロバイダータイプ（例: jquants, yfinance）")
    is_enabled: bool = Field(True, description="有効/無効フラグ")
    base_url: str = Field(..., description="APIのベースURL")
    api_version: Optional[str] = Field(None, description="APIバージョン")
    rate_limit_per_minute: int = Field(60, description="分間レート制限")
    rate_limit_per_hour: int = Field(3600, description="時間レート制限")
    rate_limit_per_day: int = Field(86400, description="日間レート制限")


class DataSourceCreate(DataSourceBase):
    """データソース作成用スキーマ"""
    credentials: Optional[Dict[str, Any]] = Field(None, description="認証情報（暗号化して保存されます）")


class DataSourceUpdate(BaseModel):
    """データソース更新用スキーマ"""
    name: Optional[str] = Field(None, description="データソース名")
    description: Optional[str] = Field(None, description="説明")
    provider_type: Optional[str] = Field(None, description="プロバイダータイプ")
    is_enabled: Optional[bool] = Field(None, description="有効/無効フラグ")
    base_url: Optional[str] = Field(None, description="APIのベースURL")
    api_version: Optional[str] = Field(None, description="APIバージョン")
    rate_limit_per_minute: Optional[int] = Field(None, description="分間レート制限")
    rate_limit_per_hour: Optional[int] = Field(None, description="時間レート制限")
    rate_limit_per_day: Optional[int] = Field(None, description="日間レート制限")
    credentials: Optional[Dict[str, Any]] = Field(None, description="認証情報（暗号化して保存されます）")


class DataSourceResponse(DataSourceBase):
    """データソースレスポンス用スキーマ"""
    id: int = Field(..., description="データソースID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """トークン取得レスポンス用スキーマ"""
    token: str = Field(..., description="取得したトークン")
    expired_at: Optional[datetime] = Field(None, description="トークンの有効期限")
    token_type: str = Field(..., description="トークンの種類（refresh_token, id_token）")


class DataSourceListResponse(BaseModel):
    """データソース一覧レスポンス用スキーマ"""
    data_sources: list[DataSourceResponse] = Field(..., description="データソース一覧")
    total: int = Field(..., description="総件数")
    page: int = Field(1, description="現在のページ")
    per_page: int = Field(10, description="1ページあたりの件数") 