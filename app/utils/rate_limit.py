"""
データソースベースのレートリミット管理ユーティリティ
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.db.session import get_db


class RateLimitManager:
    """データソースのレートリミット設定を管理するクラス"""
    
    _cache: Dict[str, str] = {}
    
    @classmethod
    def get_rate_limit_for_provider(
        cls,
        provider_type: str,
        db: Optional[Session] = None
    ) -> str:
        """
        プロバイダータイプに基づいてレートリミットを取得
        
        Args:
            provider_type: プロバイダーのタイプ（"jquants", "yfinance"など）
            db: データベースセッション（オプショナル）
            
        Returns:
            Celery形式のレートリミット文字列（例: "10/m"）
        """
        # キャッシュをチェック
        if provider_type in cls._cache:
            return cls._cache[provider_type]
        
        # データベースから取得
        if db is None:
            db = next(get_db())
            
        try:
            data_source = db.query(DataSource).filter(
                DataSource.provider_type == provider_type,
                DataSource.is_enabled == True
            ).first()
            
            if data_source:
                # 分あたりのレートリミットを優先的に使用
                rate_limit = f"{data_source.rate_limit_per_minute}/m"
                cls._cache[provider_type] = rate_limit
                return rate_limit
            else:
                # デフォルト値
                default_rates = {
                    "jquants": "10/m",
                    "yfinance": "30/m",
                }
                return default_rates.get(provider_type, "60/m")
                
        finally:
            if db:
                db.close()
    
    @classmethod
    def clear_cache(cls):
        """キャッシュをクリア"""
        cls._cache.clear()
    
    @classmethod
    def get_rate_limit_for_data_source(
        cls,
        data_source_id: int,
        db: Optional[Session] = None
    ) -> str:
        """
        データソースIDに基づいてレートリミットを取得
        
        Args:
            data_source_id: データソースのID
            db: データベースセッション（オプショナル）
            
        Returns:
            Celery形式のレートリミット文字列（例: "10/m"）
        """
        if db is None:
            db = next(get_db())
            
        try:
            data_source = db.query(DataSource).filter(
                DataSource.id == data_source_id,
                DataSource.is_enabled == True
            ).first()
            
            if data_source:
                # 分あたりのレートリミットを使用
                return f"{data_source.rate_limit_per_minute}/m"
            else:
                # デフォルト値
                return "60/m"
                
        finally:
            if db:
                db.close()