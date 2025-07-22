"""
企業関連のPydanticスキーマ
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    """企業の基本情報"""
    code: str = Field(..., description="銘柄コード")
    company_name: str = Field(..., description="会社名（日本語）")
    company_name_english: Optional[str] = Field(None, description="会社名（英語）")
    sector17_code: Optional[str] = Field(None, description="17業種区分コード")
    sector33_code: Optional[str] = Field(None, description="33業種区分コード")
    scale_category: Optional[str] = Field(None, description="規模区分")
    market_code: Optional[str] = Field(None, description="市場区分コード")
    margin_code: Optional[str] = Field(None, description="信用区分")
    is_active: bool = Field(True, description="アクティブフラグ")


class CompanyCreate(CompanyBase):
    """企業作成スキーマ"""
    pass


class CompanyUpdate(BaseModel):
    """企業更新スキーマ"""
    company_name: Optional[str] = Field(None, description="会社名（日本語）")
    company_name_english: Optional[str] = Field(None, description="会社名（英語）")
    sector17_code: Optional[str] = Field(None, description="17業種区分コード")
    sector33_code: Optional[str] = Field(None, description="33業種区分コード")
    scale_category: Optional[str] = Field(None, description="規模区分")
    market_code: Optional[str] = Field(None, description="市場区分コード")
    margin_code: Optional[str] = Field(None, description="信用区分")
    is_active: Optional[bool] = Field(None, description="アクティブフラグ")


class Company(CompanyBase):
    """企業レスポンススキーマ"""
    id: int = Field(..., description="ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    
    class Config:
        from_attributes = True


class CompanyList(BaseModel):
    """企業リストレスポンス"""
    items: List[Company] = Field(..., description="企業リスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="現在のページ")
    per_page: int = Field(..., description="1ページあたりの件数")
    pages: int = Field(..., description="総ページ数")


class CompanySyncRequest(BaseModel):
    """企業データ同期リクエスト"""
    data_source_id: int = Field(..., description="J-QuantsデータソースID")
    sync_type: str = Field("full", description="同期タイプ（full/incremental）")


class CompanySyncHistoryBase(BaseModel):
    """同期履歴の基本情報"""
    sync_date: date = Field(..., description="同期対象日")
    sync_type: str = Field(..., description="同期タイプ（full/incremental）")
    status: str = Field(..., description="同期状態（running/completed/failed）")
    execution_type: Optional[str] = Field("manual", description="実行タイプ（manual/scheduled）")
    total_companies: Optional[int] = Field(None, description="総企業数")
    new_companies: Optional[int] = Field(None, description="新規企業数")
    updated_companies: Optional[int] = Field(None, description="更新企業数")
    deleted_companies: Optional[int] = Field(None, description="削除企業数")
    started_at: datetime = Field(..., description="開始時刻")
    completed_at: Optional[datetime] = Field(None, description="完了時刻")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")


class CompanySyncHistory(CompanySyncHistoryBase):
    """同期履歴レスポンススキーマ"""
    id: int = Field(..., description="ID")
    
    class Config:
        from_attributes = True


class CompanySyncHistoryList(BaseModel):
    """同期履歴リストレスポンス"""
    items: List[CompanySyncHistory] = Field(..., description="同期履歴リスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="現在のページ")
    per_page: int = Field(..., description="1ページあたりの件数")
    pages: int = Field(..., description="総ページ数")


class SectorMasterBase(BaseModel):
    """業種マスターの基本情報"""
    code: str = Field(..., description="業種コード")
    name: str = Field(..., description="業種名")
    name_english: Optional[str] = Field(None, description="業種名（英語）")
    description: Optional[str] = Field(None, description="業種説明")
    display_order: int = Field(0, description="表示順序")
    is_active: bool = Field(True, description="アクティブフラグ")


class Sector17Master(SectorMasterBase):
    """17業種区分マスターレスポンス"""
    id: int = Field(..., description="ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    
    class Config:
        from_attributes = True


class Sector33Master(SectorMasterBase):
    """33業種区分マスターレスポンス"""
    id: int = Field(..., description="ID")
    sector17_code: str = Field(..., description="対応する17業種コード")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    
    class Config:
        from_attributes = True


class MarketMasterBase(BaseModel):
    """市場区分マスターの基本情報"""
    code: str = Field(..., description="市場コード")
    name: str = Field(..., description="市場名")
    name_english: Optional[str] = Field(None, description="市場名（英語）")
    description: Optional[str] = Field(None, description="市場説明")
    display_order: int = Field(0, description="表示順序")
    is_active: bool = Field(True, description="アクティブフラグ")


class MarketMaster(MarketMasterBase):
    """市場区分マスターレスポンス"""
    id: int = Field(..., description="ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    
    class Config:
        from_attributes = True


class CompanySearchRequest(BaseModel):
    """企業検索リクエスト"""
    code: Optional[str] = Field(None, description="銘柄コード（部分一致）")
    company_name: Optional[str] = Field(None, description="会社名（部分一致）")
    sector17_code: Optional[str] = Field(None, description="17業種区分コード")
    sector33_code: Optional[str] = Field(None, description="33業種区分コード")
    market_code: Optional[str] = Field(None, description="市場区分コード")
    is_active: Optional[bool] = Field(None, description="アクティブフラグ")
    page: int = Field(1, ge=1, description="ページ番号")
    per_page: int = Field(50, ge=1, le=1000, description="1ページあたりの件数")


class CompanySyncScheduleRequest(BaseModel):
    """企業同期スケジュールリクエスト"""
    hour: int = Field(..., ge=0, le=23, description="実行時（時）")
    minute: int = Field(..., ge=0, le=59, description="実行時（分）")