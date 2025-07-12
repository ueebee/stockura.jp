from celery import Celery
from celery.signals import worker_ready
from app.core.config import settings
from app.utils.rate_limit import RateLimitManager
from app.services.auth import StrategyRegistry
from app.services.auth.strategies.jquants_strategy import JQuantsStrategy
from app.services.auth.strategies.yfinance_strategy import YFinanceStrategy
import logging

logger = logging.getLogger(__name__)

# Celeryアプリケーションの作成
celery_app = Celery(
    "stockura",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.stock_tasks",
        "app.tasks.sample_tasks",
        "app.tasks.company_tasks",
        "app.tasks.daily_quotes_tasks"
    ]
)

# Celery設定
celery_app.conf.update(
    # タスクの結果を保存するかどうか
    task_ignore_result=False,
    
    # タスクの結果の有効期限（秒）
    result_expires=3600,
    
    # ワーカーの同時実行数
    worker_concurrency=4,
    
    # ワーカープールの設定（soloを使用してシングルスレッドで実行）
    worker_pool="solo",
    
    # タスクの優先度
    task_default_priority=5,
    
    # タスクのキュー名
    task_default_queue="default",
    
    # タスクのルーティング設定
    task_routes={
        "app.tasks.stock_tasks.*": {"queue": "stock_data"},
        "app.tasks.sample_tasks.*": {"queue": "default"},
        "app.tasks.company_tasks.*": {"queue": "jquants"},
        "app.tasks.daily_quotes_tasks.*": {"queue": "jquants"},
    },
    
    # レート制限の設定
    # データソースから動的に取得するが、フォールバックとして静的な値も設定
    task_annotations={
        # yfinance API タスク
        "app.tasks.stock_tasks.fetch_stock_data": {
            "rate_limit": RateLimitManager.get_rate_limit_for_provider("yfinance")
        },
        "app.tasks.stock_tasks.fetch_stock_data_with_retry": {
            "rate_limit": RateLimitManager.get_rate_limit_for_provider("yfinance")
        },
        
        # J-Quants API タスク
        "app.tasks.company_tasks.sync_companies_task": {
            "rate_limit": RateLimitManager.get_rate_limit_for_provider("jquants")
        },
        "app.tasks.company_tasks.sync_companies_with_retry": {
            "rate_limit": RateLimitManager.get_rate_limit_for_provider("jquants")
        },
        "app.tasks.company_tasks.test_jquants_connection": {
            "rate_limit": RateLimitManager.get_rate_limit_for_provider("jquants")
        },
        "app.tasks.daily_quotes_tasks.sync_daily_quotes_task": {
            "rate_limit": RateLimitManager.get_rate_limit_for_provider("jquants")
        },
        
        # サンプルタスクのレート制限
        "app.tasks.sample_tasks.heavy_task": {"rate_limit": "5/m"},
    },
    
    # タスクの再試行設定
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # ログ設定
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

# タスクの自動検出
celery_app.autodiscover_tasks()

# Beat scheduleの読み込み
from app.core.celery_beat_schedule import CELERY_BEAT_SCHEDULE
celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

# ワーカー起動時に認証ストラテジーを登録
@worker_ready.connect
def setup_worker(sender=None, **kwargs):
    """ワーカー起動時の初期化処理"""
    logger.info("Initializing worker...")
    
    # 認証ストラテジーを登録
    try:
        StrategyRegistry.register("jquants", JQuantsStrategy)
        StrategyRegistry.register("yfinance", YFinanceStrategy)
        logger.info(f"Registered authentication strategies: jquants, yfinance")
    except Exception as e:
        logger.error(f"Failed to register authentication strategies: {e}")
        raise
