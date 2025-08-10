#!/usr/bin/env python
"""即座に実行されるスケジュールを作成してテストするスクリプト"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import json

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.tasks import fetch_listed_info_task


async def create_immediate_schedule():
    """現在時刻で実行されるスケジュールを作成"""
    settings = get_settings()
    
    # 非同期エンジンを作成
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    print("=" * 80)
    print("即時実行スケジュール作成テスト")
    print("=" * 80)
    print()
    
    # 現在時刻を取得
    now_utc = datetime.utcnow()
    now_jst = datetime.now()
    
    print(f"現在時刻:")
    print(f"  UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  JST: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 毎分実行する cron 式を作成（すべての分で実行）
    cron_expression_utc = "* * * * *"  # 毎分実行
    
    schedule_id = uuid4()
    schedule_name = f"immediate_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # パラメータを準備
    task_params = {
        "period_type": "custom",
        "from_date": "2024-08-06",
        "to_date": "2024-08-06",
        "codes": None,
        "market": None,
        "schedule_id": str(schedule_id)
    }
    
    print(f"作成するスケジュール:")
    print(f"  ID: {schedule_id}")
    print(f"  名前: {schedule_name}")
    print(f"  タスク名: fetch_listed_info_task")
    print(f"  Cron 式: {cron_expression_utc} (毎分実行)")
    print(f"  パラメータ: {json.dumps(task_params, ensure_ascii=False, indent=2)}")
    print()
    
    async with async_session() as session:
        try:
            # 既存のテストスケジュールを削除
            await session.execute(
                text("DELETE FROM celery_beat_schedules WHERE name LIKE '%test%'")
            )
            
            # 新しいスケジュールを挿入
            await session.execute(
                text("""
                    INSERT INTO celery_beat_schedules 
                    (id, name, task_name, cron_expression, enabled, args, kwargs, description)
                    VALUES 
                    (:id, :name, :task_name, :cron_expression, :enabled, :args, :kwargs, :description)
                """),
                {
                    "id": schedule_id,
                    "name": schedule_name,
                    "task_name": "fetch_listed_info_task",
                    "cron_expression": cron_expression_utc,
                    "enabled": True,
                    "args": json.dumps([]),
                    "kwargs": json.dumps(task_params),
                    "description": f"毎分実行テスト"
                }
            )
            
            await session.commit()
            print("✅ スケジュール作成成功")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()
    
    print("\n" + "=" * 80)
    print("次のステップ:")
    print("1. Celery Beat のログを監視:")
    print("   docker-compose logs -f celery-beat | grep -E '(immediate_test|Applying|Sending|ERROR)'")
    print("2. Celery Worker のログを監視:")
    print("   docker-compose logs -f celery-worker | grep -E '(fetch_listed_info|immediate_test)'")
    print("3. 次の実行は 1 分以内に発生するはずです")
    print("=" * 80)


async def main():
    """メイン処理"""
    # Celery タスクが登録されているか確認
    if 'fetch_listed_info_task' in celery_app.tasks:
        print("✅ Celery タスク 'fetch_listed_info_task' が登録されています")
    else:
        print("❌ Celery タスク 'fetch_listed_info_task' が見つかりません")
        return
    
    # 即時実行スケジュールを作成
    await create_immediate_schedule()


if __name__ == "__main__":
    asyncio.run(main())