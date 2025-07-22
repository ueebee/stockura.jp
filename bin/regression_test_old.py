#!/usr/bin/env python3
"""
リグレッションテストスクリプト
DBをクリーンな状態にリセットし、主要機能の動作確認を手動/自動で行う
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Playwrightのインポート（インストールされている場合のみ）
try:
    from playwright.async_api import (Browser, BrowserContext, Page,
                                      async_playwright)
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class RegressionTester:
    def __init__(self):
        self.start_time = datetime.now()
        self.base_url = "http://localhost:8000"
        self.test_results = []
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def log(self, message: str, level: str = "INFO"):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_command(self, command: str, description: str = "") -> bool:
        """コマンドを実行し、成功/失敗を返す"""
        self.log(f"実行: {description or command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                self.log(f"出力: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"エラー: {e.stderr}", "ERROR")
            return False

    def reset_database(self) -> bool:
        """データベースをクリーンな状態にリセット"""
        self.log("="*60)
        self.log("データベースのリセットを開始します")
        self.log("="*60)

        commands = [
            ("docker compose down", "Docker環境を停止"),
            ("docker volume rm stockurajp_postgres_data", "PostgreSQLボリュームを削除"),
            ("docker compose up -d", "Docker環境を起動"),
            ("sleep 10", "サービスの起動を待機"),
            ("docker compose exec -T web alembic upgrade head", "マイグレーションを実行"),
            ("docker compose down", "Docker環境を一旦停止"),
            ("docker compose up -d", "Docker環境を再起動"),
            ("sleep 15", "全サービスの起動を待機")
        ]

        for command, description in commands:
            if not self.run_command(command, description):
                # ボリューム削除でエラーが出る場合は無視（既に削除されている場合）
                if "docker volume rm" in command:
                    self.log("ボリュームが既に削除されています（問題ありません）")
                    continue
                else:
                    return False

        self.log("データベースのリセットが完了しました", "SUCCESS")
        return True

    def get_jst_time_after_minutes(self, minutes: int) -> str:
        """現在時刻から指定分後のJST時刻を HH:MM 形式で返す"""
        # 現在のJST時刻を取得（UTC+9）
        jst_offset = timedelta(hours=9)
        jst_now = datetime.utcnow() + jst_offset
        future_time = jst_now + timedelta(minutes=minutes)
        return future_time.strftime("%H:%M")

    def get_jst_time_after_seconds(self, seconds: int) -> str:
        """現在時刻から指定秒後のJST時刻を HH:MM:SS 形式で返す"""
        # 現在のJST時刻を取得（UTC+9）
        jst_offset = timedelta(hours=9)
        jst_now = datetime.utcnow() + jst_offset
        future_time = jst_now + timedelta(seconds=seconds)
        return future_time.strftime("%H:%M:%S")

    def print_test_instructions(self):
        """手動テストの手順を表示"""
        schedule_time = self.get_jst_time_after_minutes(2)

        print("\n" + "="*60)
        print("手動テスト手順")
        print("="*60)
        print(f"\nベースURL: {self.base_url}")
        print(f"2分後のJST時刻（スケジュール設定用）: {schedule_time}\n")

        print("【1. 上場企業一覧のテスト】")
        print("-" * 40)
        print("1-1. 手動同期テスト:")
        print("  a) データソース管理画面にアクセス: {}/data-sources".format(self.base_url))
        print("  b) J-Quantsデータソースをクリック")
        print("  c) 「APIエンドポイント管理」をクリック")
        print("  d) 上場企業一覧の行をクリック")
        print("  e) 「今すぐ同期」ボタンをクリック")
        print("  f) 実行履歴に「完了」ステータスが表示されることを確認")
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
        print("  a) スケジュール名に「テストスケジュール」を入力")
        print("  b) 実行時刻に「{}」を入力".format(schedule_time))
        print("  c) 実行頻度で「毎日」を選択")
        print("  d) 取得期間で「実行日から過去7日間」を選択")
        print("  e) 「保存」ボタンをクリック")
        print("  f) 約2分待機")
        print("  g) 「履歴を更新」ボタンをクリック")
        print("  h) 実行履歴に同期タイプ「Full」、実行タイプ「Scheduled」、ステータス「完了」が表示されることを確認")
        print()
        print("="*60)

    async def setup_browser(self, headless: bool = True):
        """ブラウザのセットアップ"""
        if not PLAYWRIGHT_AVAILABLE:
            return False

        self.log(f"ブラウザを起動しています... (ヘッドレス: {headless})")
        try:
            playwright = await async_playwright().start()
            # ヘッドレスモードの切り替えが可能
            self.browser = await playwright.chromium.launch(headless=headless)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            return True
        except Exception as e:
            self.log(f"ブラウザの起動に失敗しました: {e}", "ERROR")
            return False

    async def cleanup_browser(self):
        """ブラウザのクリーンアップ"""
        if self.browser:
            await self.browser.close()

    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """要素が表示されるまで待機"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            self.log(f"要素 {selector} が見つかりませんでした: {e}", "ERROR")
            return False

    async def test_company_sync(self) -> Dict[str, Any]:
        """上場企業一覧の同期テスト"""
        self.log("="*60)
        self.log("上場企業一覧の同期テストを開始します")
        self.log("="*60)

        test_result = {
            "name": "上場企業一覧同期",
            "status": "FAILED",
            "manual_sync": False,
            "errors": []
        }

        try:
            # データソース管理画面へ移動
            self.log("データソース管理画面へアクセス...")
            await self.page.goto(f"{self.base_url}/data-sources")
            await self.page.wait_for_load_state("networkidle")

            # ページ内容を確認
            page_title = await self.page.title()
            self.log(f"ページタイトル: {page_title}")

            # データソーステーブルの存在を確認
            table = await self.page.query_selector('table')
            if not table:
                self.log("データソーステーブルが見つかりません", "ERROR")
                await self.page.screenshot(path="error_no_table.png")
                # ページのHTMLを出力
                html = await self.page.content()
                with open("error_page_content.html", "w") as f:
                    f.write(html)

            # J-Quantsデータソースをクリック
            self.log("J-Quantsデータソースを選択...")
            try:
                await self.page.click("text=J-Quants", timeout=5000)
                await self.page.wait_for_load_state("networkidle")
            except Exception as e:
                self.log(f"J-Quantsクリックでエラー: {e}", "ERROR")
                await self.page.screenshot(path="error_jquants_click.png")

            # APIエンドポイント管理画面へ
            self.log("APIエンドポイント管理画面へ移動...")
            try:
                # もしかしたらAPIエンドポイント管理ボタンが別の場所にあるかもしれない
                # まずはエンドポイントリンクを探す
                endpoint_link = await self.page.query_selector('a[href*="/endpoints"]')
                if endpoint_link:
                    await endpoint_link.click()
                else:
                    await self.page.click("text=APIエンドポイント管理")
                await self.page.wait_for_load_state("networkidle")
            except Exception as e:
                self.log(f"APIエンドポイント管理へのナビゲーションでエラー: {e}", "ERROR")
                await self.page.screenshot(path="error_api_endpoint_navigation.png")

            # 上場企業一覧の行をクリックして詳細を表示
            self.log("上場企業一覧の行をクリックして詳細を表示...")
            await self.page.click('tr:has-text("上場企業一覧")')
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(1000)

            # 手動同期テスト
            self.log("手動同期を実行します...")
            await self.page.click('button:has-text("今すぐ同期")')

            # 同期が完了するまで待機（最大30秒）
            self.log("同期の完了を待機しています...")
            success = False
            for i in range(30):
                await self.page.wait_for_timeout(1000)

                # 成功メッセージが表示されているか確認
                success_element = await self.page.query_selector('text=同期が完了しました')
                if success_element:
                    success = True
                    break

                # 履歴を更新
                if i % 3 == 0:
                    update_button = await self.page.query_selector('button:has-text("履歴を更新")')
                    if update_button:
                        await update_button.click()
                        await self.page.wait_for_timeout(500)

                        # 最新の履歴で完了ステータスを確認
                        completed = await self.page.query_selector('tr:first-child .badge:has-text("完了")')
                        if completed:
                            success = True
                            break

            if success:
                test_result["manual_sync"] = True
                test_result["status"] = "SUCCESS"
                self.log("手動同期テストが成功しました", "SUCCESS")
                await self.page.screenshot(path="test_company_manual_sync_success.png")
            else:
                test_result["errors"].append("手動同期がタイムアウトしました")
                self.log("手動同期がタイムアウトしました", "ERROR")

        except Exception as e:
            test_result["errors"].append(str(e))
            self.log(f"テスト中にエラーが発生しました: {e}", "ERROR")

        return test_result

    async def test_daily_quotes_sync(self) -> Dict[str, Any]:
        """日次株価データの同期テスト"""
        self.log("="*60)
        self.log("日次株価データの同期テストを開始します")
        self.log("="*60)

        test_result = {
            "name": "日次株価データ同期",
            "status": "FAILED",
            "manual_sync": False,
            "errors": []
        }

        try:
            # APIエンドポイント管理画面へ
            await self.page.goto(f"{self.base_url}/data-sources/1/endpoints")
            await self.page.wait_for_load_state("networkidle")

            # 日次株価データの行をクリックして詳細を表示
            self.log("日次株価データの行をクリックして詳細を表示...")
            await self.page.click('tr:has-text("日次株価データ")')
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(1000)

            # 過去7日間を選択
            self.log("過去7日間の同期を設定...")
            await self.page.click('button:has-text("過去7日間")')
            await self.page.wait_for_timeout(500)

            # 同期を開始
            self.log("同期を開始します...")
            await self.page.click('button:has-text("同期を開始")')

            # 同期が完了するまで待機（最大60秒）
            self.log("同期の完了を待機しています...")
            success = False
            for i in range(60):
                await self.page.wait_for_timeout(1000)

                # 成功メッセージが表示されているか確認
                success_element = await self.page.query_selector('text=同期が正常に完了しました')
                if success_element:
                    success = True
                    break

                # 履歴を更新して確認
                if i % 5 == 0:
                    update_button = await self.page.query_selector('button:has-text("履歴を更新")')
                    if update_button:
                        await update_button.click()
                        await self.page.wait_for_timeout(1000)

                        # 最新の履歴で完了ステータスを確認
                        completed = await self.page.query_selector('tr:first-child:has-text("full"):has-text("manual") .badge:has-text("完了")')
                        if completed:
                            success = True
                            break

                self.log(f"待機中... ({i+1}/60)")

            if success:
                test_result["manual_sync"] = True
                test_result["status"] = "SUCCESS"
                self.log("手動同期テストが成功しました", "SUCCESS")
                await self.page.screenshot(path="test_daily_quotes_manual_sync_success.png")
            else:
                test_result["errors"].append("手動同期がタイムアウトしました")
                self.log("手動同期がタイムアウトしました", "ERROR")

        except Exception as e:
            test_result["errors"].append(str(e))
            self.log(f"テスト中にエラーが発生しました: {e}", "ERROR")

        return test_result

    async def test_schedule_crud(self) -> Dict[str, Any]:
        """定期実行スケジュールのCRUD操作と実行結果の取得テスト"""
        self.log("="*60)
        self.log("定期実行スケジュール設定テストを開始します")
        self.log("="*60)

        test_result = {
            "name": "定期実行スケジュール設定",
            "status": "FAILED",
            "daily_schedule_created": False,
            "company_schedule_created": False,
            "errors": []
        }

        try:
            # スケジュール実行時間を2分後に設定
            schedule_time = self.get_jst_time_after_minutes(2)
            self.log(f"スケジュール実行時刻: {schedule_time}")

            # 1. 日次株価データのスケジュール設定
            self.log("日次株価データのスケジュール設定を開始します...")
            await self.page.goto(f"{self.base_url}/data-sources/1/endpoints")
            await self.page.wait_for_load_state("networkidle")
            await self.page.click('tr:has-text("日次株価データ")')
            await self.page.wait_for_load_state("networkidle")

            # 新規スケジュールボタンをクリック
            await self.page.click('button:has-text("新規スケジュール")')
            await self.page.wait_for_timeout(500)

            # スケジュール名を入力
            await self.page.fill('input[placeholder="例: 日次更新（過去7日間）"]', "日次株価データ自動取得")

            # 実行時刻を設定
            try:
                await self.page.get_by_label('実行時刻（JST）').fill(schedule_time)
            except:
                # ラベルが見つからない場合は別の方法で探す
                time_inputs = await self.page.query_selector_all('input[type="time"]')
                if time_inputs:
                    await time_inputs[-1].fill(schedule_time)

            # 実行頻度はデフォルトで「毎日」が選択されているはず
            # 取得期間は「実行日から過去7日間」がデフォルトで選択されているはず

            # 保存ボタンをクリック
            save_button = await self.page.query_selector('button:has-text("保存"):not(:has-text("新規"))')
            if save_button:
                await save_button.click()
                self.log("保存ボタンをクリックしました")
            else:
                # より具体的なセレクタで試す
                modal_save = await self.page.query_selector('.fixed button:has-text("保存")')
                if modal_save:
                    await modal_save.click()
                    self.log("モーダル内の保存ボタンをクリックしました")
                else:
                    self.log("保存ボタンが見つかりません", "ERROR")
            await self.page.wait_for_timeout(1000)

            # 成功メッセージまたはスケジュール一覧で確認
            await self.page.wait_for_timeout(2000)  # 保存後の画面更新を待つ

            # モーダルが閉じられたか確認（固定位置の要素がなくなったか）
            modal_closed = await self.page.query_selector('.fixed:has-text("新規定期実行スケジュール")')
            if not modal_closed:
                # モーダルが閉じられた = 保存成功
                self.log("スケジュール作成モーダルが閉じられました")

            # スケジュール一覧に表示されているか確認
            schedule_table = await self.page.query_selector('h4:has-text("定期実行スケジュール") + button + table')
            if schedule_table:
                schedule_created = await schedule_table.query_selector('td:has-text("日次株価データ自動取得")')
            else:
                schedule_created = await self.page.query_selector('td:has-text("日次株価データ自動取得")')

            if schedule_created:
                test_result["daily_schedule_created"] = True
                self.log("日次株価データのスケジュール作成に成功しました", "SUCCESS")
            else:
                # エラーメッセージを探す
                error_msg = await self.page.query_selector('.text-red-600')
                if error_msg:
                    error_text = await error_msg.text_content()
                    test_result["errors"].append(f"日次株価データのスケジュール作成に失敗: {error_text}")
                else:
                    test_result["errors"].append("日次株価データのスケジュール作成に失敗しました")

            # 2. 上場企業一覧のスケジュール設定
            self.log("上場企業一覧のスケジュール設定を開始します...")
            
            # エンドポイント一覧に戻る
            await self.page.goto(f"{self.base_url}/data-sources/1/endpoints")
            await self.page.wait_for_load_state("networkidle")
            
            # 上場企業一覧の詳細画面を開く
            await self.page.click('tr:has-text("上場企業一覧")')
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(1000)
            
            # 新規スケジュールボタンをクリック
            await self.page.click('button:has-text("新規スケジュール")')
            await self.page.wait_for_timeout(500)
            
            # スケジュール名を入力
            await self.page.fill('input[placeholder="例: 日次更新（過去7日間）"]', "上場企業一覧自動取得")
            
            # 実行時刻を設定（同じ時刻）
            try:
                await self.page.get_by_label('実行時刻（JST）').fill(schedule_time)
            except:
                # ラベルが見つからない場合は別の方法で探す
                time_inputs = await self.page.query_selector_all('input[type="time"]')
                if time_inputs:
                    await time_inputs[-1].fill(schedule_time)
            
            # 保存ボタンをクリック
            save_button = await self.page.query_selector('button:has-text("保存"):not(:has-text("新規"))')
            if save_button:
                await save_button.click()
                self.log("保存ボタンをクリックしました")
            else:
                # より具体的なセレクタで試す
                modal_save = await self.page.query_selector('.fixed button:has-text("保存")')
                if modal_save:
                    await modal_save.click()
                    self.log("モーダル内の保存ボタンをクリックしました")
            await self.page.wait_for_timeout(1000)
            
            # 成功メッセージまたはスケジュール一覧で確認
            await self.page.wait_for_timeout(2000)  # 保存後の画面更新を待つ
            
            # スケジュール一覧に表示されているか確認
            schedule_table = await self.page.query_selector('h4:has-text("定期実行スケジュール") + button + table')
            if schedule_table:
                schedule_created = await schedule_table.query_selector('td:has-text("上場企業一覧自動取得")')
            else:
                schedule_created = await self.page.query_selector('td:has-text("上場企業一覧自動取得")')
            
            if schedule_created:
                test_result["company_schedule_created"] = True
                self.log("上場企業一覧のスケジュール作成に成功しました", "SUCCESS")
            else:
                # エラーメッセージを探す
                error_msg = await self.page.query_selector('.text-red-600')
                if error_msg:
                    error_text = await error_msg.text_content()
                    test_result["errors"].append(f"上場企業一覧のスケジュール作成に失敗: {error_text}")
                else:
                    test_result["errors"].append("上場企業一覧のスケジュール作成に失敗しました")

            # # 2. スケジュール更新のテスト
            # if test_result["schedule_created"]:
            #     self.log("スケジュールを更新します...")
            #
            #     # エンドポイント一覧に戻る
            #     self.log("エンドポイント一覧に戻ります...")
            #     await self.page.goto(f"{self.base_url}/data-sources/1/endpoints")
            #     await self.page.wait_for_load_state("networkidle")
            #
            #     # 日次株価データの行をクリック
            #     await self.page.click('tr:has-text("日次株価データ")')
            #     await self.page.wait_for_load_state("networkidle")
            #     await self.page.wait_for_timeout(1000)
            #
            #     try:
            #         # スケジュールテーブル内の編集ボタンを探す
            #         edit_buttons = self.page.get_by_text("編集")
            #         edit_button_count = await edit_buttons.count()
            #         if edit_button_count > 0:
            #             await edit_buttons.first.click()
            #             await self.page.wait_for_timeout(1000)
            #             self.log("編集ボタンをクリックしました")
            #
            #             # スケジュール名を更新
            #             # プレースホルダーテキストで入力フィールドを探す
            #             name_input = await self.page.query_selector('input[placeholder*="スケジュール名"]')
            #             if name_input:
            #                 # 全選択してから新しい値を入力
            #                 await name_input.click()
            #                 await self.page.keyboard.press("Control+A")
            #                 await name_input.type("更新された自動テストスケジュール")
            #                 self.log("スケジュール名を更新しました")
            #             else:
            #                 # 別の方法で入力フィールドを探す
            #                 first_input = await self.page.query_selector('input[type="text"]:first-of-type')
            #                 if first_input:
            #                     await first_input.click()
            #                     await self.page.keyboard.press("Control+A")
            #                     await first_input.type("更新された自動テストスケジュール")
            #                     self.log("スケジュール名を更新しました")
            #
            #             # 保存ボタンをクリック（編集モーダル内）
            #             save_button = await self.page.query_selector('.fixed button:has-text("保存")')
            #             if save_button:
            #                 await save_button.click()
            #                 self.log("保存ボタンをクリックしました")
            #             else:
            #                 # モーダル外の保存ボタンを探す
            #                 await self.page.click('button:has-text("保存"):visible')
            #             await self.page.wait_for_timeout(2000)
            #
            #             # 更新成功を確認
            #             updated = await self.page.query_selector('text=更新された自動テストスケジュール')
            #             if updated:
            #                 test_result["schedule_updated"] = True
            #                 self.log("スケジュールの更新に成功しました", "SUCCESS")
            #             else:
            #                 # スケジュールテーブルを再確認
            #                 await self.page.wait_for_timeout(1000)
            #                 updated_in_table = await self.page.query_selector('td:has-text("更新された自動テストスケジュール")')
            #                 if updated_in_table:
            #                     test_result["schedule_updated"] = True
            #                     self.log("スケジュールの更新に成功しました", "SUCCESS")
            #                 else:
            #                     test_result["errors"].append("スケジュールの更新に失敗しました")
            #         else:
            #             self.log("編集ボタンが見つかりません", "WARNING")
            #             test_result["errors"].append("編集ボタンが見つかりません")
            #     except Exception as e:
            #         self.log(f"スケジュール更新中にエラー: {e}", "ERROR")
            #         test_result["errors"].append(f"スケジュール更新エラー: {str(e)}")

            # 3. スケジュール実行結果の確認（実行開始から2分待機）
            if test_result["schedule_created"]:
                self.log(f"スケジュールの実行を待機しています（実行予定時刻: {schedule_time}）...")

                # 実行開始タイミング（1分後）+ 実行に2分 = 合計3分待機
                # 10秒ごとに18回 = 180秒 = 3分
                for i in range(18):  # 10秒ごとに18回 = 180秒
                    await self.page.wait_for_timeout(10000)  # 10秒待機

                    # ページをリフレッシュ
                    await self.page.reload()
                    self.log("ページを再読み込みしました")
                    await self.page.wait_for_load_state("networkidle")

                    # 交互にエンドポイントの詳細画面を確認
                    if i % 2 == 0:
                        # 日次株価データの詳細画面に戻る
                        await self.page.click('tr:has-text("日次株価データ") td:has-text("詳細")')
                        await self.page.wait_for_load_state("networkidle")
                        await self.page.wait_for_timeout(1000)
                        self.log("日次株価データの詳細画面を開きました")
                    else:
                        # 上場企業一覧の詳細画面を確認
                        await self.page.click('tr:has-text("上場企業一覧") td:has-text("詳細")')
                        await self.page.wait_for_load_state("networkidle")
                        await self.page.wait_for_timeout(1000)
                        self.log("上場企業一覧の詳細画面を開きました")

                    # スケジュール実行を確認（実行履歴の最初の行をチェック）
                    # 実行履歴テーブルの最初の行を探す
                    history_table = await self.page.query_selector('h4:has-text("実行履歴") + div table')
                    if history_table:
                        rows = await history_table.query_selector_all('tbody tr')
                        for row in rows[:3]:  # 最初の3行をチェック
                            # 行のテキストを取得して確認
                            row_text = await row.text_content()
                            if row_text and "scheduled" in row_text and "完了" in row_text:
                                # 自動テストスケジュールの実行か確認
                                if "自動テストスケジュール" in row_text or "更新された自動テストスケジュール" in row_text:
                                    test_result["schedule_executed"] = True
                                    self.log("スケジュール実行を確認しました", "SUCCESS")
                                    break
                            else:
                                # バッジで確認
                                scheduled_badge = await row.query_selector('span:has-text("scheduled")')
                                completed_badge = await row.query_selector('span:has-text("完了")')
                                task_name = await row.query_selector('td:first-child')

                                if scheduled_badge and completed_badge and task_name:
                                    task_text = await task_name.text_content()
                                    if "自動テストスケジュール" in task_text or "更新された自動テストスケジュール" in task_text:
                                        test_result["schedule_executed"] = True
                                        self.log("スケジュール実行を確認しました", "SUCCESS")
                                        break

                        if test_result["schedule_executed"]:
                            break

                    self.log(f"待機中... ({(i+1)*10}/180秒)")

                if not test_result["schedule_executed"]:
                    test_result["errors"].append("スケジュール実行がタイムアウトしました")
            else:
                self.log("スケジュールが作成されていないため、実行確認をスキップします")

            # # 4. スケジュール削除のテスト（一旦スキップ）
            # if test_result["schedule_created"]:
            #     self.log("スケジュール削除テストは一旦スキップします")
            #     test_result["schedule_deleted"] = True  # 削除テストはスキップ
            # else:
            #     self.log("スケジュールが作成されていないため、削除テストをスキップします")
            #     return test_result

            # 全体のステータスを判定
            if (test_result["schedule_created"] and
                test_result["schedule_updated"] and
                test_result["schedule_executed"] and
                test_result["schedule_deleted"]):
                test_result["status"] = "SUCCESS"
                await self.page.screenshot(path="test_schedule_crud_success.png")

        except Exception as e:
            test_result["errors"].append(str(e))
            self.log(f"テスト中にエラーが発生しました: {e}", "ERROR")
            await self.page.screenshot(path="test_schedule_crud_error.png")

        return test_result

    def generate_report(self):
        """テスト結果のレポートを生成"""
        self.log("テスト結果レポートを生成しています...")

        end_time = datetime.now()
        duration = end_time - self.start_time

        report = {
            "test_date": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(duration),
            "total_tests": len(self.test_results),
            "passed": sum(1 for r in self.test_results if r["status"] == "SUCCESS"),
            "failed": sum(1 for r in self.test_results if r["status"] == "FAILED"),
            "results": self.test_results
        }

        # レポートをJSONファイルとして保存
        report_file = f"regression_test_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # コンソールにサマリーを表示
        print("\n" + "="*60)
        print("自動テスト結果サマリー")
        print("="*60)
        print(f"実行日時: {report['test_date']}")
        print(f"実行時間: {report['duration']}")
        print(f"総テスト数: {report['total_tests']}")
        print(f"成功: {report['passed']}")
        print(f"失敗: {report['failed']}")
        print("="*60)

        for result in self.test_results:
            status_mark = "✅" if result["status"] == "SUCCESS" else "❌"
            print(f"{status_mark} {result['name']}")
            if result["status"] == "FAILED":
                for error in result["errors"]:
                    print(f"   - {error}")

        print("="*60)
        print(f"詳細なレポートは {report_file} に保存されました")

        # スクリーンショットがある場合は通知
        screenshots = [
            "test_company_manual_sync_success.png",
            "test_daily_quotes_manual_sync_success.png"
        ]
        existing_screenshots = [f for f in screenshots if os.path.exists(f)]
        if existing_screenshots:
            print(f"スクリーンショット: {', '.join(existing_screenshots)}")

        return report["failed"] == 0

    async def run_auto_tests(self, headless: bool = True):
        """自動ブラウザテストを実行"""
        if not await self.setup_browser(headless):
            self.log("Playwrightがインストールされていません。手動テストモードに切り替えます。", "WARNING")
            return False

        try:
            # 各機能のテストを実行
            # 上場企業一覧のテスト
            company_result = await self.test_company_sync()
            self.test_results.append(company_result)

            # 日次株価データのテスト
            daily_quotes_result = await self.test_daily_quotes_sync()
            self.test_results.append(daily_quotes_result)

            # 定期実行スケジュールのCRUDテスト
            schedule_result = await self.test_schedule_crud()
            self.test_results.append(schedule_result)

        finally:
            await self.cleanup_browser()

        # レポートを生成
        return self.generate_report()

    def run(self, auto_mode: bool = False, headless: bool = True):
        """リグレッションテストを実行"""
        self.log("リグレッションテストを開始します")

        # 1. データベースをリセット
        if not self.reset_database():
            self.log("データベースのリセットに失敗しました", "ERROR")
            return False

        if auto_mode and PLAYWRIGHT_AVAILABLE:
            # 自動テストモード
            self.log("自動ブラウザテストモードで実行します")
            return asyncio.run(self.run_auto_tests(headless))
        else:
            # 手動テストモード
            if auto_mode and not PLAYWRIGHT_AVAILABLE:
                self.log("Playwrightがインストールされていないため、手動テストモードで実行します", "WARNING")

            # 2. 手動テスト手順を表示
            self.print_test_instructions()

            # 3. 環境の準備完了を通知
            print("\n" + "="*60)
            print("環境の準備が完了しました！")
            print("上記の手順に従って手動テストを実行してください。")
            print("="*60)

            return True


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Stockura リグレッションテストツール")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="自動ブラウザテストモードで実行（Playwrightが必要）"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="確認プロンプトをスキップ"
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="ブラウザを表示状態で実行（ヘッドレスモードを無効化）"
    )
    args = parser.parse_args()

    print("Stockura リグレッションテストツール")
    print("="*60)

    if args.auto:
        if PLAYWRIGHT_AVAILABLE:
            print("自動ブラウザテストモードで実行します")
        else:
            print("Playwrightがインストールされていません。")
            print("インストールするには: pip install playwright && playwright install chromium")
            print("手動テストモードで続行します。")
    else:
        print("手動テストモードで実行します")
        print("自動テストを実行するには --auto オプションを使用してください")

    print("="*60)

    # 確認プロンプト
    if not args.no_confirm:
        response = input("\nデータベースをリセットして環境を初期化しますか？ (y/N): ")
        if response.lower() != 'y':
            print("テストをキャンセルしました。")
            return

    tester = RegressionTester()
    headless = not args.visible  # --visible が指定されたらヘッドレスを無効化
    success = tester.run(auto_mode=args.auto, headless=headless)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
