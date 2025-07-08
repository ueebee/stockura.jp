"""
Celeryタスク用のカスタムデコレーター
"""
import functools
from typing import Any, Callable, Optional
from celery import Task

from app.core.celery_app import celery_app
from app.utils.rate_limit import RateLimitManager


def data_source_rate_limited_task(
    provider_type: Optional[str] = None,
    name: Optional[str] = None,
    **task_kwargs
) -> Callable:
    """
    データソースベースのレートリミットを適用するタスクデコレーター
    
    Args:
        provider_type: プロバイダータイプ（"jquants", "yfinance"など）
        name: タスク名（オプショナル）
        **task_kwargs: その他のCeleryタスクのオプション
        
    使用例:
        @data_source_rate_limited_task(provider_type="jquants")
        def sync_companies():
            pass
            
        @data_source_rate_limited_task()  # タスク内でprovider_typeを動的に決定
        def sync_data(data_source_id: int):
            pass
    """
    def decorator(func: Callable) -> Task:
        # レートリミットを取得（provider_typeが指定されている場合）
        if provider_type:
            rate_limit = RateLimitManager.get_rate_limit_for_provider(provider_type)
            task_kwargs['rate_limit'] = rate_limit
        
        # タスクを作成
        @celery_app.task(name=name, **task_kwargs)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 動的なレートリミットの適用（data_source_idが引数にある場合）
            if 'data_source_id' in kwargs and not provider_type:
                # ここでは実行時のレートリミットは適用できないため、
                # タスク登録時のレートリミットを使用
                pass
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def dynamic_rate_limit_task(name: Optional[str] = None, **task_kwargs) -> Callable:
    """
    実行時に動的にレートリミットを決定するタスクデコレーター
    
    注意: Celeryのレートリミットはワーカー起動時に固定されるため、
    実行時の動的な変更には対応していません。
    データソースごとに異なるレートリミットが必要な場合は、
    別々のタスクを作成するか、カスタムのレートリミッター実装が必要です。
    
    Args:
        name: タスク名（オプショナル）
        **task_kwargs: その他のCeleryタスクのオプション
    """
    def decorator(func: Callable) -> Task:
        @celery_app.task(name=name, **task_kwargs)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator