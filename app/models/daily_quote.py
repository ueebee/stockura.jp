"""
株価データ関連のデータモデル
"""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Boolean, Date, DateTime, Integer, Index, Text, ForeignKey, DECIMAL, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class DailyQuote(Base):
    """日次株価データモデル"""
    
    __tablename__ = "daily_quotes"
    
    # 基本情報
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(10), ForeignKey("companies.code"), nullable=False, comment="銘柄コード")
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, comment="取引日")
    
    # 調整前価格データ
    open_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="始値")
    high_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="高値")
    low_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="安値")
    close_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="終値")
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, comment="取引高")
    turnover_value: Mapped[Optional[int]] = mapped_column(BigInteger, comment="取引代金")
    
    # 調整後価格データ
    adjustment_factor: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6), default=1.0, comment="調整係数")
    adjustment_open: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="調整後始値")
    adjustment_high: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="調整後高値")
    adjustment_low: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="調整後安値")
    adjustment_close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="調整後終値")
    adjustment_volume: Mapped[Optional[int]] = mapped_column(BigInteger, comment="調整後取引高")
    
    # 制限フラグ
    upper_limit_flag: Mapped[bool] = mapped_column(Boolean, default=False, comment="ストップ高フラグ")
    lower_limit_flag: Mapped[bool] = mapped_column(Boolean, default=False, comment="ストップ安フラグ")
    
    # Premium限定（将来拡張用）
    morning_open: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="前場始値")
    morning_high: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="前場高値")
    morning_low: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="前場安値")
    morning_close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="前場終値")
    morning_volume: Mapped[Optional[int]] = mapped_column(BigInteger, comment="前場取引高")
    morning_turnover_value: Mapped[Optional[int]] = mapped_column(BigInteger, comment="前場取引代金")
    
    afternoon_open: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="後場始値")
    afternoon_high: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="後場高値")
    afternoon_low: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="後場安値")
    afternoon_close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="後場終値")
    afternoon_volume: Mapped[Optional[int]] = mapped_column(BigInteger, comment="後場取引高")
    afternoon_turnover_value: Mapped[Optional[int]] = mapped_column(BigInteger, comment="後場取引代金")
    
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # 複合インデックス
    __table_args__ = (
        Index('ix_daily_quotes_code_date', 'code', 'trade_date', unique=True),
        Index('ix_daily_quotes_date', 'trade_date'),
        Index('ix_daily_quotes_code', 'code'),
        Index('ix_daily_quotes_volume', 'volume'),
        Index('ix_daily_quotes_code_date_desc', 'code', 'trade_date', postgresql_using='btree'),
    )
    
    def __repr__(self) -> str:
        return f"<DailyQuote(code='{self.code}', trade_date='{self.trade_date}', close_price='{self.close_price}')>"


class DailyQuotesSyncHistory(Base):
    """株価データ同期履歴"""
    
    __tablename__ = "daily_quotes_sync_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sync_date: Mapped[date] = mapped_column(Date, nullable=False, comment="同期対象日")
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="同期タイプ（full/incremental/single_stock)")
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="同期状態（running/completed/failed）")
    execution_type: Mapped[Optional[str]] = mapped_column(String(20), comment="実行タイプ（manual/scheduled）", default="manual")
    
    # 統計情報
    target_companies: Mapped[Optional[int]] = mapped_column(Integer, comment="対象企業数")
    total_records: Mapped[Optional[int]] = mapped_column(Integer, comment="総レコード数")
    new_records: Mapped[Optional[int]] = mapped_column(Integer, comment="新規レコード数")
    updated_records: Mapped[Optional[int]] = mapped_column(Integer, comment="更新レコード数")
    skipped_records: Mapped[Optional[int]] = mapped_column(Integer, comment="スキップレコード数")
    
    # 実行情報
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="開始時刻")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="完了時刻")
    error_message: Mapped[Optional[str]] = mapped_column(Text, comment="エラーメッセージ")
    
    # 処理詳細
    from_date: Mapped[Optional[date]] = mapped_column(Date, comment="処理開始日")
    to_date: Mapped[Optional[date]] = mapped_column(Date, comment="処理終了日")
    specific_codes: Mapped[Optional[str]] = mapped_column(Text, comment="特定銘柄指定（JSON配列）")
    
    # インデックス
    __table_args__ = (
        Index('ix_daily_quotes_sync_date_status', 'sync_date', 'status'),
        Index('ix_daily_quotes_sync_started_at', 'started_at'),
    )
    
    def __repr__(self) -> str:
        return f"<DailyQuotesSyncHistory(sync_date='{self.sync_date}', status='{self.status}')>"