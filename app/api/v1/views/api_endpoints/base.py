"""
APIエンドポイント管理の基底クラスと共通機能
"""
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models import DataSource, APIEndpoint, APIEndpointExecutionLog, APIEndpointSchedule, EndpointDataType, ExecutionMode
from app.models.daily_quote_schedule import DailyQuoteSchedule
from app.models.daily_quote import DailyQuotesSyncHistory


def get_endpoint_schedule_info(db: Session, endpoint: APIEndpoint) -> Optional[Dict[str, Any]]:
    """
    エンドポイントのスケジュール情報を取得する共通関数
    
    Returns:
        Dict with keys:
            - is_enabled: bool - スケジュールが有効かどうか
            - execution_time: time or None - 実行時刻
            - schedule_type: str or None - スケジュールタイプ（daily, weekly, monthly）
    """
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        # 上場企業一覧用のスケジュール
        schedule = db.query(APIEndpointSchedule).filter(
            APIEndpointSchedule.endpoint_id == endpoint.id
        ).first()
        if schedule:
            return {
                "is_enabled": schedule.is_enabled,
                "execution_time": schedule.execution_time,
                "schedule_type": "daily"  # 上場企業一覧は日次のみ
            }
    elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        # 日次株価データ用のスケジュール
        # 有効なスケジュールが1つでもあるかチェック
        active_schedule = db.query(DailyQuoteSchedule).filter(
            DailyQuoteSchedule.data_source_id == endpoint.data_source_id,
            DailyQuoteSchedule.is_enabled == True
        ).first()
        if active_schedule:
            return {
                "is_enabled": True,
                "execution_time": active_schedule.execution_time,
                "schedule_type": active_schedule.schedule_type
            }
    
    return None


def get_endpoint_execution_stats(db: Session, endpoint: APIEndpoint) -> Dict[str, Any]:
    """
    エンドポイントの実行統計情報を取得する共通関数
    
    Returns:
        Dict with keys:
            - last_execution_at: datetime or None - 最終実行日時
            - last_success_at: datetime or None - 最終成功日時
            - last_error_at: datetime or None - 最終エラー日時
            - total_executions: int - 総実行回数
            - successful_executions: int - 成功した実行回数
            - last_data_count: int or None - 最後のデータ件数
    """
    if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
        # APIEndpointExecutionLogから統計を取得（既存のエンドポイントの値を使用）
        return {
            "last_execution_at": endpoint.last_execution_at,
            "last_success_at": endpoint.last_success_at,
            "last_error_at": endpoint.last_error_at,
            "total_executions": endpoint.total_executions,
            "successful_executions": endpoint.successful_executions,
            "last_data_count": endpoint.last_data_count
        }
    elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
        # DailyQuotesSyncHistoryから統計を最適化されたクエリで計算
        stats = db.query(
            func.max(DailyQuotesSyncHistory.started_at).label('last_execution'),
            func.max(case(
                (DailyQuotesSyncHistory.status == 'completed', DailyQuotesSyncHistory.started_at),
                else_=None
            )).label('last_success'),
            func.max(case(
                (DailyQuotesSyncHistory.status == 'failed', DailyQuotesSyncHistory.started_at),
                else_=None
            )).label('last_error'),
            func.count(DailyQuotesSyncHistory.id).label('total_executions'),
            func.sum(case(
                (DailyQuotesSyncHistory.status == 'completed', 1),
                else_=0
            )).label('successful_executions')
        ).first()
        
        # 最新の実行履歴から最後のデータ件数を取得
        latest_history = db.query(DailyQuotesSyncHistory).order_by(
            DailyQuotesSyncHistory.started_at.desc()
        ).first()
        
        last_data_count = None
        if latest_history and latest_history.total_records:
            last_data_count = latest_history.total_records
        
        return {
            "last_execution_at": stats.last_execution,
            "last_success_at": stats.last_success,
            "last_error_at": stats.last_error,
            "total_executions": stats.total_executions or 0,
            "successful_executions": stats.successful_executions or 0,
            "last_data_count": last_data_count
        }
    else:
        # その他のエンドポイントタイプ（デフォルト値）
        return {
            "last_execution_at": endpoint.last_execution_at,
            "last_success_at": endpoint.last_success_at,
            "last_error_at": endpoint.last_error_at,
            "total_executions": endpoint.total_executions,
            "successful_executions": endpoint.successful_executions,
            "last_data_count": endpoint.last_data_count
        }


def create_initial_endpoints(db: Session, data_source: DataSource) -> list[APIEndpoint]:
    """データソース用の初期エンドポイントを作成"""
    endpoints = []
    
    if data_source.provider_type == "jquants":
        # J-Quants用エンドポイント
        jquants_endpoints = [
            {
                "name": "上場企業一覧",
                "description": "全上場企業の基本情報を取得",
                "endpoint_path": "/listed/info",
                "http_method": "GET",
                "data_type": EndpointDataType.LISTED_COMPANIES,
                "required_parameters": ["idtoken"],
                "optional_parameters": ["date", "includeDetails"],
                "default_parameters": {"includeDetails": "true"},
                "rate_limit_per_minute": 60
            },
            {
                "name": "日次株価データ",
                "description": "指定期間の日次株価データを取得",
                "endpoint_path": "/prices/daily_quotes",
                "http_method": "GET",
                "data_type": EndpointDataType.DAILY_QUOTES,
                "required_parameters": ["idtoken"],
                "optional_parameters": ["code", "from", "to", "date"],
                "default_parameters": {"code": "*"},
                "batch_size": 1000,
                "rate_limit_per_minute": 300
            }
        ]
        
        for ep_data in jquants_endpoints:
            endpoint = APIEndpoint(
                data_source_id=data_source.id,
                **ep_data
            )
            db.add(endpoint)
            endpoints.append(endpoint)
    
    elif data_source.provider_type == "yfinance":
        # Yahoo Finance用エンドポイント
        yfinance_endpoints = [
            {
                "name": "リアルタイム株価",
                "description": "現在の株価情報を取得",
                "endpoint_path": "/quote",
                "http_method": "GET",
                "data_type": EndpointDataType.REALTIME_QUOTES,
                "required_parameters": ["symbol"],
                "rate_limit_per_minute": 2000
            },
            {
                "name": "ヒストリカルデータ",
                "description": "過去の株価データを取得",
                "endpoint_path": "/history",
                "http_method": "GET",
                "data_type": EndpointDataType.HISTORICAL_DATA,
                "required_parameters": ["symbol"],
                "optional_parameters": ["period", "interval", "start", "end"],
                "default_parameters": {"period": "1mo", "interval": "1d"},
                "rate_limit_per_minute": 1000
            },
            {
                "name": "企業プロファイル",
                "description": "企業の基本情報を取得",
                "endpoint_path": "/info",
                "http_method": "GET",
                "data_type": EndpointDataType.COMPANY_PROFILE,
                "required_parameters": ["symbol"],
                "rate_limit_per_minute": 500
            }
        ]
        
        for ep_data in yfinance_endpoints:
            endpoint = APIEndpoint(
                data_source_id=data_source.id,
                **ep_data
            )
            db.add(endpoint)
            endpoints.append(endpoint)
    
    db.commit()
    
    # リフレッシュして返す
    for endpoint in endpoints:
        db.refresh(endpoint)
    
    return endpoints