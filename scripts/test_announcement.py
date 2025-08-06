#!/usr/bin/env python3
"""決算発表予定データ取得スクリプト"""

import asyncio
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# 自動入力ユーティリティをインポート
try:
    from scripts.utils.auto_input import get_auto_input
except ImportError:
    # フォールバック: 通常の input を使用
    def get_auto_input(prompt: str, default: Optional[str] = None) -> str:
        user_input = input(prompt).strip()
        return user_input if user_input else (default or '')

from app.application.use_cases.fetch_announcement import FetchAnnouncementUseCase
from app.core.logger import get_logger
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.repositories.database.announcement_repository_impl import AnnouncementRepositoryImpl

logger = get_logger(__name__)


async def test_celery_task():
    """Celery タスクを使用してデータを取得"""
    try:
        from app.infrastructure.celery.tasks.announcement_task_asyncpg import fetch_announcement_data
        
        print("\n✅ Celery タスクのインポートに成功しました")
        
        # タスクを非同期実行
        print("\n📤 タスクをキューに送信しています...")
        result = fetch_announcement_data.delay()
        
        print(f"✅ タスクが送信されました")
        print(f"   タスク ID: {result.id}")
        print(f"   ステータス: {result.status}")
        
        # タスクの完了を待つ（最大 60 秒）
        print("\n⏳ タスクの完了を待機中...")
        try:
            task_result = result.get(timeout=60)
            print("\n✅ タスクが完了しました")
            print(f"   結果: {task_result}")
        except Exception as e:
            print(f"\n⚠️  タスクのタイムアウトまたはエラー: {e}")
            print("   Celery ワーカーが起動していることを確認してください")
            
    except ImportError as e:
        logger.error(f"Celery タスクのインポートエラー: {e}")
        print(f"\n❌ Celery タスクのインポートに失敗しました: {e}")
    except Exception as e:
        logger.error(f"Celery タスク実行エラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")


