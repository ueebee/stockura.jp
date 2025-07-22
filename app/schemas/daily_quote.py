"""
株価データ関連のPydanticスキーマ
"""

from datetime import datetime
import datetime as dt
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class DailyQuoteBase(BaseModel):
    """株価データの基本情報"""
    code: str = Field(..., description="銘柄コード")
    trade_date: dt.date = Field(..., description="取引日")
    
    # 調整前価格データ
    open_price: Optional[Decimal] = Field(None, description="始値")
    high_price: Optional[Decimal] = Field(None, description="高値")
    low_price: Optional[Decimal] = Field(None, description="安値")
    close_price: Optional[Decimal] = Field(None, description="終値")
    volume: Optional[int] = Field(None, description="取引高")
    turnover_value: Optional[int] = Field(None, description="取引代金")
    
    # 調整後価格データ
    adjustment_factor: Optional[Decimal] = Field(None, description="調整係数")
    adjustment_open: Optional[Decimal] = Field(None, description="調整後始値")
    adjustment_high: Optional[Decimal] = Field(None, description="調整後高値")
    adjustment_low: Optional[Decimal] = Field(None, description="調整後安値")
    adjustment_close: Optional[Decimal] = Field(None, description="調整後終値")
    adjustment_volume: Optional[int] = Field(None, description="調整後取引高")
    
    # 制限フラグ
    upper_limit_flag: bool = Field(False, description="ストップ高フラグ")
    lower_limit_flag: bool = Field(False, description="ストップ安フラグ")


class DailyQuoteCreate(DailyQuoteBase):
    """株価データ作成スキーマ"""
    pass


class DailyQuoteUpdate(BaseModel):
    """株価データ更新スキーマ"""
    open_price: Optional[Decimal] = Field(None, description="始値")
    high_price: Optional[Decimal] = Field(None, description="高値")
    low_price: Optional[Decimal] = Field(None, description="安値")
    close_price: Optional[Decimal] = Field(None, description="終値")
    volume: Optional[int] = Field(None, description="取引高")
    turnover_value: Optional[int] = Field(None, description="取引代金")
    
    adjustment_factor: Optional[Decimal] = Field(None, description="調整係数")
    adjustment_open: Optional[Decimal] = Field(None, description="調整後始値")
    adjustment_high: Optional[Decimal] = Field(None, description="調整後高値")
    adjustment_low: Optional[Decimal] = Field(None, description="調整後安値")
    adjustment_close: Optional[Decimal] = Field(None, description="調整後終値")
    adjustment_volume: Optional[int] = Field(None, description="調整後取引高")
    
    upper_limit_flag: Optional[bool] = Field(None, description="ストップ高フラグ")
    lower_limit_flag: Optional[bool] = Field(None, description="ストップ安フラグ")


