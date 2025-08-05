#!/usr/bin/env python3
"""Celery trades_spec タスクのデバッグスクリプト"""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリを PYTHONPATH に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.celery.tasks.trades_spec_task_asyncpg import (
    _fetch_trades_spec_async,
    fetch_trades_spec_task_asyncpg
)


async def test_async_function_directly():
    """非同期関数を直接テスト"""
    print("=== 非同期関数の直接テスト ===\n")
    
    try:
        # 日付範囲を設定
        to_date = date.today() - timedelta(days=1)
        from_date = to_date - timedelta(days=0)  # 1 日分のみ
        
        print(f"期間: {from_date} ~ {to_date}")
        print(f"市場区分: TSEPrime\n")
        
        # 非同期関数を直接呼び出し
        result = await _fetch_trades_spec_async(
            section="TSEPrime",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            max_pages=1,
            task_id="test-direct-async"
        )
        
        print("結果:")
        print(f"  成功: {result.get('success')}")
        print(f"  取得件数: {result.get('fetched_count')}")
        print(f"  保存件数: {result.get('saved_count')}")
        
        if not result.get('success'):
            print(f"  エラー: {result.get('error')}")
            
    except Exception as e:
        print(f"\n✗ エラー発生: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


def test_celery_task_sync():
    """Celery タスクを同期的にテスト"""
    print("\n=== Celery タスクの同期テスト ===\n")
    
    try:
        # 日付範囲を設定
        to_date = date.today() - timedelta(days=1)
        from_date = to_date
        
        print(f"期間: {from_date} ~ {to_date}")
        print(f"市場区分: TSEPrime\n")
        
        # Celery タスクを直接実行（非同期キューを使わない）
        result = fetch_trades_spec_task_asyncpg(
            section="TSEPrime",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            max_pages=1
        )
        
        print("結果:")
        print(f"  成功: {result.get('success')}")
        print(f"  取得件数: {result.get('fetched_count')}")
        print(f"  保存件数: {result.get('saved_count')}")
        
        if not result.get('success'):
            print(f"  エラー: {result.get('error')}")
            
    except Exception as e:
        print(f"\n✗ エラー発生: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


def test_celery_task_async():
    """Celery タスクを非同期キューでテスト"""
    print("\n=== Celery タスクの非同期キューテスト ===\n")
    
    try:
        # 日付範囲を設定
        to_date = date.today() - timedelta(days=1)
        from_date = to_date
        
        print(f"期間: {from_date} ~ {to_date}")
        print(f"市場区分: TSEPrime\n")
        
        # Celery タスクを非同期実行
        async_result = fetch_trades_spec_task_asyncpg.delay(
            section="TSEPrime",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            max_pages=1
        )
        
        print(f"タスク ID: {async_result.id}")
        print("結果を待機中...")
        
        # タスクの完了を待つ（最大 30 秒）
        result = async_result.get(timeout=30)
        
        print("\n 結果:")
        print(f"  成功: {result.get('success')}")
        print(f"  取得件数: {result.get('fetched_count')}")
        print(f"  保存件数: {result.get('saved_count')}")
        
        if not result.get('success'):
            print(f"  エラー: {result.get('error')}")
            
    except Exception as e:
        print(f"\n✗ エラー発生: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Celery trades_spec タスクのデバッグ")
    print("=" * 60)
    
    # 1. 非同期関数を直接テスト
    asyncio.run(test_async_function_directly())
    
    # 2. Celery タスクを同期的にテスト
    test_celery_task_sync()
    
    # 3. Celery タスクを非同期キューでテスト
    test_celery_task_async()