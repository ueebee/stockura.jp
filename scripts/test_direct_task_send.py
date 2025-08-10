#!/usr/bin/env python
"""タスクを直接送信して Worker の動作を確認するスクリプト"""
import sys
from pathlib import Path

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.tasks import fetch_listed_info_task


def test_direct_send():
    """タスクを直接送信"""
    print("=" * 80)
    print("タスク直接送信テスト")
    print("=" * 80)
    print()
    
    # タスクが登録されているか確認
    if 'fetch_listed_info_task' not in celery_app.tasks:
        print("❌ タスクが登録されていません")
        return
    
    print("✅ タスク 'fetch_listed_info_task' が登録されています")
    
    # タスクを送信
    try:
        result = fetch_listed_info_task.delay(
            schedule_id=None,
            from_date="2024-08-06",
            to_date="2024-08-06",
            codes=None,
            market=None,
            period_type="custom"
        )
        
        print(f"\n✅ タスク送信成功")
        print(f"  タスク ID: {result.id}")
        print(f"  ステータス: {result.status}")
        print()
        print("Worker ログを確認してください:")
        print("  docker-compose logs -f celery-worker")
        
    except Exception as e:
        print(f"❌ エラー: {e}")


if __name__ == "__main__":
    test_direct_send()