class DailyQuote(DailyQuoteBase):
    """株価データレスポンススキーマ"""
    id: int = Field(..., description="ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    
    # Premium限定データ（将来拡張用）
    morning_open: Optional[Decimal] = Field(None, description="前場始値")
    morning_high: Optional[Decimal] = Field(None, description="前場高値")
    morning_low: Optional[Decimal] = Field(None, description="前場安値")
    morning_close: Optional[Decimal] = Field(None, description="前場終値")
    morning_volume: Optional[int] = Field(None, description="前場取引高")
    morning_turnover_value: Optional[int] = Field(None, description="前場取引代金")
    
    afternoon_open: Optional[Decimal] = Field(None, description="後場始値")
    afternoon_high: Optional[Decimal] = Field(None, description="後場高値")
    afternoon_low: Optional[Decimal] = Field(None, description="後場安値")
    afternoon_close: Optional[Decimal] = Field(None, description="後場終値")
    afternoon_volume: Optional[int] = Field(None, description="後場取引高")
    afternoon_turnover_value: Optional[int] = Field(None, description="後場取引代金")
    
    class Config:
        from_attributes = True


class DailyQuoteList(BaseModel):
    """株価データリストレスポンス"""
    data: List[DailyQuote] = Field(..., description="株価データリスト")
    pagination: "PaginationInfo" = Field(..., description="ページネーション情報")


class PaginationInfo(BaseModel):
    """ページネーション情報"""
    total: int = Field(..., description="総件数")
    limit: int = Field(..., description="1ページあたりの件数")
    offset: int = Field(..., description="オフセット")
    has_next: bool = Field(..., description="次のページが存在するか")


class DailyQuoteSearchRequest(BaseModel):
    """株価データ検索リクエスト"""
    codes: Optional[List[str]] = Field(None, description="銘柄コードリスト")
    date: Optional[dt.date] = Field(None, description="取引日")
    from_date: Optional[dt.date] = Field(None, description="期間開始日")
    to_date: Optional[dt.date] = Field(None, description="期間終了日")
    market_code: Optional[str] = Field(None, description="市場区分コード")
    sector17_code: Optional[str] = Field(None, description="17業種区分コード")
    limit: int = Field(100, ge=1, le=1000, description="取得件数")
    offset: int = Field(0, ge=0, description="オフセット")


class DailyQuotesSyncRequest(BaseModel):
    """株価データ同期リクエスト"""
    data_source_id: int = Field(..., description="J-QuantsデータソースID")
    sync_type: str = Field("incremental", description="同期タイプ（full/incremental/single_stock）")
    target_date: Optional[dt.date] = Field(None, description="対象日（incremental同期時）")
    from_date: Optional[dt.date] = Field(None, description="期間開始日（full同期時）")
    to_date: Optional[dt.date] = Field(None, description="期間終了日（full同期時）")
    codes: Optional[List[str]] = Field(None, description="特定銘柄コードリスト（single_stock同期時）")


class DailyQuotesSyncHistoryBase(BaseModel):
    """株価データ同期履歴の基本情報"""
    sync_date: dt.date = Field(..., description="同期対象日")
    sync_type: str = Field(..., description="同期タイプ（full/incremental/single_stock）")
    status: str = Field(..., description="同期状態（running/completed/failed）")
    execution_type: Optional[str] = Field("manual", description="実行タイプ（manual/scheduled）")
    
    # 統計情報
    target_companies: Optional[int] = Field(None, description="対象企業数")
    total_records: Optional[int] = Field(None, description="総レコード数")
    new_records: Optional[int] = Field(None, description="新規レコード数")
    updated_records: Optional[int] = Field(None, description="更新レコード数")
    skipped_records: Optional[int] = Field(None, description="スキップレコード数")
    
    # 実行情報
    started_at: datetime = Field(..., description="開始時刻")
    completed_at: Optional[datetime] = Field(None, description="完了時刻")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    
    # 処理詳細
    from_date: Optional[dt.date] = Field(None, description="処理開始日")
    to_date: Optional[dt.date] = Field(None, description="処理終了日")
    specific_codes: Optional[List[str]] = Field(None, description="特定銘柄指定")


class DailyQuotesSyncHistory(DailyQuotesSyncHistoryBase):
    """株価データ同期履歴レスポンススキーマ"""
    id: int = Field(..., description="ID")
    
    class Config:
        from_attributes = True


class DailyQuotesSyncHistoryList(BaseModel):
    """株価データ同期履歴リストレスポンス"""
    items: List[DailyQuotesSyncHistory] = Field(..., description="同期履歴リスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="現在のページ")
    per_page: int = Field(..., description="1ページあたりの件数")
    pages: int = Field(..., description="総ページ数")


class DailyQuotesByCodeRequest(BaseModel):
    """特定銘柄の株価データ取得リクエスト"""
    from_date: Optional[dt.date] = Field(None, description="期間開始日")
    to_date: Optional[dt.date] = Field(None, description="期間終了日")
    limit: int = Field(100, ge=1, le=1000, description="取得件数")
    offset: int = Field(0, ge=0, description="オフセット")


class DailyQuotesByDateRequest(BaseModel):
    """特定日の株価データ取得リクエスト"""
    limit: int = Field(1000, ge=1, le=10000, description="取得件数")
    offset: int = Field(0, ge=0, description="オフセット")


class DailyQuoteSyncResponse(BaseModel):
    """株価データ同期実行レスポンス"""
    sync_id: int = Field(..., description="同期履歴ID")
    message: str = Field(..., description="実行結果メッセージ")
    status: str = Field(..., description="同期状態")


class DailyQuoteSyncStatusResponse(BaseModel):
    """株価データ同期ステータスレスポンス"""
    sync_history: DailyQuotesSyncHistory = Field(..., description="同期履歴")
    is_running: bool = Field(..., description="実行中フラグ")
    progress_percentage: Optional[float] = Field(None, description="進捗率（%）")
    estimated_completion: Optional[datetime] = Field(None, description="完了予想時刻")


# 前方参照を解決
DailyQuoteList.model_rebuild()