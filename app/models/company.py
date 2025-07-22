"""
上場企業関連のデータモデル
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Boolean, Date, DateTime, Integer, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Company(Base):
    """上場企業情報モデル"""
    
    __tablename__ = "companies"
    
    # 基本情報
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False, comment="銘柄コード")
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="会社名（日本語）")
    company_name_english: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="会社名（英語）")
    
    # 分類情報
    sector17_code: Mapped[Optional[str]] = mapped_column(String(10), index=True, comment="17業種区分コード")
    sector33_code: Mapped[Optional[str]] = mapped_column(String(10), index=True, comment="33業種区分コード")
    scale_category: Mapped[Optional[str]] = mapped_column(String(50), comment="規模区分")
    market_code: Mapped[Optional[str]] = mapped_column(String(10), index=True, comment="市場区分コード")
    margin_code: Mapped[Optional[str]] = mapped_column(String(10), comment="信用区分")
    
    # メタデータ
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="アクティブフラグ")
    
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
        Index('ix_companies_market_sector', 'market_code', 'sector17_code'),
        Index('ix_companies_active_market', 'is_active', 'market_code'),
        Index('ix_companies_active_sector17', 'is_active', 'sector17_code'),
        Index('ix_companies_name_search', 'company_name', postgresql_using='gin', postgresql_ops={'company_name': 'gin_trgm_ops'}),
    )
    
    def __repr__(self) -> str:
        return f"<Company(code='{self.code}', name='{self.company_name}')>"


class Sector17Master(Base):
    """17業種区分マスター"""
    
    __tablename__ = "sector17_masters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False, comment="17業種コード")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="業種名")
    name_english: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="業種名（英語）")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="業種説明")
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="表示順序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="アクティブフラグ")
    
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Sector17Master(code='{self.code}', name='{self.name}')>"


class Sector33Master(Base):
    """33業種区分マスター"""
    
    __tablename__ = "sector33_masters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False, comment="33業種コード")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="業種名")
    name_english: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="業種名（英語）")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="業種説明")
    sector17_code: Mapped[str] = mapped_column(String(10), index=True, nullable=False, comment="対応する17業種コード")
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="表示順序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="アクティブフラグ")
    
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # インデックス
    __table_args__ = (
        Index('ix_sector33_sector17_order', 'sector17_code', 'display_order'),
    )
    
    def __repr__(self) -> str:
        return f"<Sector33Master(code='{self.code}', name='{self.name}')>"


class MarketMaster(Base):
    """市場区分マスター"""
    
    __tablename__ = "market_masters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False, comment="市場コード")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="市場名")
    name_english: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="市場名（英語）")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="市場説明")
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="表示順序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="アクティブフラグ")
    
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # インデックス
    __table_args__ = (
        Index('ix_market_active_order', 'is_active', 'display_order'),
    )
    
    def __repr__(self) -> str:
        return f"<MarketMaster(code='{self.code}', name='{self.name}')>"


class CompanySyncHistory(Base):
    """企業データ同期履歴"""
    
    __tablename__ = "company_sync_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sync_date: Mapped[date] = mapped_column(Date, nullable=False, comment="同期対象日")
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="同期タイプ（full/incremental）")
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="同期状態（running/completed/failed）")
    execution_type: Mapped[Optional[str]] = mapped_column(String(20), comment="実行タイプ（manual/scheduled）", default="manual")
    
    # 統計情報
    total_companies: Mapped[Optional[int]] = mapped_column(Integer, comment="総企業数")
    new_companies: Mapped[Optional[int]] = mapped_column(Integer, comment="新規企業数")
    updated_companies: Mapped[Optional[int]] = mapped_column(Integer, comment="更新企業数")
    deleted_companies: Mapped[Optional[int]] = mapped_column(Integer, comment="削除企業数")
    
    # 実行情報
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="開始時刻")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="完了時刻")
    error_message: Mapped[Optional[str]] = mapped_column(Text, comment="エラーメッセージ")
    
    # インデックス
    __table_args__ = (
        Index('ix_sync_history_date_status', 'sync_date', 'status'),
        Index('ix_sync_history_started_at', 'started_at'),
    )
    
    def __repr__(self) -> str:
        return f"<CompanySyncHistory(sync_date='{self.sync_date}', status='{self.status}')>"