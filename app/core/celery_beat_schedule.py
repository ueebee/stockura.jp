"""
Celery Beatスケジュール設定
"""

from celery.schedules import crontab

# Beatスケジュール設定
CELERY_BEAT_SCHEDULE = {
    # 日次タスク - J-Quants API接続テスト（毎日午前5時）
    'daily-token-refresh': {
        'task': 'app.tasks.company_tasks.test_jquants_connection',
        'schedule': crontab(hour=5, minute=0),
        'args': (1,),  # J-QuantsデータソースID
        'options': {
            'queue': 'default',
            'expires': 3600,  # 1時間でタスクを期限切れに
        }
    },
    
    # 週次タスク - 企業データ同期（毎週日曜日午前6時）
    'weekly-company-sync': {
        'task': 'app.tasks.company_tasks.daily_company_sync',
        'schedule': crontab(hour=6, minute=0, day_of_week=0),
        'args': ([1],),  # J-QuantsデータソースIDのリスト
        'options': {
            'queue': 'default',
            'expires': 7200,  # 2時間でタスクを期限切れに
        }
    },
    
    # 定期テストタスク（開発用、本番では無効化を推奨）
    # 'periodic-test': {
    #     'task': 'app.tasks.sample_tasks.periodic_task',
    #     'schedule': crontab(minute='*/30'),  # 30分ごと
    #     'options': {
    #         'queue': 'default',
    #     }
    # },
    
    # 上場企業一覧の日次同期（デフォルト: 毎日午前5時）
    # 注: 実際のスケジュールはAPIEndpointScheduleテーブルで管理され、
    # ScheduleServiceによって動的に更新されます
    'sync_companies_default': {
        'task': 'sync_listed_companies',
        'schedule': crontab(hour=5, minute=0),
        'options': {
            'queue': 'default',
            'timezone': 'Asia/Tokyo',
            'expires': 3600,  # 1時間でタスクを期限切れに
        }
    },
}