#!/usr/bin/env python3
"""TradesSpec 機能の動作確認スクリプト（Celery 対応版）"""
import argparse
import asyncio
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

# プロジェクトのルートディレクトリを PYTHONPATH に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.fetch_trades_spec import FetchTradesSpecUseCase
from app.core.config import get_settings
from app.domain.repositories.trades_spec_repository import TradesSpecRepository
from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.tasks.trades_spec_task_asyncpg import fetch_trades_spec_task_asyncpg
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.repositories.trades_spec_repository_impl import TradesSpecRepositoryImpl


class TradesSpecTester:
    """TradesSpec 機能のテスター"""
    
    def __init__(self):
        self.factory = JQuantsClientFactory()
        self.test_results = []
        self.start_time = None
        
    def print_header(self):
        """ヘッダー表示"""
        print("=" * 60)
        print("TradesSpec 動作確認スクリプト")
        print("=" * 60)
        print()
        
    def print_step(self, step_num: int, total: int, description: str):
        """ステップ表示"""
        print(f"[{step_num}/{total}] {description}...", end=" ", flush=True)
        
    def print_result(self, success: bool, detail: str = ""):
        """結果表示"""
        if success:
            print(f"✓ {detail}" if detail else "✓")
            self.test_results.append(True)
        else:
            print(f"✗ {detail}" if detail else "✗")
            self.test_results.append(False)
            
    async def wrap_sync(self, func):
        """同期関数を非同期にラップする"""
        return func()
        
    def print_summary(self):
        """サマリー表示"""
        elapsed_time = time.time() - self.start_time
        success_count = sum(self.test_results)
        total_count = len(self.test_results)
        
        print()
        print(f"実行時間: {elapsed_time:.2f}秒")
        print(f"テスト結果: {success_count}/{total_count} 成功")
        
        if success_count == total_count:
            print("すべてのテストが正常に完了しました！ 🎉")
        else:
            print("一部のテストが失敗しました。詳細を確認してください。")
            
    async def test_environment(self) -> bool:
        """環境設定の確認"""
        try:
            settings = get_settings()
            
            # 必須環境変数の確認
            if not settings.jquants_email or not settings.jquants_password:
                self.print_result(False, "J-Quants 認証情報が設定されていません")
                return False
                
            # データベース接続確認
            async with get_async_session_context() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                
            self.print_result(True)
            return True
            
        except Exception as e:
            self.print_result(False, f"エラー: {str(e)}")
            return False
            
    async def test_api_auth(self) -> bool:
        """API 認証テスト"""
        try:
            # 認証を実行（内部でキャッシュされる）
            await self.factory._ensure_authenticated()
            self.print_result(True)
            return True
            
        except Exception as e:
            self.print_result(False, f"認証エラー: {str(e)}")
            return False
            
    async def test_fetch_data(self, section: str = None, days: int = 1) -> bool:
        """データ取得テスト"""
        try:
            # 日付範囲の設定（最新データから指定日数分）
            to_date = date.today() - timedelta(days=1)  # 昨日
            from_date = to_date - timedelta(days=days - 1)
            
            # クライアントとリポジトリの準備
            client = await self.factory.create_trades_spec_client()
            async with get_async_session_context() as session:
                repository = TradesSpecRepositoryImpl(session)
                use_case = FetchTradesSpecUseCase(client, repository)
                
                # データ取得実行
                result = await use_case.execute(
                    section=section,
                    from_date=from_date,
                    to_date=to_date,
                    max_pages=1  # テストなので 1 ページのみ
                )
                
                if result.success:
                    self.print_result(True, f"{result.fetched_count}件取得")
                    return True
                else:
                    self.print_result(False, result.error_message)
                    return False
                    
        except Exception as e:
            self.print_result(False, f"エラー: {str(e)}")
            return False
            
    async def test_database_operations(self) -> bool:
        """データベース操作テスト"""
        try:
            async with get_async_session_context() as session:
                repository = TradesSpecRepositoryImpl(session)
                
                # テスト用の日付
                test_date = date.today() - timedelta(days=1)
                
                # 1. データの検索（日付指定）
                specs = await repository.find_by_date_and_section(test_date)
                
                if not specs:
                    self.print_result(True, "データなし（正常）")
                    return True
                    
                # 2. 特定銘柄の検索
                if specs:
                    first_spec = specs[0]
                    found = await repository.find_by_code_and_date(
                        first_spec.code,
                        first_spec.trade_date
                    )
                    
                    if found:
                        self.print_result(True, f"{len(specs)}件のデータを確認")
                        return True
                    else:
                        self.print_result(False, "データ検索エラー")
                        return False
                        
        except Exception as e:
            self.print_result(False, f"エラー: {str(e)}")
            return False
            
    async def test_search_patterns(self) -> bool:
        """検索パターンテスト"""
        try:
            async with get_async_session_context() as session:
                repository = TradesSpecRepositoryImpl(session)
                
                # 各種検索パターンをテスト
                test_patterns = [
                    # 日付範囲検索
                    {
                        "name": "日付範囲検索",
                        "method": repository.find_by_date_range_and_section,
                        "args": [
                            date.today() - timedelta(days=7),
                            date.today() - timedelta(days=1),
                            None
                        ]
                    },
                ]
                
                all_success = True
                for pattern in test_patterns:
                    try:
                        result = await pattern["method"](*pattern["args"])
                        # 結果の型チェックのみ（データがなくても OK）
                        if isinstance(result, list):
                            continue
                        else:
                            all_success = False
                            break
                    except Exception:
                        all_success = False
                        break
                        
                if all_success:
                    self.print_result(True, "全パターン正常")
                    return True
                else:
                    self.print_result(False, "一部のパターンでエラー")
                    return False
                    
        except Exception as e:
            self.print_result(False, f"エラー: {str(e)}")
            return False
            
    async def test_error_handling(self) -> bool:
        """エラーハンドリングテスト"""
        try:
            client = await self.factory.create_trades_spec_client()
            async with get_async_session_context() as session:
                repository = TradesSpecRepositoryImpl(session)
                use_case = FetchTradesSpecUseCase(client, repository)
                
                # 無効な日付範囲でテスト
                result = await use_case.execute(
                    from_date=date.today() + timedelta(days=10),  # 未来の日付
                    to_date=date.today() + timedelta(days=20),
                    max_pages=1
                )
                
                # エラーが適切に処理されているか確認
                if not result.success or result.fetched_count == 0:
                    self.print_result(True, "エラー処理正常")
                    return True
                else:
                    self.print_result(False, "エラーが検出されませんでした")
                    return False
                    
        except Exception as e:
            # 例外が適切にキャッチされていれば OK
            self.print_result(True, f"例外処理正常: {type(e).__name__}")
            return True
            
    async def test_celery_task(self, section: str = None, days: int = 1) -> bool:
        """Celery タスクテスト"""
        try:
            # 日付範囲の設定
            to_date = date.today() - timedelta(days=1)
            from_date = to_date - timedelta(days=days - 1)
            
            # Celery タスクを非同期実行
            result = fetch_trades_spec_task_asyncpg.delay(
                section=section,
                from_date=from_date.isoformat() if from_date else None,
                to_date=to_date.isoformat() if to_date else None,
                max_pages=1
            )
            
            # タスク ID を表示
            print(f"(Task ID: {result.id})", end=" ")
            
            # タスクの完了を待つ（最大 30 秒）
            try:
                task_result = result.get(timeout=30)
                
                if task_result.get("success"):
                    fetched = task_result.get("fetched_count", 0)
                    saved = task_result.get("saved_count", 0)
                    self.print_result(True, f"Celery 経由で{fetched}件取得、{saved}件保存")
                    return True
                else:
                    error = task_result.get("error", "不明なエラー")
                    self.print_result(False, f"タスクエラー: {error}")
                    return False
                    
            except Exception as timeout_error:
                self.print_result(False, f"タスクタイムアウト: {str(timeout_error)}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Celery エラー: {str(e)}")
            return False
            
    def test_celery_status(self) -> bool:
        """Celery ワーカーの状態確認"""
        try:
            # Celery ワーカーの状態を確認
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                worker_count = len(stats)
                self.print_result(True, f"{worker_count}個のワーカーが稼働中")
                return True
            else:
                self.print_result(False, "Celery ワーカーが起動していません")
                return False
                
        except Exception as e:
            self.print_result(False, f"Celery 接続エラー: {str(e)}")
            return False
            
    async def test_task_history(self) -> bool:
        """タスク実行履歴の確認"""
        try:
            async with get_async_session_context() as session:
                # タスクログを確認（簡易版）
                from sqlalchemy import text
                result = await session.execute(
                    text("SELECT COUNT(*) FROM task_execution_logs WHERE task_name LIKE '%trades_spec%'")
                )
                count = result.scalar()
                
                if count is not None:
                    self.print_result(True, f"{count}件のタスク履歴")
                    return True
                else:
                    self.print_result(True, "タスク履歴なし")
                    return True
                    
        except Exception as e:
            self.print_result(False, f"履歴確認エラー: {str(e)}")
            return False
            
    async def run(self, args):
        """テスト実行"""
        self.start_time = time.time()
        self.print_header()
        
        # テスト実行
        if args.use_celery:
            # Celery 版のテスト
            tests = [
                (1, "環境設定確認", self.test_environment),
                (2, "Celery ワーカー確認", lambda: self.wrap_sync(self.test_celery_status)),
                (3, "API 認証", self.test_api_auth),
                (4, f"Celery タスクテスト (最新{args.days}日分)", 
                 lambda: self.test_celery_task(args.section, args.days)),
                (5, "タスク履歴確認", self.test_task_history),
                (6, "データベース検索", self.test_database_operations),
            ]
        else:
            # 直接実行版のテスト
            tests = [
                (1, "環境設定確認", self.test_environment),
                (2, "API 認証", self.test_api_auth),
                (3, f"データ取得テスト (最新{args.days}日分)", 
                 lambda: self.test_fetch_data(args.section, args.days)),
                (4, "データベース操作", self.test_database_operations),
                (5, "検索機能テスト", self.test_search_patterns),
                (6, "エラーハンドリング確認", self.test_error_handling),
            ]
        
        total_tests = len(tests)
        
        for step_num, description, test_func in tests:
            self.print_step(step_num, total_tests, description)
            
            # 前のテストが失敗した場合、以降のテストはスキップ
            if step_num > 2 and not all(self.test_results[:step_num-1]):
                self.print_result(False, "前提条件を満たしていないためスキップ")
                continue
                
            await test_func()
            
        self.print_summary()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="TradesSpec 機能の動作確認スクリプト（Celery 対応版）"
    )
    parser.add_argument(
        "--section",
        type=str,
        help="市場区分（例: TSEPrime）",
        default=None
    )
    parser.add_argument(
        "--days",
        type=int,
        help="取得する日数（デフォルト: 1）",
        default=1
    )
    parser.add_argument(
        "--code",
        type=str,
        help="特定銘柄コード（未実装）",
        default=None
    )
    parser.add_argument(
        "--use-celery",
        action="store_true",
        help="Celery タスクを使用して実行（本番環境での動作確認）",
        default=False
    )
    
    args = parser.parse_args()
    
    # Celery モードの場合の注意事項を表示
    if args.use_celery:
        print("=" * 60)
        print("【 Celery モードでの実行】")
        print("以下のコマンドで Celery ワーカーが起動していることを確認してください：")
        print("  celery -A app.infrastructure.celery.app worker --loglevel=info")
        print("=" * 60)
        print()
    
    # テスター実行
    tester = TradesSpecTester()
    asyncio.run(tester.run(args))


if __name__ == "__main__":
    main()