"""
日次株価データの同期テスト
既存のtest_daily_quotes_syncを移植・リファクタリング
"""
from .base import BaseRegressionTest
from ..utils import TestResult


class DailyQuotesTest(BaseRegressionTest):
    """日次株価データの同期テスト"""
    
    def get_test_name(self) -> str:
        return "日次株価データ同期テスト"
    
    async def execute(self) -> TestResult:
        """テストを実行"""
        # APIエンドポイント管理画面へ遷移
        if not await self.navigate_to_endpoint_management():
            self.result.fail("APIエンドポイント管理画面への遷移に失敗")
            return self.result
        
        # 日次株価データの行をクリック
        if not await self.wait_and_click('tr:has-text("日次株価データ")', "日次株価データの行", 10000):
            self.result.fail("日次株価データの行が見つかりません")
            await self.browser.take_screenshot("daily_quotes_row_not_found")
            return self.result
        
        await self.browser.wait_for_load_state()
        await self.browser.wait_for_timeout(1000)
        
        # 期間選択のテスト
        date_range_result = await self._test_date_range_selection()
        if not date_range_result:
            self.result.fail("期間選択テストが失敗しました")
            return self.result
        
        # 手動同期テスト
        manual_sync_result = await self._test_manual_sync()
        if not manual_sync_result:
            self.result.fail("手動同期テストが失敗しました")
            return self.result
        
        self.result.success(
            manual_sync=True,
            sync_type="full",
            execution_type="manual",
            date_range="過去7日間"
        )
        
        return self.result
    
    async def _test_date_range_selection(self) -> bool:
        """期間選択機能をテスト"""
        self.logger.info("期間選択機能をテストします...")
        
        # 過去7日間ボタンをクリック
        if not await self.wait_and_click('button:has-text("過去7日間")', "過去7日間ボタン", 5000):
            self.logger.error("過去7日間ボタンが見つかりません")
            return False
        
        await self.browser.wait_for_timeout(500)
        
        # 期間設定の確認
        if await self.browser.is_visible('text="の期間設定"'):
            self.logger.info("期間設定が正しく表示されています")
        
        # 開始日と終了日の入力フィールドを確認
        start_date_visible = await self.browser.is_visible('input[type="date"]:nth-of-type(1)')
        end_date_visible = await self.browser.is_visible('input[type="date"]:nth-of-type(2)')
        
        if not (start_date_visible and end_date_visible):
            self.logger.warning("日付入力フィールドが見つかりません")
            # エラーとはせず、処理を続行
        
        return True
    
    async def _test_manual_sync(self) -> bool:
        """手動同期をテスト"""
        self.logger.info("日次株価データの手動同期を実行します...")
        
        # 同期を開始ボタンをクリック
        if not await self.wait_and_click('button:has-text("同期を開始")', "同期を開始ボタン", 10000):
            self.logger.error("同期を開始ボタンのクリックに失敗")
            return False
        
        # 同期が完了するまで待機（最大60秒）
        self.logger.info("同期の完了を待機しています...")
        
        for i in range(60):
            await self.browser.wait_for_timeout(1000)
            
            # 成功メッセージが表示されているか確認
            if await self.browser.is_visible('text="同期が正常に完了しました"'):
                self.logger.info("同期完了メッセージを確認")
                return True
            
            # 履歴を更新して最新状態を確認
            if i % 5 == 0:
                update_button_visible = await self.browser.is_visible('button:has-text("履歴を更新")')
                if update_button_visible:
                    await self.browser.safe_click('button:has-text("履歴を更新")', "履歴更新ボタン")
                    await self.browser.wait_for_timeout(1000)
                    
                    # 最新の履歴で完了ステータスを確認
                    # fullとmanualの両方を含む行を探す
                    completed_selector = 'tr:first-child:has-text("full"):has-text("manual"):has-text("完了")'
                    if await self.browser.is_visible(completed_selector):
                        self.logger.info("実行履歴で完了ステータスを確認")
                        
                        # 更新されたデータ件数の確認
                        data_count = await self.browser.get_text('tr:first-child td:nth-child(5)')
                        if data_count and data_count.replace(',', '').isdigit():
                            self.logger.info(f"同期されたデータ件数: {data_count}件")
                        
                        return True
            
            self.logger.debug(f"待機中... ({i+1}/60)")
        
        self.logger.error("手動同期がタイムアウトしました")
        await self.browser.take_screenshot("daily_quotes_sync_timeout")
        return False