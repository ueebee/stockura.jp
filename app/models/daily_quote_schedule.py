"""
日次株価データ定期実行スケジュールモデル
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Integer, Index, Text, Time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class DailyQuoteSchedule(Base):
    """日次株価データ定期実行スケジュール"""
    
    __tablename__ = "daily_quote_schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="スケジュール名")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="説明")
    
    # 同期設定
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="同期タイプ（full/incremental）")
    relative_preset: Mapped[Optional[str]] = mapped_column(String(30), comment="相対日付プリセット（last7days等）")
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="データソースID")
    
    # スケジュール設定
    schedule_type: Mapped[str] = mapped_column(String(20), default="daily", comment="スケジュールタイプ（daily/weekly/monthly）")
    execution_time: Mapped[datetime.time] = mapped_column(Time, nullable=False, comment="実行時刻（JST）")
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, comment="実行曜日（0=月曜日、週次の場合）")
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, comment="実行日（月次の場合）")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Tokyo", comment="タイムゾーン")
    
    # 状態
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="有効フラグ")
    
    # 実行履歴
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="最終実行日時")
    last_execution_status: Mapped[Optional[str]] = mapped_column(String(20), comment="最終実行ステータス")
    last_execution_message: Mapped[Optional[str]] = mapped_column(Text, comment="最終実行メッセージ")
    last_sync_count: Mapped[Optional[int]] = mapped_column(Integer, comment="最終同期件数")
    
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # インデックス
    __table_args__ = (
        Index('ix_daily_quote_schedules_is_enabled', 'is_enabled'),
        Index('ix_daily_quote_schedules_schedule_type', 'schedule_type'),
    )
    
    def __repr__(self) -> str:
        return f"<DailyQuoteSchedule(name='{self.name}', sync_type='{self.sync_type}', is_enabled={self.is_enabled})>"