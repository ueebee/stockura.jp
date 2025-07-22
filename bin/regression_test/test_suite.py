"""
テストスイート管理モジュール
テストの実行を統括する
"""
import asyncio
from typing import List, Type, Optional

from .config import TestConfig
from .browser import BrowserController
from .database import DatabaseManager
from .reporter import TestReporter
from .utils import setup_logger
from .tests.base import BaseRegressionTest

# テストクラスのインポート
from .tests.ui_test import APIEndpointUITest
from .tests.company_sync_test import CompanySyncTest
from .tests.daily_quotes_test import DailyQuotesTest
from .tests.schedule_crud_test import ScheduleCRUDTest
from .tests.quick_integration_test import QuickIntegrationTest


class TestSuite:
    """テストスイートクラス"""
    
    # デフォルトのテストクラスリスト（高速テストを優先）
    DEFAULT_TESTS = [
        QuickIntegrationTest,  # 高速統合テストをデフォルトに
    ]
    
    # 詳細なテストクラスリスト
    FULL_TESTS = [
        APIEndpointUITest,
        CompanySyncTest,
        DailyQuotesTest,
        ScheduleCRUDTest,
    ]
    
    def __init__(self, config: TestConfig):
        """
        Args:
            config: テスト設定
        """
        self.config = config
        self.logger = setup_logger(self.__class__.__name__, config.log_level, config.log_file)
        self.browser = BrowserController(config)
        self.database = DatabaseManager(config)
        self.reporter = TestReporter(config)
        
    async def run(self, test_classes: Optional[List[Type[BaseRegressionTest]]] = None) -> bool:
        """テストスイートを実行
        
        Args:
            test_classes: 実行するテストクラスのリスト（Noneの場合はデフォルト）
            
        Returns:
            全てのテストが成功した場合True
        """
        if test_classes is None:
            test_classes = self.DEFAULT_TESTS
        
        self.logger.info("リグレッションテストスイートを開始します")
        
        # データベースリセット（設定により実行）
        if not self.config.skip_db_reset:
            if not self.database.reset_database():
                self.logger.error("データベースのリセットに失敗しました")
                return False
        else:
            self.logger.info("データベースリセットをスキップします")
            
            # Docker環境が実行中か確認
            if not self.database.is_running():
                self.logger.error("Docker環境が実行されていません")
                self.logger.info("docker compose up -d を実行してください")
                return False
        
        # ブラウザのセットアップ
        if not await self.browser.setup():
            self.logger.error("ブラウザのセットアップに失敗しました")
            return False
        
        try:
            # 各テストを実行
            for test_class in test_classes:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"テストクラス: {test_class.__name__}")
                self.logger.info(f"{'='*60}")
                
                # テストインスタンスを作成
                test = test_class(self.browser, self.config)
                
                # テストを実行
                result = await test.run()
                
                # 結果をレポーターに追加
                self.reporter.add_result(result)
                
                # 失敗時の処理
                if result.status == "FAILED" and not self.config.parallel_execution:
                    self.logger.warning("テストが失敗しました。残りのテストを続行します。")
                
                # テスト間の待機
                await asyncio.sleep(1)
            
        finally:
            # ブラウザのクリーンアップ
            await self.browser.cleanup()
        
        # レポートの生成と保存
        self.reporter.finalize()
        report_path = self.reporter.save_report()
        self.logger.info(f"レポートを保存しました: {report_path}")
        
        # コンソールサマリーの出力
        self.reporter.print_console_summary()
        
        # 全体の成功/失敗を判定
        failed_count = sum(1 for r in self.reporter.results if r.status == "FAILED")
        return failed_count == 0
    
    def print_manual_test_instructions(self):
        """手動テストの手順を表示"""
        from ..utils import get_jst_time_after_minutes
        
        schedule_time = get_jst_time_after_minutes(2)
        
        print("\n" + "="*60)
        print("手動テスト手順")
        print("="*60)
        print(f"\nベースURL: {self.config.base_url}")
        print(f"2分後のJST時刻（スケジュール設定用）: {schedule_time}\n")
        
        print("【1. 上場企業一覧のテスト】")
        print("-" * 40)
        print("1-1. 手動同期テスト:")
        print("  a) データソース管理画面にアクセス: {}/data-sources".format(self.config.base_url))
        print("  b) J-Quantsデータソースをクリック")
        print("  c) 「APIエンドポイント管理」をクリック")
        print("  d) 上場企業一覧の行をクリック")
        print("  e) 「今すぐ同期」ボタンをクリック")
        print("  f) 実行履歴にステータス「完了」が表示されることを確認")
        print()
        print("1-2. 定期実行スケジュールテスト:")
        print("  a) 実行時刻に「{}」を入力".format(schedule_time))
        print("  b) 「スケジュール保存」ボタンをクリック")
        print("  c) 約2分待機")
        print("  d) 「履歴を更新」ボタンをクリック")
        print("  e) 実行履歴に実行タイプ「Scheduled」、ステータス「完了」が表示されることを確認")
        print()
        
        print("【2. 日次株価データのテスト】")
        print("-" * 40)
        print("2-1. 手動同期テスト:")
        print("  a) 日次株価データの行をクリック")
        print("  b) 「過去7日間」ボタンをクリック")
        print("  c) 「同期を開始」ボタンをクリック")
        print("  d) 実行履歴に同期タイプ「Full」、実行タイプ「Manual」、ステータス「完了」が表示されることを確認")
        print()
        print("2-2. 定期実行スケジュールテスト:")
        print("  a) 「新規スケジュール」ボタンをクリック")
        print("  b) 実行時刻に「{}」を入力".format(schedule_time))
        print("  c) 実行頻度で「毎日」を選択")
        print("  d) 取得期間で「実行日から過去7日間」を選択")
        print("  e) 「保存」ボタンをクリック")
        print("  f) 約2分待機")
        print("  g) 「履歴を更新」ボタンをクリック")
        print("  h) 実行履歴に同期タイプ「Full」、実行タイプ「Scheduled」、ステータス「完了」が表示されることを確認")
        print()
        print("="*60)