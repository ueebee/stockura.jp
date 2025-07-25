#!/usr/bin/env python3
"""
リグレッションテストスクリプト（リファクタリング版）
DBをクリーンな状態にリセットし、主要機能の動作確認を手動/自動で行う
"""
import asyncio
import os
import sys
import argparse
import subprocess
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

# 新しいモジュール構造をインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from regression_test.config import TestConfig
from regression_test.test_suite import TestSuite
from regression_test.browser import PLAYWRIGHT_AVAILABLE

# Playwrightのインポート（利用可能な場合）
if PLAYWRIGHT_AVAILABLE:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page


# 後方互換性のため、旧RegressionTesterクラスを残す
class RegressionTester:
    def __init__(self):
        self.start_time = datetime.now()
        # 環境変数から設定を読み込み、デフォルト値を設定
        self.base_url = os.getenv("STOCKURA_BASE_URL", "http://localhost:8000")
        self.docker_compose_file = os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.yml")
        self.test_timeout = int(os.getenv("TEST_TIMEOUT", "60"))  # 秒
        self.schedule_wait_minutes = int(os.getenv("SCHEDULE_WAIT_MINUTES", "2"))
        self.test_results = []
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # _tmpディレクトリを作成（存在しない場合）
        self.tmp_dir = Path("_tmp")
        self.tmp_dir.mkdir(exist_ok=True)

        # 設定をログ出力
        self.log(f"設定: base_url={self.base_url}, timeout={self.test_timeout}s, schedule_wait={self.schedule_wait_minutes}分")

    def log(self, message: str, level: str = "INFO"):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_command(self, command: str, description: str = "", retry_count: int = 3) -> bool:
        """コマンドを実行し、成功/失敗を返す（リトライ機能付き）"""
        self.log(f"実行: {description or command}")
        
        for attempt in range(retry_count):
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
                self.log(f"エラー (試行 {attempt + 1}/{retry_count}): {e.stderr}", "ERROR")
                if attempt < retry_count - 1:
                    self.log(f"5秒後にリトライします...")
                    time.sleep(5)
                else:
                    return False
        return False

    def reset_database(self) -> bool:
        """データベースをクリーンな状態にリセット"""
        self.log("="*60)
        self.log("データベースのリセットを開始します")
        self.log("="*60)

        # Docker Composeコマンドのベース
        compose_cmd = f"docker compose -f {self.docker_compose_file}"

        commands = [
            (f"{compose_cmd} down", "Docker環境を停止"),
            ("docker volume rm stockurajp_postgres_data", "PostgreSQLボリュームを削除"),
            (f"{compose_cmd} up -d", "Docker環境を起動"),
            ("sleep 10", "サービスの起動を待機"),
            (f"{compose_cmd} exec -T web alembic upgrade head", "マイグレーションを実行"),
            (f"{compose_cmd} down", "Docker環境を一旦停止"),
            (f"{compose_cmd} up -d", "Docker環境を再起動"),
            ("sleep 15", "全サービスの起動を待機")
        ]

        for command, description in commands:
            if not self.run_command(command, description):
                # ボリューム削除でエラーが出る場合は無視（既に削除されている場合）
                if "docker volume rm" in command:
                    self.log("ボリュームが既に削除されています（問題ありません）")
                    continue
                else:
                    self.log(f"コマンド '{command}' の実行に失敗しました", "ERROR")
                    return False

        self.log("データベースのリセットが完了しました", "SUCCESS")
        return True

    def get_jst_time_after_minutes(self, minutes: int) -> str:
        """現在時刻から指定分後のJST時刻を HH:MM 形式で返す"""
        # 現在のJST時刻を取得（UTC+9）
        from datetime import timezone
        jst_offset = timezone(timedelta(hours=9))
        jst_now = datetime.now(jst_offset)
        future_time = jst_now + timedelta(minutes=minutes)
        return future_time.strftime("%H:%M")

    def get_jst_time_after_seconds(self, seconds: int) -> str:
        """現在時刻から指定秒後のJST時刻を HH:MM:SS 形式で返す"""
        # 現在のJST時刻を取得（UTC+9）
        from datetime import timezone
        jst_offset = timezone(timedelta(hours=9))
        jst_now = datetime.now(jst_offset)
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

    async def safe_click(self, selector: str, description: str = "", timeout: int = 5000) -> bool:
        """安全なクリック操作（エラーハンドリング付き）"""
        try:
            await self.page.click(selector, timeout=timeout)
            self.log(f"クリック成功: {description or selector}")
            return True
        except Exception as e:
            self.log(f"クリック失敗: {description or selector} - {e}", "ERROR")
            return False

    async def safe_fill(self, selector: str, value: str, description: str = "", timeout: int = 5000) -> bool:
        """安全な入力操作（エラーハンドリング付き）"""
        try:
            await self.page.fill(selector, value, timeout=timeout)
            self.log(f"入力成功: {description or selector} = {value}")
            return True
        except Exception as e:
            self.log(f"入力失敗: {description or selector} - {e}", "ERROR")
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
                await self.page.screenshot(path=str(self.tmp_dir / "error_no_table.png"))
                # ページのHTMLを出力
                html = await self.page.content()
                with open(self.tmp_dir / "error_page_content.html", "w") as f:
                    f.write(html)
                test_result["errors"].append("データソーステーブルが見つかりません")
                return test_result

            # J-Quantsデータソースをクリック
            self.log("J-Quantsデータソースを選択...")
            if not await self.safe_click("text=J-Quants", "J-Quantsデータソース"):
                await self.page.screenshot(path=str(self.tmp_dir / "error_jquants_click.png"))
                test_result["errors"].append("J-Quantsデータソースのクリックに失敗")
                return test_result

            await self.page.wait_for_load_state("networkidle")

            # APIエンドポイント管理画面へ
            self.log("APIエンドポイント管理画面へ移動...")
            endpoint_link = await self.page.query_selector('a[href*="/endpoints"]')
            if endpoint_link:
                if not await self.safe_click('a[href*="/endpoints"]', "APIエンドポイント管理リンク"):
                    test_result["errors"].append("APIエンドポイント管理へのナビゲーションに失敗")
                    return test_result
            else:
                if not await self.safe_click("text=APIエンドポイント管理", "APIエンドポイント管理ボタン"):
                    test_result["errors"].append("APIエンドポイント管理ボタンのクリックに失敗")
                    return test_result

            await self.page.wait_for_load_state("networkidle")

            # 上場企業一覧の行をクリックして詳細を表示
            self.log("上場企業一覧の行をクリックして詳細を表示...")
            if not await self.safe_click('tr:has-text("上場企業一覧")', "上場企業一覧の行"):
                test_result["errors"].append("上場企業一覧の行のクリックに失敗")
                return test_result

            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(1000)

            # 手動同期テスト
            self.log("手動同期を実行します...")
            if not await self.safe_click('button:has-text("今すぐ同期")', "今すぐ同期ボタン"):
                test_result["errors"].append("今すぐ同期ボタンのクリックに失敗")
                return test_result

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
                await self.page.screenshot(path=str(self.tmp_dir / "test_company_manual_sync_success.png"))
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
                await self.page.screenshot(path=str(self.tmp_dir / "test_daily_quotes_manual_sync_success.png"))
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
            # networkidleの代わりに特定要素の表示を待つ
            await self.page.wait_for_selector('tr:has-text("日次株価データ")', timeout=5000)
            
            await self.page.click('tr:has-text("日次株価データ")')
            # 詳細パネルの表示を待つ（新規スケジュールボタンが表示されるまで）
            await self.page.wait_for_selector('button:has-text("新規スケジュール")', timeout=5000)

            # 新規スケジュールボタンをクリック
            await self.page.click('button:has-text("新規スケジュール")')
            # モーダルの表示を待つ（入力フィールドが表示されるまで）
            await self.page.wait_for_selector('input[placeholder="例: 日次更新（過去7日間）"]', timeout=3000)

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
            # まずは通常のセレクタで試す
            save_button = await self.page.query_selector('button:has-text("保存"):not(:has-text("新規"))')
            if save_button:
                await save_button.click()
                self.log("保存ボタンをクリックしました")
            else:
                # モーダル内の保存ボタンを探す
                await self.page.click('.fixed button:has-text("保存")')
                self.log("モーダル内の保存ボタンをクリックしました")
            
            # モーダルが閉じるのを待つ（固定位置の要素がなくなるまで）
            try:
                await self.page.wait_for_selector('.fixed:has-text("新規定期実行スケジュール")', state='detached', timeout=5000)
            except:
                # タイムアウトした場合は、スケジュール一覧が表示されているか確認
                pass

            # モーダルが閉じられた = 保存成功
            self.log("スケジュール作成モーダルが閉じられました")
            
            # 少し待機してからスケジュール一覧を確認
            await self.page.wait_for_timeout(1000)
            
            # スケジュール一覧に表示されているか確認
            schedule_created = await self.page.query_selector('td:has-text("日次株価データ自動取得")')
            
            if not schedule_created:
                # デバッグ用スクリーンショット
                await self.page.screenshot(path=str(self.tmp_dir / "test_daily_schedule_not_found.png"))
                # より広範囲で検索
                any_schedule = await self.page.query_selector('table:has-text("スケジュール名")')
                if any_schedule:
                    self.log("スケジュールテーブルは存在しますが、作成したスケジュールが見つかりません", "WARNING")
            
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
            # 上場企業一覧の行が表示されるまで待つ
            await self.page.wait_for_selector('tr:has-text("上場企業一覧")', timeout=5000)
            
            # 上場企業一覧の詳細画面を開く
            await self.page.click('tr:has-text("上場企業一覧")')
            # 新規スケジュールボタンが表示されるまで待つ
            await self.page.wait_for_selector('button:has-text("新規スケジュール")', timeout=5000)
            
            # 新規スケジュールボタンをクリック
            await self.page.click('button:has-text("新規スケジュール")')
            # time入力フィールドが表示されるまで待つ
            await self.page.wait_for_selector('input[type="time"]', timeout=3000)
            
            # 上場企業一覧の場合はスケジュール名の入力欄がないのでスキップ
            self.log(f"上場企業一覧のスケジュール時刻を設定: {schedule_time}")
            
            # 実行時刻を設定（同じ時刻）
            try:
                await self.page.get_by_label('実行時刻（JST）').fill(schedule_time)
                self.log("ラベルで時刻入力フィールドを見つけました")
            except:
                # ラベルが見つからない場合は別の方法で探す
                time_inputs = await self.page.query_selector_all('input[type="time"]')
                if time_inputs:
                    await time_inputs[-1].fill(schedule_time)
                    self.log(f"time入力フィールドを{len(time_inputs)}個見つけ、最後のものに入力しました")
                else:
                    self.log("時刻入力フィールドが見つかりません", "ERROR")
            
            # 保存前のスクリーンショット（デバッグ時のみ必要）
            # await self.page.screenshot(path="test_company_schedule_before_save.png")
            
            # 保存ボタンをクリック
            # まずは通常のセレクタで試す
            save_button = await self.page.query_selector('button:has-text("保存"):not(:has-text("新規"))')
            if save_button:
                await save_button.click()
                self.log("保存ボタンをクリックしました")
            else:
                # モーダル内の保存ボタンを探す
                await self.page.click('.fixed button:has-text("保存")')
                self.log("モーダル内の保存ボタンをクリックしました")
            
            # モーダルが閉じるのを待つ（固定位置の要素がなくなるまで）
            try:
                await self.page.wait_for_selector('.fixed:has-text("定期実行時間の設定")', state='detached', timeout=5000)
            except:
                # タイムアウトした場合は続行
                pass
            
            # デバッグ用スクリーンショット（必要に応じて有効化）
            # await self.page.screenshot(path="test_company_schedule_after_save.png")
            
            # モーダルが閉じられた = 保存成功
            self.log("スケジュール設定モーダルが閉じられました")
            
            # エンドポイント一覧に戻って確認
            self.log("エンドポイント一覧に戻って状態を確認します...")
            await self.page.goto(f"{self.base_url}/data-sources/1/endpoints")
            # 上場企業一覧の行が表示されるまで待つ
            await self.page.wait_for_selector('tr:has-text("上場企業一覧")', timeout=5000)
            
            # エンドポイント一覧で確認（実行モードが「定期実行」に変わっているか）
            company_row = await self.page.query_selector('tr:has-text("上場企業一覧")')
            if company_row:
                # より詳細なデバッグ情報
                row_text = await company_row.text_content()
                self.log(f"上場企業一覧の行内容: {row_text}")
                
                schedule_mode = await company_row.query_selector('text=定期実行')
                if schedule_mode:
                    test_result["company_schedule_created"] = True
                    self.log("上場企業一覧のスケジュール作成に成功しました（実行モードが定期実行に変更）", "SUCCESS")
                else:
                    manual_mode = await company_row.query_selector('text=手動のみ')
                    if manual_mode:
                        self.log("実行モードがまだ「手動のみ」です", "WARNING")
                    
                    # 詳細画面でも確認
                    await self.page.click('tr:has-text("上場企業一覧")')
                    await self.page.wait_for_load_state("networkidle")
                    await self.page.wait_for_timeout(1000)
                    
                    # スケジュールが設定されているか確認
                    no_schedule_msg = await self.page.query_selector('text=スケジュールが設定されていません')
                    if not no_schedule_msg:
                        # 実行時刻が表示されているか確認
                        schedule_info = await self.page.query_selector(f'text={schedule_time}')
                        if schedule_info:
                            test_result["company_schedule_created"] = True
                            self.log("上場企業一覧のスケジュール作成に成功しました（詳細画面で確認）", "SUCCESS")
                        else:
                            self.log(f"スケジュール時刻 {schedule_time} が見つかりません", "WARNING")
                            test_result["errors"].append("上場企業一覧のスケジュール時刻が確認できません")
                    else:
                        self.log("「スケジュールが設定されていません」メッセージが表示されています", "WARNING")
                        test_result["errors"].append("上場企業一覧のスケジュールが作成されていません")
            else:
                self.log("上場企業一覧の行が見つかりません", "ERROR")
                test_result["errors"].append("上場企業一覧のスケジュール作成に失敗しました")

            # 全体のステータスを判定
            if test_result["daily_schedule_created"] and test_result["company_schedule_created"]:
                test_result["status"] = "SUCCESS"
                self.log("両方のスケジュール設定に成功しました", "SUCCESS")
                await self.page.screenshot(path=str(self.tmp_dir / "test_schedule_creation_success.png"))

        except Exception as e:
            test_result["errors"].append(str(e))
            self.log(f"テスト中にエラーが発生しました: {e}", "ERROR")
            await self.page.screenshot(path=str(self.tmp_dir / "test_schedule_crud_error.png"))

        return test_result

    def generate_report(self):
        """テスト結果のレポートを生成"""
        self.log("テスト結果レポートを生成しています...")

        end_time = datetime.now()
        duration = end_time - self.start_time

        # 詳細な統計情報を計算
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "SUCCESS")
        failed_tests = sum(1 for r in self.test_results if r["status"] == "FAILED")
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = {
            "test_date": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(duration),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": round(success_rate, 2),
            "environment": {
                "base_url": self.base_url,
                "docker_compose_file": self.docker_compose_file,
                "test_timeout": self.test_timeout,
                "schedule_wait_minutes": self.schedule_wait_minutes
            },
            "results": self.test_results
        }

        # レポートをJSONファイルとして保存
        report_file = self.tmp_dir / f"regression_test_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
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
        print(f"成功率: {report['success_rate']}%")
        print("="*60)

        for result in self.test_results:
            status_mark = "✅" if result["status"] == "SUCCESS" else "❌"
            print(f"{status_mark} {result['name']}")
            if result["status"] == "FAILED":
                for error in result["errors"]:
                    print(f"   - {error}")
            else:
                # 成功したテストの詳細情報も表示
                if "manual_sync" in result and result["manual_sync"]:
                    print("   - 手動同期: 成功")
                if "daily_schedule_created" in result and result["daily_schedule_created"]:
                    print("   - 日次スケジュール作成: 成功")
                if "company_schedule_created" in result and result["company_schedule_created"]:
                    print("   - 企業スケジュール作成: 成功")

        print("="*60)
        print(f"詳細なレポートは {report_file} に保存されました")

        # スクリーンショットがある場合は通知
        screenshots = list(self.tmp_dir.glob("*.png"))
        if screenshots:
            print(f"スクリーンショット: {len(screenshots)}個のファイルが生成されました")
            for screenshot in screenshots:
                print(f"  - {screenshot.name}")

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

    parser = argparse.ArgumentParser(
        description="Stockura リグレッションテストツール",
        epilog="""
使用例:
  # 手動テストモード（デフォルト）
  python bin/regression_test.py

  # 自動テストモード（Playwrightが必要）
  python bin/regression_test.py --auto

  # ブラウザを表示して自動テスト
  python bin/regression_test.py --auto --visible

  # カスタム設定でテスト
  python bin/regression_test.py --base-url http://localhost:8080 --timeout 120

  # データベースリセットをスキップ
  python bin/regression_test.py --skip-db-reset --auto

環境変数:
  STOCKURA_BASE_URL: テスト対象のベースURL
  DOCKER_COMPOSE_FILE: Docker Composeファイルのパス
  TEST_TIMEOUT: テストタイムアウト時間（秒）
  SCHEDULE_WAIT_MINUTES: スケジュール実行待機時間（分）
        """
    )
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
    parser.add_argument(
        "--base-url",
        default=os.getenv("STOCKURA_BASE_URL", "http://localhost:8000"),
        help="テスト対象のベースURL（デフォルト: http://localhost:8000）"
    )
    parser.add_argument(
        "--docker-compose-file",
        default=os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.yml"),
        help="Docker Composeファイルのパス（デフォルト: docker-compose.yml）"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("TEST_TIMEOUT", "60")),
        help="テストタイムアウト時間（秒、デフォルト: 60）"
    )
    parser.add_argument(
        "--schedule-wait",
        type=int,
        default=int(os.getenv("SCHEDULE_WAIT_MINUTES", "2")),
        help="スケジュール実行待機時間（分、デフォルト: 2）"
    )
    parser.add_argument(
        "--skip-db-reset",
        action="store_true",
        help="データベースリセットをスキップ"
    )
    parser.add_argument(
        "--retry-count",
        type=int,
        default=3,
        help="コマンド実行のリトライ回数（デフォルト: 3）"
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

    # 環境変数を設定
    os.environ["STOCKURA_BASE_URL"] = args.base_url
    os.environ["DOCKER_COMPOSE_FILE"] = args.docker_compose_file
    os.environ["TEST_TIMEOUT"] = str(args.timeout)
    os.environ["SCHEDULE_WAIT_MINUTES"] = str(args.schedule_wait)

    tester = RegressionTester()
    headless = not args.visible  # --visible が指定されたらヘッドレスを無効化
    
    # データベースリセットをスキップする場合
    if args.skip_db_reset:
        tester.log("データベースリセットをスキップします", "WARNING")
        if args.auto and PLAYWRIGHT_AVAILABLE:
            success = asyncio.run(tester.run_auto_tests(headless))
        else:
            tester.print_test_instructions()
            print("\n" + "="*60)
            print("環境の準備が完了しました！")
            print("上記の手順に従って手動テストを実行してください。")
            print("="*60)
            success = True
    else:
        success = tester.run(auto_mode=args.auto, headless=headless)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()