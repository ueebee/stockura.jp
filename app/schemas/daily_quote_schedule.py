"""
日次株価データ定期実行スケジュールのスキーマ
"""
from datetime import datetime, time
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DailyQuoteScheduleBase(BaseModel):
    """スケジュール基本スキーマ"""
    name: str = Field(..., max_length=100, description="スケジュール名")
    description: Optional[str] = Field(None, description="説明")
    sync_type: str = Field(..., pattern="^(full|incremental)$", description="同期タイプ")
    relative_preset: Optional[str] = Field(None, description="相対日付プリセット")
    data_source_id: int = Field(..., description="データソースID")
    schedule_type: str = Field("daily", pattern="^(daily|weekly|monthly)$", description="スケジュールタイプ")
    execution_time: time = Field(..., description="実行時刻（JST）")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="実行曜日（0=月曜日）")
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="実行日")
    is_enabled: bool = Field(True, description="有効フラグ")


class DailyQuoteScheduleCreate(DailyQuoteScheduleBase):
    """スケジュール作成スキーマ"""
    pass


class DailyQuoteScheduleUpdate(BaseModel):
    """スケジュール更新スキーマ"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    sync_type: Optional[str] = Field(None, pattern="^(full|incremental)$")
    relative_preset: Optional[str] = None
    data_source_id: Optional[int] = None
    schedule_type: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    execution_time: Optional[time] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    is_enabled: Optional[bool] = None


class DailyQuoteSchedule(DailyQuoteScheduleBase):
    """スケジュールスキーマ"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_execution_at: Optional[datetime] = None
    last_execution_status: Optional[str] = None
    last_execution_message: Optional[str] = None
    last_sync_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class DailyQuoteScheduleDetail(DailyQuoteSchedule):
    """スケジュール詳細スキーマ（次回実行情報含む）"""
    next_run: Optional[datetime] = Field(None, description="次回実行予定時刻")
    next_run_date_range: Optional[Dict[str, str]] = Field(None, description="次回実行時の日付範囲")
    
    class Config:
        from_attributes = True