from datetime import datetime, time
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, ForeignKey, Text, Float, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class EndpointDataType(str, Enum):
    """エンドポイントのデータ種別"""
    AUTHENTICATION = "authentication"
    LISTED_COMPANIES = "listed_companies"
    DAILY_QUOTES = "daily_quotes"
    FINANCIAL_STATEMENTS = "financial_statements"
    REALTIME_QUOTES = "realtime_quotes"
    HISTORICAL_DATA = "historical_data"
    COMPANY_PROFILE = "company_profile"


class ExecutionMode(str, Enum):
    """実行モード"""
    MANUAL_ONLY = "manual_only"
    SCHEDULED = "scheduled"


class APIEndpoint(Base):
    """APIエンドポイントのモデル"""

    __tablename__ = "api_endpoints"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    endpoint_path: Mapped[str] = mapped_column(String, nullable=False)
    http_method: Mapped[str] = mapped_column(String, default="GET", nullable=False)
    data_type: Mapped[str] = mapped_column(String, nullable=False)  # EndpointDataType enum
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String, default="manual_only", nullable=False)  # ExecutionMode enum
    
    # パラメータ設定
    default_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    required_parameters: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    optional_parameters: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # 実行設定
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    batch_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # レート制限（エンドポイント固有）
    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_per_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # スケジュール設定
    schedule_cron: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    schedule_timezone: Mapped[str] = mapped_column(String, default="Asia/Tokyo", nullable=False)
    next_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # 実行統計
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_data_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # リレーション
    data_source = relationship("DataSource", back_populates="endpoints")
    execution_logs = relationship("APIEndpointExecutionLog", back_populates="endpoint", cascade="all, delete-orphan")
    parameter_presets = relationship("APIEndpointParameterPreset", back_populates="endpoint", cascade="all, delete-orphan")
    schedule = relationship("APIEndpointSchedule", back_populates="endpoint", uselist=False, cascade="all, delete-orphan")


class APIEndpointExecutionLog(Base):
    """APIエンドポイント実行ログのモデル"""
    
    __tablename__ = "api_endpoint_execution_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("api_endpoints.id"), nullable=False)
    execution_type: Mapped[str] = mapped_column(String, nullable=False)  # "manual", "scheduled", "test"
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters_used: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # リレーション
    endpoint = relationship("APIEndpoint", back_populates="execution_logs")


class APIEndpointParameterPreset(Base):
    """APIエンドポイントパラメータプリセットのモデル"""
    
    __tablename__ = "api_endpoint_parameter_presets"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("api_endpoints.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # リレーション
    endpoint = relationship("APIEndpoint", back_populates="parameter_presets")


class APIEndpointSchedule(Base):
    """APIエンドポイントの実行スケジュール"""
    __tablename__ = "api_endpoint_schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("api_endpoints.id"), nullable=False, unique=True)
    
    # スケジュール設定
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)  # daily only for now
    execution_time: Mapped[time] = mapped_column(Time, default=time(5, 0), nullable=False)  # デフォルト 5:00
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Tokyo", nullable=False)
    
    # 実行履歴
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_execution_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # success/failed
    last_sync_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # メタデータ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # リレーション
    endpoint = relationship("APIEndpoint", back_populates="schedule")