"""
Celery Beat初期化
データベースからスケジュール設定を読み込む
"""

import asyncio
from datetime import time as datetime_time
from celery.schedules import crontab
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.api_endpoint import APIEndpointSchedule
import pytz
from datetime import datetime

def load_schedules_from_database():
    """データベースからスケジュール設定を読み込む"""
    
    async def _load_schedules():
        schedules = {}
        
        async with async_session_maker() as db:
            # 有効なスケジュールを取得
            result = await db.execute(
                select(APIEndpointSchedule).where(APIEndpointSchedule.is_enabled == True)
            )
            db_schedules = result.scalars().all()
            
            for schedule in db_schedules:
                # JSTの時刻をUTCに変換
                jst_time = schedule.execution_time
                
                # 今日の日付でdatetimeを作成
                jst = pytz.timezone('Asia/Tokyo')
                utc = pytz.UTC
                today = datetime.now(jst).date()
                jst_datetime = jst.localize(datetime.combine(today, jst_time))
                utc_datetime = jst_datetime.astimezone(utc)
                
                schedule_name = f"sync_companies_{schedule.endpoint_id}"
                schedules[schedule_name] = {
                    'task': 'sync_listed_companies',
                    'schedule': crontab(
                        hour=utc_datetime.hour,
                        minute=utc_datetime.minute
                    ),
                    'kwargs': {'execution_type': 'scheduled'},
                    'options': {
                        'queue': 'default',
                        'expires': 3600,
                    }
                }
                
                print(f"Loaded schedule: {schedule_name} - JST {jst_time} -> UTC {utc_datetime.hour}:{utc_datetime.minute:02d}")
        
        return schedules
    
    # 同期的に実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_load_schedules())
    finally:
        loop.close()