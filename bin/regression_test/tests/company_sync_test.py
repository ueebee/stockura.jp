"""
上場企業一覧の同期テスト
既存のtest_company_syncを移植・リファクタリング
"""
from .base import BaseRegressionTest
from ..utils import TestResult


class CompanySyncTest(BaseRegressionTest):
    """上場企業一覧の同期テスト"""
    
    def get_test_name(self) -> str:
        return "上場企業一覧同期テスト"
    
    async def execute(self) -> TestResult:
        """テストを実行"""
        # APIエンドポイント管理画面へ遷移
        if not await self.navigate_to_endpoint_management():
            self.result.fail("APIエンドポイント管理画面への遷移に失敗")
            return self.result
        
        # 上場企業一覧の行をクリック
        if not await self.wait_and_click('tr:has-text("上場企業一覧")', "上場企業一覧の行", 10000):
            self.result.fail("上場企業一覧の行が見つかりません")
            await self.browser.take_screenshot("company_row_not_found")
            return self.result
        
        await self.browser.wait_for_load_state()
        await self.browser.wait_for_timeout(1000)
        
        # 手動同期テスト
        manual_sync_result = await self._test_manual_sync()
        if not manual_sync_result:
            self.result.fail("手動同期テストが失敗しました")
            return self.result
        
        self.result.success(
            manual_sync=True,
            sync_type="full",
            execution_type="manual"
        )
        
        return self.result
    
    async def _test_manual_sync(self) -> bool:
        """手動同期をテスト"""
        self.logger.info("上場企業一覧の手動同期を実行します...")
        
        # 今すぐ同期ボタンをクリック
        if not await self.wait_and_click('button:has-text("今すぐ同期")', "今すぐ同期ボタン", 10000):
            self.logger.error("今すぐ同期ボタンのクリックに失敗")
            return False
        
        # 同期が完了するまで待機（最大30秒）
        self.logger.info("同期の完了を待機しています...")
        
        for i in range(30):
            await self.browser.wait_for_timeout(1000)
            
            # 成功メッセージが表示されているか確認
            if await self.browser.is_visible('text="同期が完了しました"'):
                self.logger.info("同期完了メッセージを確認")
                return True
            
            # 履歴を更新して最新状態を確認
            if i % 3 == 0:
                update_button_visible = await self.browser.is_visible('button:has-text("履歴を更新")')
                if update_button_visible:
                    await self.browser.safe_click('button:has-text("履歴を更新")', "履歴更新ボタン")
                    await self.browser.wait_for_timeout(500)
                    
                    # 最新の履歴で完了ステータスを確認
                    if await self.browser.is_visible('tr:first-child:has-text("完了")'):
                        self.logger.info("実行履歴で完了ステータスを確認")
                        
                        # データ件数の確認
                        company_count = await self.browser.get_text('tr:first-child td:nth-child(5)')
                        if company_count and company_count.isdigit():
                            self.logger.info(f"同期された企業数: {company_count}社")
                        
                        return True
        
        self.logger.error("手動同期がタイムアウトしました")
        await self.browser.take_screenshot("company_sync_timeout")
        return False