#!/usr/bin/env python
"""Test script for manually executing fetch_listed_info_task via Celery."""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_task():
    """手動で Celery タスクを実行して listed_info を取得"""
    try:
        # Celery タスクをインポート
        from app.infrastructure.celery.tasks.listed_info_task import fetch_listed_info_task
        
        print("=" * 80)
        print("Celery タスク手動実行テスト - fetch_listed_info_task")
        print("=" * 80)
        
        # 実行パラメータの設定
        params = {
            "schedule_id": None,  # 手動実行なので None
            "from_date": None,    # period_type が yesterday の場合は自動計算される
            "to_date": None,      # period_type が yesterday の場合は自動計算される
            "codes": None,        # 全銘柄を取得
            "market": None,       # 全市場を取得
            "period_type": "yesterday"  # 昨日のデータを取得
        }
        
        print("\n 実行パラメータ:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        print("\n 実行方法を選択してください:")
        print("1. 非同期実行 (.delay()) - Celery ワーカーが必要")
        print("2. 同期実行 (.apply()) - 即座に実行")
        print("3. 直接実行 (関数呼び出し) - Celery を経由しない")
        
        # 非対話的モードで実行する場合は選択 3 (直接実行) を使用
        import os
        if os.environ.get('CI') or not sys.stdin.isatty():
            print("
⚠️  非対話的モードで実行中のため、選択 3 (直接実行) を自動選択します")
            choice = "3"
        else:
            choice = input("
 選択 (1/2/3): ").strip()
        
        if choice == "1":
            print("\n 非同期実行を開始します...")
            print("注意: Celery ワーカーが起動している必要があります")
            print("ワーカー起動コマンド: celery -A app.infrastructure.celery.app worker --loglevel=info")
            
            result = fetch_listed_info_task.delay(**params)
            print(f"\n タスクがキューに追加されました")
            print(f"タスク ID: {result.id}")
            print(f"ステータス: {result.status}")
            
            print("\n 結果を待機しています... (最大 300 秒)")
            try:
                task_result = result.get(timeout=300)
                print("\n✅ タスクが正常に完了しました")
                print(f"結果: {task_result}")
            except Exception as e:
                print(f"\n❌ タスクの実行に失敗しました: {e}")
                
        elif choice == "2":
            print("\n 同期実行を開始します...")
            result = fetch_listed_info_task.apply(kwargs=params)
            print(f"\n タスク ID: {result.id}")
            print(f"ステータス: {result.status}")
            
            if result.successful():
                print("\n✅ タスクが正常に完了しました")
                print(f"結果: {result.result}")
            else:
                print(f"\n❌ タスクの実行に失敗しました")
                if result.traceback:
                    print(f"エラー詳細:\n{result.traceback}")
                    
        elif choice == "3":
            print("\n 直接実行を開始します...")
            print("注意: この方法では Celery の機能（リトライ、ログ記録など）は使用されません")
            
            # タスクを直接実行（self 引数は None またはダミーオブジェクトを渡す）
            class DummyRequest:
                id = f"manual-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            class DummySelf:
                request = DummyRequest()
            
            result = fetch_listed_info_task(DummySelf(), **params)
            print("\n✅ タスクが完了しました")
            print(f"結果: {result}")
            
        else:
            print("\n 無効な選択です")
            return
            
    except ImportError as e:
        print(f"\n❌ インポートエラー: {e}")
        print("\nCelery タスクが見つかりません。以下を確認してください：")
        print("1. プロジェクトルートから実行しているか")
        print("2. 必要な依存関係がインストールされているか")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Celery 手動実行テストスクリプト")
    print("-" * 40)
    
    # 環境確認
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        if not settings.jquants_email or not settings.jquants_password:
            print("\n⚠️  警告: J-Quants 認証情報が設定されていません")
            print("環境変数 JQUANTS_EMAIL と JQUANTS_PASSWORD を設定してください")
            
    except Exception as e:
        print(f"\n 設定の読み込みに失敗しました: {e}")
    
    run_task()