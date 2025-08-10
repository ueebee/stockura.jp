#!/usr/bin/env python
"""API を経由せずに直接スケジュールを作成してテストするスクリプト"""
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


async def create_test_schedule():
    """テスト用のスケジュールを直接 DB に作成"""
    settings = get_settings()
    
    # 非同期エンジンを作成
    engine = create_async_engine(
        settings.database_url,
        echo=True,  # SQL ログを表示
        future=True,
    )
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    print("=" * 80)
    print("直接スケジュール作成テスト")
    print("=" * 80)
    print()
    
    # 2 分後の実行時刻を設定
    now = datetime.now()
    target_time = now + timedelta(minutes=2)
    cron_expression = f"{target_time.minute} {target_time.hour} * * *"
    
    schedule_id = uuid4()
    schedule_name = f"direct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # パラメータを準備
    task_params = {
        "period_type": "custom",
        "from_date": "2024-08-06",
        "to_date": "2024-08-06",
        "codes": None,
        "market": None
    }
    
    print(f"作成するスケジュール:")
    print(f"  ID: {schedule_id}")
    print(f"  名前: {schedule_name}")
    print(f"  タスク名: fetch_listed_info_task")
    print(f"  Cron 式: {cron_expression}")
    print(f"  実行予定: {target_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"  パラメータ: {json.dumps(task_params, ensure_ascii=False, indent=2)}")
    print()
    
    async with async_session() as session:
        try:
            # スケジュールを挿入
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
                    "cron_expression": cron_expression,
                    "enabled": True,
                    "args": json.dumps([]),
                    "kwargs": json.dumps(task_params),
                    "description": f"直接作成テスト - {target_time.strftime('%Y-%m-%d %H:%M')}に実行"
                }
            )
            
            await session.commit()
            print("✅ スケジュール作成成功")
            
            # 作成したスケジュールを確認
            result = await session.execute(
                text("SELECT * FROM celery_beat_schedules WHERE id = :id"),
                {"id": schedule_id}
            )
            schedule = result.fetchone()
            
            if schedule:
                print("\n 作成されたスケジュール:")
                print(f"  確認: スケジュールが DB に保存されました")
                print(f"  kwargs: {schedule.kwargs}")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()
    
    print("\n" + "=" * 80)
    print("次のステップ:")
    print("1. Celery Beat が起動していることを確認")
    print("2. Celery Worker が起動していることを確認")
    print(f"3. {target_time.strftime('%H:%M')}に実行されるか監視")
    print("4. デバッグスクリプトで確認: python scripts/debug_celery_schedules.py")
    print("=" * 80)


async def check_existing_schedules():
    """既存のスケジュールを確認"""
    settings = get_settings()
    
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
    
    async with async_session() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM celery_beat_schedules")
        )
        count = result.scalar()
        print(f"\n 現在のスケジュール数: {count}")
        
        if count > 0:
            result = await session.execute(
                text("""
                    SELECT id, name, task_name, enabled, created_at 
                    FROM celery_beat_schedules 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
            )
            schedules = result.fetchall()
            print("\n 最近のスケジュール:")
            for s in schedules:
                print(f"  - {s.name} ({s.task_name}) - 有効: {s.enabled} - 作成: {s.created_at}")
    
    await engine.dispose()


async def main():
    """メイン処理"""
    # Celery タスクが登録されているか確認
    if 'fetch_listed_info_task' in celery_app.tasks:
        print("✅ Celery タスク 'fetch_listed_info_task' が登録されています")
    else:
        print("❌ Celery タスク 'fetch_listed_info_task' が見つかりません")
        return
    
    # 既存のスケジュールを確認
    await check_existing_schedules()
    
    # 新しいスケジュールを作成
    await create_test_schedule()


if __name__ == "__main__":
    asyncio.run(main())