from celery import Celery
from app.core.config import settings

# Celeryアプリケーションの作成
celery_app = Celery(
    "stockura",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.stock_tasks", "app.tasks.sample_tasks"]
)

# Celery設定
celery_app.conf.update(
    # タスクの結果を保存するかどうか
    task_ignore_result=False,
    
    # タスクの結果の有効期限（秒）
    result_expires=3600,
    
    # ワーカーの同時実行数
    worker_concurrency=4,
    
    # タスクの優先度
    task_default_priority=5,
    
    # タスクのキュー名
    task_default_queue="default",
    
    # タスクのルーティング設定
    task_routes={
        "app.tasks.stock_tasks.*": {"queue": "stock_data"},
        "app.tasks.sample_tasks.*": {"queue": "default"},
    },
    
    # レート制限の設定
    task_annotations={
        "app.tasks.stock_tasks.fetch_stock_data": {"rate_limit": "10/m"},
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
