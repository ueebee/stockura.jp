#!/usr/bin/env python
"""Celery Beat のスケジュール状況をデバッグするスクリプト"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.infrastructure.celery.app import celery_app

# タスクを明示的にインポート
try:
    from app.infrastructure.celery.tasks import fetch_listed_info_task
    print("タスクのインポート成功")
except Exception as e:
    print(f"タスクのインポートエラー: {e}")


async def check_celery_beat_schedules():
    """celery_beat_schedules テーブルの内容を確認"""
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
    print("Celery Beat Schedules デバッグ情報")
    print("=" * 80)
    print()
    
    async with async_session() as session:
        # 1. テーブルの存在確認
        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'celery_beat_schedules'
                )
            """)
        )
        table_exists = result.scalar()
        print(f"1. celery_beat_schedules テーブル存在: {table_exists}")
        
        if not table_exists:
            print("   ⚠️  テーブルが存在しません！")
            return
            
        # 2. スケジュール一覧を取得
        result = await session.execute(
            text("""
                SELECT 
                    id,
                    name,
                    task_name,
                    cron_expression,
                    enabled,
                    kwargs,
                    created_at,
                    updated_at
                FROM celery_beat_schedules
                ORDER BY created_at DESC
            """)
        )
        schedules = result.fetchall()
        
        print(f"\n2. 登録されているスケジュール数: {len(schedules)}")
        print()
        
        for idx, schedule in enumerate(schedules, 1):
            print(f"   スケジュール {idx}:")
            print(f"   - ID: {schedule.id}")
            print(f"   - 名前: {schedule.name}")
            print(f"   - タスク名: {schedule.task_name}")
            print(f"   - Cron 式: {schedule.cron_expression}")
            print(f"   - 有効: {schedule.enabled}")
            print(f"   - 作成日時: {schedule.created_at}")
            print(f"   - 更新日時: {schedule.updated_at}")
            
            if schedule.kwargs:
                try:
                    kwargs = json.loads(schedule.kwargs) if isinstance(schedule.kwargs, str) else schedule.kwargs
                    print(f"   - パラメータ:")
                    for key, value in kwargs.items():
                        print(f"     - {key}: {value}")
                except:
                    print(f"   - パラメータ（raw）: {schedule.kwargs}")
            print()
    
    await engine.dispose()


def check_celery_tasks():
    """Celery に登録されているタスクを確認"""
    print("\n3. Celery に登録されているタスク:")
    print("   " + "-" * 70)
    
    # 登録されているタスクを取得
    tasks = list(celery_app.tasks.keys())
    tasks.sort()
    
    for task_name in tasks:
        # システムタスクは除外
        if not task_name.startswith('celery.'):
            print(f"   - {task_name}")
    
    # 特定のタスクの詳細確認
    target_task = "fetch_listed_info_task"
    if target_task in celery_app.tasks:
        print(f"\n   ✅ '{target_task}' が登録されています")
        task = celery_app.tasks[target_task]
        print(f"      - タスククラス: {task.__class__.__name__}")
        print(f"      - モジュール: {task.__module__}")
    else:
        print(f"\n   ❌ '{target_task}' が登録されていません！")
        
        # 類似のタスクを探す
        similar_tasks = [t for t in tasks if 'listed_info' in t.lower()]
        if similar_tasks:
            print(f"   類似のタスク:")
            for t in similar_tasks:
                print(f"   - {t}")


def check_celery_beat_config():
    """Celery Beat 設定を確認"""
    print("\n4. Celery Beat 設定:")
    print("   " + "-" * 70)
    
    # Beat スケジューラー設定
    scheduler = celery_app.conf.get('beat_scheduler', 'デフォルト')
    print(f"   - Beat スケジューラー: {scheduler}")
    
    # タスクルーティング設定
    task_routes = celery_app.conf.get('task_routes', {})
    print(f"   - タスクルーティング:")
    for task_name, route in task_routes.items():
        print(f"     - {task_name}: {route}")
    
    # タイムゾーン設定
    timezone = celery_app.conf.get('timezone', 'UTC')
    print(f"   - タイムゾーン: {timezone}")
    
    # その他の重要な設定
    print(f"   - broker_url: {celery_app.conf.get('broker_url', 'Not set')}")
    print(f"   - result_backend: {celery_app.conf.get('result_backend', 'Not set')}")


def suggest_solutions():
    """問題の解決策を提案"""
    print("\n5. 推奨される解決策:")
    print("   " + "-" * 70)
    
    print("\n   1. Celery Beat 起動コマンドの確認:")
    print("      正しいコマンド例:")
    print("      ```")
    print("      celery -A app.infrastructure.celery.app beat --loglevel=info")
    print("      ```")
    
    print("\n   2. Celery Worker 起動コマンドの確認:")
    print("      正しいコマンド例:")
    print("      ```")
    print("      celery -A app.infrastructure.celery.app worker --loglevel=info")
    print("      ```")
    
    print("\n   3. タスク名の確認:")
    print("      - DB の task フィールド: 'fetch_listed_info_task'")
    print("      - Celery タスク名: 'fetch_listed_info_task'")
    print("      - 完全修飾名が必要な場合: 'app.infrastructure.celery.tasks.listed_info_task.fetch_listed_info_task'")
    
    print("\n   4. ログファイルの確認:")
    print("      - Celery Beat のログでスケジュール読み込みエラーがないか")
    print("      - Celery Worker のログでタスク実行エラーがないか")


async def main():
    """メイン処理"""
    print("Celery Beat スケジュール デバッグツール")
    print("実行時刻:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # 1. DB のスケジュール確認
    await check_celery_beat_schedules()
    
    # 2. Celery タスク確認
    check_celery_tasks()
    
    # 3. Celery 設定確認
    check_celery_beat_config()
    
    # 4. 解決策の提案
    suggest_solutions()
    
    print("\n" + "=" * 80)
    print("デバッグ完了")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())