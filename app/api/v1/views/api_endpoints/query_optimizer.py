"""
APIエンドポイント管理のクエリ最適化機能
N+1問題を回避するためのバッチクエリ実装
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models import APIEndpoint, APIEndpointSchedule, EndpointDataType
from app.models.daily_quote_schedule import DailyQuoteSchedule
from app.models.daily_quote import DailyQuotesSyncHistory


def get_batch_schedule_info(db: Session, endpoints: List[APIEndpoint]) -> Dict[int, Optional[Dict[str, Any]]]:
    """
    複数のエンドポイントのスケジュール情報を一括取得
    
    Args:
        db: データベースセッション
        endpoints: エンドポイントのリスト
        
    Returns:
        エンドポイントIDをキーとするスケジュール情報の辞書
    """
    result = {}
    
    # エンドポイントをデータタイプ別にグループ化
    companies_endpoints = []
    daily_quotes_data_source_ids = set()
    
    for endpoint in endpoints:
        if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
            companies_endpoints.append(endpoint.id)
        elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
            daily_quotes_data_source_ids.add(endpoint.data_source_id)
        result[endpoint.id] = None
    
    # 上場企業一覧のスケジュールを一括取得
    if companies_endpoints:
        schedules = db.query(APIEndpointSchedule).filter(
            APIEndpointSchedule.endpoint_id.in_(companies_endpoints)
        ).all()
        
        for schedule in schedules:
            result[schedule.endpoint_id] = {
                "is_enabled": schedule.is_enabled,
                "execution_time": schedule.execution_time,
                "schedule_type": "daily"
            }
    
    # 日次株価データのスケジュールを一括取得
    if daily_quotes_data_source_ids:
        active_schedules = db.query(DailyQuoteSchedule).filter(
            DailyQuoteSchedule.data_source_id.in_(daily_quotes_data_source_ids),
            DailyQuoteSchedule.is_enabled == True
        ).all()
        
        # データソースIDごとに最初の有効なスケジュールをマッピング
        data_source_schedules = {}
        for schedule in active_schedules:
            if schedule.data_source_id not in data_source_schedules:
                data_source_schedules[schedule.data_source_id] = {
                    "is_enabled": True,
                    "execution_time": schedule.execution_time,
                    "schedule_type": schedule.schedule_type
                }
        
        # エンドポイントにマッピング
        for endpoint in endpoints:
            if endpoint.data_type == EndpointDataType.DAILY_QUOTES:
                if endpoint.data_source_id in data_source_schedules:
                    result[endpoint.id] = data_source_schedules[endpoint.data_source_id]
    
    return result


def get_batch_execution_stats(db: Session, endpoints: List[APIEndpoint]) -> Dict[int, Dict[str, Any]]:
    """
    複数のエンドポイントの実行統計情報を一括取得
    
    Args:
        db: データベースセッション
        endpoints: エンドポイントのリスト
        
    Returns:
        エンドポイントIDをキーとする統計情報の辞書
    """
    result = {}
    
    # 日次株価データのエンドポイントIDを収集
    daily_quotes_endpoint_ids = []
    
    for endpoint in endpoints:
        if endpoint.data_type == EndpointDataType.LISTED_COMPANIES:
            # 上場企業一覧はエンドポイントの値をそのまま使用
            result[endpoint.id] = {
                "last_execution_at": endpoint.last_execution_at,
                "last_success_at": endpoint.last_success_at,
                "last_error_at": endpoint.last_error_at,
                "total_executions": endpoint.total_executions,
                "successful_executions": endpoint.successful_executions,
                "last_data_count": endpoint.last_data_count
            }
        elif endpoint.data_type == EndpointDataType.DAILY_QUOTES:
            daily_quotes_endpoint_ids.append(endpoint.id)
            # デフォルト値を設定
            result[endpoint.id] = {
                "last_execution_at": None,
                "last_success_at": None,
                "last_error_at": None,
                "total_executions": 0,
                "successful_executions": 0,
                "last_data_count": None
            }
        else:
            # その他のエンドポイントタイプ
            result[endpoint.id] = {
                "last_execution_at": endpoint.last_execution_at,
                "last_success_at": endpoint.last_success_at,
                "last_error_at": endpoint.last_error_at,
                "total_executions": endpoint.total_executions,
                "successful_executions": endpoint.successful_executions,
                "last_data_count": endpoint.last_data_count
            }
    
    # 日次株価データの統計を一括取得
    if daily_quotes_endpoint_ids:
        # 集計クエリ（現在はdata_source_idごとの集計なので、全体を取得）
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
        
        # 最新の実行履歴を取得
        latest_history = db.query(DailyQuotesSyncHistory).order_by(
            DailyQuotesSyncHistory.started_at.desc()
        ).first()
        
        last_data_count = None
        if latest_history and latest_history.total_records:
            last_data_count = latest_history.total_records
        
        # 全ての日次株価エンドポイントに同じ統計を設定
        for endpoint_id in daily_quotes_endpoint_ids:
            result[endpoint_id] = {
                "last_execution_at": stats.last_execution,
                "last_success_at": stats.last_success,
                "last_error_at": stats.last_error,
                "total_executions": stats.total_executions or 0,
                "successful_executions": stats.successful_executions or 0,
                "last_data_count": last_data_count
            }
    
    return result