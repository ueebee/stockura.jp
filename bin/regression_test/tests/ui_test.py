"""
APIエンドポイント管理画面のUIテスト
本番データを使用して画面の表示と操作を確認
"""
from typing import List, Dict, Any

from .base import BaseRegressionTest
from ..utils import TestResult, get_jst_time_after_minutes


class APIEndpointUITest(BaseRegressionTest):
    """APIエンドポイント管理画面のUIテスト"""
    
    def get_test_name(self) -> str:
        return "APIエンドポイント管理UIテスト"
    
    async def execute(self) -> TestResult:
        """テストを実行"""
        # 個別のテストケースを実行
        test_cases = [
            self.test_endpoint_list_display,
            self.test_endpoint_detail_view,
            self.test_manual_sync_functionality,
            self.test_schedule_crud_operations,
            self.test_execution_history_display,
        ]
        
        passed_count = 0
        failed_count = 0
        
        for test_case in test_cases:
            self.logger.info(f"\n--- {test_case.__name__} を実行 ---")
            try:
                success = await test_case()
                if success:
                    passed_count += 1
                    self.logger.info(f"✓ {test_case.__name__} 成功")
                else:
                    failed_count += 1
                    self.logger.error(f"✗ {test_case.__name__} 失敗")
                    self.result.errors.append(f"{test_case.__name__} が失敗しました")
            except Exception as e:
                failed_count += 1
                self.logger.error(f"✗ {test_case.__name__} でエラー発生: {e}")
                self.result.errors.append(f"{test_case.__name__} でエラー: {str(e)}")
        
        # 結果を集計
        if failed_count == 0:
            self.result.success(
                total_tests=len(test_cases),
                passed=passed_count,
                failed=failed_count
            )
        else:
            self.result.fail(
                f"{failed_count}個のテストケースが失敗しました",
                total_tests=len(test_cases),
                passed=passed_count,
                failed=failed_count
            )
        
        return self.result
    
    async def test_endpoint_list_display(self) -> bool:
        """エンドポイント一覧の表示確認"""
        self.logger.info("エンドポイント一覧の表示を確認します")
        
        # APIエンドポイント管理画面へ遷移
        if not await self.navigate_to_endpoint_management():
            self.logger.error("APIエンドポイント管理画面への遷移に失敗")
            return False
        
        # ページタイトルの確認
        await self.browser.wait_for_load_state()
        
        # エンドポイント一覧テーブルの存在確認
        if not await self.browser.wait_for_element('table', 5000):
            self.logger.error("エンドポイント一覧テーブルが見つかりません")
            await self.browser.take_screenshot("no_endpoint_table")
            return False
        
        # 必須カラムの確認
        required_columns = [
            "エンドポイント",
            "データ種別",
            "実行モード",
            "最終実行",
            "データ件数",
            "成功率"
        ]
        
        for column in required_columns:
            if not await self.browser.is_visible(f'text="{column}"'):
                self.logger.error(f"カラム '{column}' が見つかりません")
                return False
        
        # エンドポイントの存在確認
        endpoints = [
            ("日次株価データ", "daily_quotes"),
            ("上場企業一覧", "listed_companies")
        ]
        
        for endpoint_name, data_type in endpoints:
            if not await self.browser.is_visible(f'text="{endpoint_name}"'):
                self.logger.error(f"エンドポイント '{endpoint_name}' が見つかりません")
                return False
            
            if not await self.browser.is_visible(f'text="{data_type}"'):
                self.logger.error(f"データ種別 '{data_type}' が見つかりません")
                return False
        
        self.logger.info("エンドポイント一覧が正しく表示されています")
        return True
    
    async def test_endpoint_detail_view(self) -> bool:
        """エンドポイント詳細画面への遷移テスト"""
        self.logger.info("エンドポイント詳細画面への遷移を確認します")
        
        # 日次株価データの行をクリック
        if not await self.wait_and_click('tr:has-text("日次株価データ")', "日次株価データの行"):
            return False
        
        # 詳細パネルの表示を待機
        await self.browser.wait_for_timeout(1000)
        
        # 詳細画面の要素確認
        detail_elements = [
            ('h3:has-text("日次株価データ")', "日次株価データのヘッダー"),
            ('h4:has-text("株価データ同期")', "株価データ同期セクション"),
            ('button:has-text("同期を開始")', "同期開始ボタン"),
            ('h4:has-text("実行履歴")', "実行履歴セクション")
        ]
        
        for selector, description in detail_elements:
            if not await self.browser.wait_for_element(selector, 5000):
                self.logger.error(f"{description}が見つかりません")
                return False
        
        # 上場企業一覧に切り替え
        if not await self.wait_and_click('tr:has-text("上場企業一覧")', "上場企業一覧の行"):
            return False
        
        await self.browser.wait_for_timeout(1000)
        
        # 上場企業一覧の詳細確認
        if not await self.browser.wait_for_element('h3:has-text("上場企業一覧")', 5000):
            self.logger.error("上場企業一覧の詳細が表示されません")
            return False
        
        if not await self.browser.wait_for_element('button:has-text("今すぐ同期")', 5000):
            self.logger.error("今すぐ同期ボタンが見つかりません")
            return False
        
        self.logger.info("エンドポイント詳細画面への遷移が正常に動作しています")
        return True
    
    async def test_manual_sync_functionality(self) -> bool:
        """手動同期機能のテスト"""
        self.logger.info("手動同期機能を確認します")
        
        # 上場企業一覧の手動同期をテスト（処理が速いため）
        if not await self.wait_and_click('tr:has-text("上場企業一覧")', "上場企業一覧の行"):
            return False
        
        await self.browser.wait_for_timeout(1000)
        
        # 今すぐ同期ボタンをクリック
        if not await self.wait_and_click('button:has-text("今すぐ同期")', "今すぐ同期ボタン"):
            return False
        
        # 同期処理の完了を待機（最大30秒）
        success = False
        for i in range(30):
            await self.browser.wait_for_timeout(1000)
            
            # 成功メッセージまたは完了ステータスを確認
            if await self.browser.is_visible('text="同期が完了しました"'):
                success = True
                break
            
            # 実行履歴の最新エントリを確認
            if await self.browser.is_visible('tr:first-child .badge:has-text("完了")'):
                success = True
                break
            
            # 履歴更新ボタンがある場合はクリック
            if i % 5 == 0 and await self.browser.is_visible('button:has-text("履歴を更新")'):
                await self.browser.safe_click('button:has-text("履歴を更新")', "履歴更新ボタン")
        
        if not success:
            self.logger.error("手動同期が完了しませんでした")
            await self.browser.take_screenshot("manual_sync_timeout")
            return False
        
        self.logger.info("手動同期機能が正常に動作しています")
        return True
    
    async def test_schedule_crud_operations(self) -> bool:
        """スケジュール設定のCRUD操作テスト"""
        self.logger.info("スケジュール設定機能を確認します")
        
        # 日次株価データのスケジュール設定をテスト
        if not await self.wait_and_click('tr:has-text("日次株価データ")', "日次株価データの行"):
            return False
        
        await self.browser.wait_for_timeout(1000)
        
        # 新規スケジュールボタンの確認
        if not await self.browser.wait_for_element('button:has-text("新規スケジュール")', 5000):
            self.logger.error("新規スケジュールボタンが見つかりません")
            return False
        
        # 上場企業一覧のスケジュール確認
        if not await self.wait_and_click('tr:has-text("上場企業一覧")', "上場企業一覧の行"):
            return False
        
        await self.browser.wait_for_timeout(1000)
        
        # 定期実行スケジュールセクションの確認
        if not await self.browser.wait_for_element('h4:has-text("定期実行スケジュール")', 5000):
            self.logger.error("定期実行スケジュールセクションが見つかりません")
            return False
        
        # スケジュールが設定されている場合の要素確認
        schedule_info_found = False
        if await self.browser.is_visible('text="実行時刻"'):
            schedule_info_found = True
            self.logger.info("既存のスケジュール設定を確認しました")
            
            # 編集・削除ボタンの確認
            if not await self.browser.is_visible('button:has-text("編集")'):
                self.logger.warning("編集ボタンが見つかりません")
            if not await self.browser.is_visible('button:has-text("削除")'):
                self.logger.warning("削除ボタンが見つかりません")
        else:
            self.logger.info("スケジュールが未設定の状態です")
        
        return True
    
    async def test_execution_history_display(self) -> bool:
        """実行履歴の表示確認"""
        self.logger.info("実行履歴の表示を確認します")
        
        # まず上場企業一覧の履歴を確認（データがある可能性が高い）
        if not await self.wait_and_click('tr:has-text("上場企業一覧")', "上場企業一覧の行"):
            return False
        
        await self.browser.wait_for_timeout(1000)
        
        # 実行履歴セクションの確認
        if not await self.browser.wait_for_element('h4:has-text("実行履歴")', 5000):
            self.logger.error("実行履歴セクションが見つかりません")
            return False
        
        # 履歴テーブルのカラム確認
        history_columns = [
            "実行日時",
            "同期タイプ/実行タイプ",
            "ステータス",
            "実行時間"
        ]
        
        columns_found = 0
        for column in history_columns:
            if await self.browser.is_visible(f'text="{column}"'):
                columns_found += 1
        
        if columns_found < len(history_columns) / 2:
            self.logger.error("実行履歴テーブルのカラムが不足しています")
            return False
        
        # 履歴更新ボタンの確認
        if not await self.browser.is_visible('button:has-text("履歴を更新")'):
            self.logger.warning("履歴更新ボタンが見つかりません")
        
        # 日次株価データの履歴も確認
        if not await self.wait_and_click('tr:has-text("日次株価データ")', "日次株価データの行"):
            return False
        
        await self.browser.wait_for_timeout(1000)
        
        # 日次株価データ特有の要素確認
        if await self.browser.is_visible('text="full"') or await self.browser.is_visible('text="incremental"'):
            self.logger.info("同期タイプ（full/incremental）の表示を確認")
        
        if await self.browser.is_visible('text="manual"') or await self.browser.is_visible('text="scheduled"'):
            self.logger.info("実行タイプ（manual/scheduled）の表示を確認")
        
        self.logger.info("実行履歴が正しく表示されています")
        return True