"""
定期実行スケジュールのCRUD操作テスト
既存のtest_schedule_crudを移植・リファクタリング
"""
from .base import BaseRegressionTest
from ..utils import TestResult, get_jst_time_after_minutes


class ScheduleCRUDTest(BaseRegressionTest):
    """定期実行スケジュールのCRUD操作テスト"""
    
    def get_test_name(self) -> str:
        return "定期実行スケジュール設定テスト"
    
    async def execute(self) -> TestResult:
        """テストを実行"""
        # スケジュール実行時間を2分後に設定
        schedule_time = get_jst_time_after_minutes(2)
        self.logger.info(f"スケジュール実行時刻: {schedule_time}")
        
        # APIエンドポイント管理画面へ遷移
        if not await self.navigate_to_endpoint_management():
            self.result.fail("APIエンドポイント管理画面への遷移に失敗")
            return self.result
        
        # 日次株価データのスケジュール設定
        daily_schedule_result = await self._test_daily_quotes_schedule(schedule_time)
        
        # 上場企業一覧のスケジュール設定
        company_schedule_result = await self._test_company_schedule(schedule_time)
        
        # 結果の集計
        if daily_schedule_result and company_schedule_result:
            self.result.success(
                daily_schedule_created=True,
                company_schedule_created=True,
                schedule_time=schedule_time
            )
        else:
            errors = []
            if not daily_schedule_result:
                errors.append("日次株価データのスケジュール作成に失敗")
            if not company_schedule_result:
                errors.append("上場企業一覧のスケジュール作成に失敗")
            
            self.result.fail(
                "スケジュール設定に失敗しました",
                daily_schedule_created=daily_schedule_result,
                company_schedule_created=company_schedule_result,
                errors=errors
            )
        
        return self.result
    
    async def _test_daily_quotes_schedule(self, schedule_time: str) -> bool:
        """日次株価データのスケジュール設定をテスト"""
        self.logger.info("日次株価データのスケジュール設定を開始します...")
        
        # 日次株価データの行をクリック
        if not await self.wait_and_click('tr:has-text("日次株価データ")', "日次株価データの行"):
            return False
        
        # 詳細パネルの表示を待つ
        if not await self.browser.wait_for_element('button:has-text("新規スケジュール")', 5000):
            self.logger.error("新規スケジュールボタンが見つかりません")
            return False
        
        # 新規スケジュールボタンをクリック
        await self.browser.safe_click('button:has-text("新規スケジュール")', "新規スケジュールボタン")
        
        # モーダルの表示を待つ
        await self.browser.wait_for_timeout(1000)
        
        # スケジュール名を入力
        name_input = 'input[placeholder="例: 日次更新（過去7日間）"]'
        if await self.browser.is_visible(name_input):
            await self.browser.safe_fill(name_input, "日次株価データ自動取得", "スケジュール名")
        
        # 実行時刻を設定
        time_input_filled = False
        
        # ラベル経由で試す
        try:
            await self.browser.page.get_by_label('実行時刻（JST）').fill(schedule_time)
            time_input_filled = True
            self.logger.info("ラベル経由で時刻を入力しました")
        except:
            pass
        
        # time入力フィールドを直接探す
        if not time_input_filled:
            time_inputs = await self.browser.page.query_selector_all('input[type="time"]')
            if time_inputs:
                await time_inputs[-1].fill(schedule_time)
                time_input_filled = True
                self.logger.info("time入力フィールドに直接入力しました")
        
        if not time_input_filled:
            self.logger.error("時刻入力フィールドが見つかりません")
            return False
        
        # 保存ボタンをクリック
        save_success = False
        
        # 通常のセレクタで試す
        save_button = await self.browser.page.query_selector('button:has-text("保存"):not(:has-text("新規"))')
        if save_button:
            await save_button.click()
            save_success = True
        else:
            # モーダル内の保存ボタンを探す
            if await self.browser.safe_click('.fixed button:has-text("保存")', "モーダル内の保存ボタン"):
                save_success = True
        
        if not save_success:
            self.logger.error("保存ボタンのクリックに失敗")
            return False
        
        # モーダルが閉じるのを待つ
        await self.browser.wait_for_timeout(2000)
        
        # スケジュール一覧に表示されているか確認
        if await self.browser.is_visible('td:has-text("日次株価データ自動取得")'):
            self.logger.info("日次株価データのスケジュール作成に成功しました")
            return True
        
        # エラーメッセージの確認
        error_element = await self.browser.page.query_selector('.text-red-600')
        if error_element:
            error_text = await error_element.text_content()
            self.logger.error(f"エラーメッセージ: {error_text}")
        
        return False
    
    async def _test_company_schedule(self, schedule_time: str) -> bool:
        """上場企業一覧のスケジュール設定をテスト"""
        self.logger.info("上場企業一覧のスケジュール設定を開始します...")
        
        # エンドポイント一覧に戻る
        await self.navigate_to_endpoint_management()
        
        # 上場企業一覧の行をクリック
        if not await self.wait_and_click('tr:has-text("上場企業一覧")', "上場企業一覧の行", 5000):
            return False
        
        # 詳細パネルの表示を待つ
        await self.browser.wait_for_timeout(1000)
        
        # 既にスケジュールが設定されている場合は編集
        if await self.browser.is_visible('button:has-text("編集")'):
            self.logger.info("既存のスケジュールを編集します")
            await self.browser.safe_click('button:has-text("編集")', "編集ボタン")
        else:
            # 新規スケジュールボタンを探す
            if await self.browser.is_visible('button:has-text("新規スケジュール")'):
                await self.browser.safe_click('button:has-text("新規スケジュール")', "新規スケジュールボタン")
            else:
                self.logger.error("スケジュール設定ボタンが見つかりません")
                return False
        
        # モーダルの表示を待つ
        await self.browser.wait_for_timeout(1000)
        
        # 実行時刻を設定
        time_input_filled = False
        
        # ラベル経由で試す
        try:
            await self.browser.page.get_by_label('実行時刻（JST）').fill(schedule_time)
            time_input_filled = True
            self.logger.info("ラベル経由で時刻を入力しました")
        except:
            pass
        
        # time入力フィールドを直接探す
        if not time_input_filled:
            time_inputs = await self.browser.page.query_selector_all('input[type="time"]')
            if time_inputs:
                await time_inputs[-1].fill(schedule_time)
                time_input_filled = True
                self.logger.info("time入力フィールドに直接入力しました")
        
        if not time_input_filled:
            self.logger.error("時刻入力フィールドが見つかりません")
            return False
        
        # 保存ボタンをクリック
        save_success = False
        
        # 通常のセレクタで試す
        save_button = await self.browser.page.query_selector('button:has-text("保存"):not(:has-text("新規"))')
        if save_button:
            await save_button.click()
            save_success = True
        else:
            # モーダル内の保存ボタンを探す
            if await self.browser.safe_click('.fixed button:has-text("保存")', "モーダル内の保存ボタン"):
                save_success = True
        
        if not save_success:
            self.logger.error("保存ボタンのクリックに失敗")
            return False
        
        # モーダルが閉じるのを待つ
        await self.browser.wait_for_timeout(2000)
        
        # エンドポイント一覧に戻って確認
        await self.navigate_to_endpoint_management()
        await self.browser.wait_for_element('tr:has-text("上場企業一覧")', 5000)
        
        # 実行モードが「定期実行」に変わっているか確認
        company_row = await self.browser.page.query_selector('tr:has-text("上場企業一覧")')
        if company_row:
            row_text = await company_row.text_content()
            if "定期実行" in row_text:
                self.logger.info("上場企業一覧のスケジュール作成に成功しました（実行モードが定期実行に変更）")
                return True
            
            # 詳細画面でも確認
            await self.browser.safe_click('tr:has-text("上場企業一覧")', "上場企業一覧の行")
            await self.browser.wait_for_timeout(1000)
            
            # スケジュール時刻が表示されているか確認
            if await self.browser.is_visible(f'text="{schedule_time}"'):
                self.logger.info("上場企業一覧のスケジュール作成に成功しました（詳細画面で確認）")
                return True
        
        self.logger.error("上場企業一覧のスケジュール作成に失敗しました")
        return False