async def test_api_connection():
    """J-Quants API 接続テスト"""
    print("\n=== J-Quants API 接続テスト ===")
    
    try:
        factory = JQuantsClientFactory()
        client = await factory.create_announcement_client()
        
        print("✓ API クライアント作成成功")
        
        # 少量のデータで接続テスト
        print("\n テストデータ取得中...")
        response = await client.get_announcements()
        
        announcements = response.get("announcement", [])
        print(f"✓ データ取得成功: {len(announcements)} 件")
        
        if announcements:
            sample = announcements[0]
            print(f"\n サンプルデータ:")
            print(f"  発表日: {sample.get('Date')}")
            print(f"  銘柄コード: {sample.get('Code')}")
            print(f"  会社名: {sample.get('CompanyName')}")
            print(f"  決算期: {sample.get('FiscalYear')}")
            print(f"  四半期: {sample.get('FiscalQuarter')}")
        
        return True
        
    except Exception as e:
        print(f"✗ エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def fetch_and_save_announcements():
    """決算発表予定データを取得して DB に保存"""
    print("\n=== 決算発表予定データ取得・保存 ===")
    
    try:
        factory = JQuantsClientFactory()
        client = await factory.create_announcement_client()
        
        async with get_async_session_context() as session:
            repository = AnnouncementRepositoryImpl(session)
            use_case = FetchAnnouncementUseCase(
                announcement_client=client,
                announcement_repository=repository,
            )
            
            print("データ取得中...")
            result = await use_case.fetch_and_save_announcements()
            
            print(f"✓ {result.total_count} 件のデータを取得・保存しました")
            
            # 取得したデータのサンプル表示
            if result.announcements:
                print("\n=== 取得データサンプル（最新 10 件） ===")
                for i, announcement in enumerate(result.announcements[:10], 1):
                    print(f"\n{i}. {announcement.company_name} ({announcement.code})")
                    print(f"   発表日: {announcement.date}")
                    print(f"   決算期: {announcement.fiscal_year}")
                    print(f"   四半期: {announcement.fiscal_quarter}")
                    print(f"   業種: {announcement.sector_name}")
                    print(f"   市場: {announcement.section}")
                
                if result.total_count > 10:
                    print(f"\n... 他 {result.total_count - 10} 件")
            
            return True
            
    except Exception as e:
        print(f"✗ エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def query_saved_data():
    """保存されたデータの検索テスト"""
    print("\n=== 保存データ検索テスト ===")
    
    try:
        factory = JQuantsClientFactory()
        client = await factory.create_announcement_client()
        
        async with get_async_session_context() as session:
            repository = AnnouncementRepositoryImpl(session)
            use_case = FetchAnnouncementUseCase(
                announcement_client=client,
                announcement_repository=repository,
            )
            
            # 最新データの取得
            print("\n1. 最新の決算発表予定を取得")
            latest = await use_case.get_latest_announcements()
            print(f"✓ {latest.total_count} 件の最新データ")
            
            if latest.announcements:
                # 特定日付での検索
                target_date = latest.announcements[0].date
                print(f"\n2. {target_date} の決算発表予定を検索")
                by_date = await use_case.get_announcements_by_date(target_date)
                print(f"✓ {by_date.total_count} 件見つかりました")
                
                # 特定銘柄での検索
                target_code = latest.announcements[0].code
                print(f"\n3. 銘柄コード {target_code} の決算発表予定を検索")
                by_code = await use_case.get_announcements_by_code(target_code)
                print(f"✓ {by_code.total_count} 件見つかりました")
                
                if by_code.announcements:
                    print("\n 検索結果サンプル:")
                    for ann in by_code.announcements[:3]:
                        print(f"  - {ann.date}: {ann.fiscal_quarter} ({ann.fiscal_year})")
            
            return True
            
    except Exception as e:
        print(f"✗ エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """メイン処理"""
    print("=" * 60)
    print("決算発表予定データ取得スクリプト")
    print("=" * 60)
    
    # 環境変数チェック
    if not os.getenv("JQUANTS_EMAIL") or not os.getenv("JQUANTS_PASSWORD"):
        print("\n✗ エラー: J-Quants 認証情報が設定されていません")
        print("以下の環境変数を設定してください:")
        print("  - JQUANTS_EMAIL")
        print("  - JQUANTS_PASSWORD")
        return
    
    # コマンドライン引数または環境変数から選択を取得
    import sys
    choice = None
    
    # コマンドライン引数から取得
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    # 環境変数から取得（CI/CD 用）
    elif os.getenv("TEST_CHOICE"):
        choice = os.getenv("TEST_CHOICE")
    # 非対話的環境では全て実行
    elif not sys.stdin.isatty():
        choice = "4"
    else:
        # 対話的環境のみプロンプトを表示
        print("\n 実行する処理を選択してください:")
        print("1. API 接続テストのみ")
        print("2. データ取得・保存")
        print("3. 保存データ検索テスト")
        print("4. すべて実行")
        print("5. Celery タスク実行（非同期）")
        
        choice = get_auto_input("\n 選択 (1-5): ")
    
    tasks = []
    if choice == "1":
        tasks = [("API 接続テスト", test_api_connection)]
    elif choice == "2":
        tasks = [("データ取得・保存", fetch_and_save_announcements)]
    elif choice == "3":
        tasks = [("保存データ検索", query_saved_data)]
    elif choice == "4":
        tasks = [
            ("API 接続テスト", test_api_connection),
            ("データ取得・保存", fetch_and_save_announcements),
            ("保存データ検索", query_saved_data),
        ]
    elif choice == "5":
        tasks = [("Celery タスク実行", test_celery_task)]
    else:
        print("無効な選択です")
        return
    
    # 処理実行
    results = []
    for task_name, task_func in tasks:
        print(f"\n{'='*60}")
        print(f"実行: {task_name}")
        print('='*60)
        
        success = await task_func()
        results.append((task_name, success))
    
    # 結果サマリー
    print(f"\n\n{'='*60}")
    print("実行結果サマリー")
    print('='*60)
    
    for task_name, success in results:
        status = "✓ 成功" if success else "✗ 失敗"
        print(f"{task_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n 合計: {passed}/{total} 成功")
    
    if passed == total:
        print("\n✓ すべての処理が正常に完了しました")
    else:
        print("\n✗ 一部の処理が失敗しました")


if __name__ == "__main__":
    asyncio.run(main())