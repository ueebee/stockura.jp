#!/usr/bin/env python
"""UTC 時間でスケジュールを作成するテストスクリプト"""
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


async def create_utc_schedule():
    """UTC 時間でスケジュールを作成"""
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
    print("UTC 時間でのスケジュール作成テスト")
    print("=" * 80)
    print()
    
    # 現在時刻を取得
    now_utc = datetime.utcnow()
    now_jst = datetime.now()
    
    print(f"現在時刻:")
    print(f"  UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  JST: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 2 分後の実行時刻を設定（UTC）
    target_time_utc = now_utc + timedelta(minutes=2)
    cron_expression_utc = f"{target_time_utc.minute} {target_time_utc.hour} * * *"
    
    # JST 換算
    target_time_jst = target_time_utc + timedelta(hours=9)
    
    schedule_id = uuid4()
    schedule_name = f"utc_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # パラメータを準備
    task_params = {
        "period_type": "custom",
        "from_date": "2024-08-06",
        "to_date": "2024-08-06",
        "codes": None,
        "market": None,
        "schedule_id": str(schedule_id)  # スケジュール ID を含める
    }
    
    print(f"作成するスケジュール:")
    print(f"  ID: {schedule_id}")
    print(f"  名前: {schedule_name}")
    print(f"  タスク名: fetch_listed_info_task")
    print(f"  Cron 式（UTC）: {cron_expression_utc}")
    print(f"  実行予定（UTC）: {target_time_utc.strftime('%Y-%m-%d %H:%M')}")
    print(f"  実行予定（JST）: {target_time_jst.strftime('%Y-%m-%d %H:%M')}")
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
                    "description": f"UTC テスト - {target_time_utc.strftime('%Y-%m-%d %H:%M')} UTC / {target_time_jst.strftime('%Y-%m-%d %H:%M')} JST に実行"
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
    print("   docker-compose logs -f celery-beat")
    print("2. Celery Worker のログを監視:")
    print("   docker-compose logs -f celery-worker")
    print(f"3. 実行予定時刻:")
    print(f"   UTC: {target_time_utc.strftime('%H:%M:%S')}")
    print(f"   JST: {target_time_jst.strftime('%H:%M:%S')}")
    print("=" * 80)


async def main():
    """メイン処理"""
    # Celery タスクが登録されているか確認
    if 'fetch_listed_info_task' in celery_app.tasks:
        print("✅ Celery タスク 'fetch_listed_info_task' が登録されています")
    else:
        print("❌ Celery タスク 'fetch_listed_info_task' が見つかりません")
        return
    
    # UTC 時間でスケジュールを作成
    await create_utc_schedule()


if __name__ == "__main__":
    asyncio.run(main())