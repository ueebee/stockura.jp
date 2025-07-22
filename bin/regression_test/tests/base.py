"""
リグレッションテスト基底クラス
全てのテストクラスはこのクラスを継承する
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

from ..config import TestConfig
from ..browser import BrowserController
from ..utils import setup_logger, TestResult


class BaseRegressionTest(ABC):
    """リグレッションテストの基底クラス"""
    
    def __init__(self, browser: BrowserController, config: TestConfig):
        """
        Args:
            browser: ブラウザコントローラー
            config: テスト設定
        """
        self.browser = browser
        self.config = config
        self.logger = setup_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            config.log_level,
            config.log_file
        )
        self.result = TestResult(self.get_test_name())
        
    def get_test_name(self) -> str:
        """テスト名を取得
        
        Returns:
            テスト名
        """
        return self.__class__.__name__
    
    async def setup(self) -> bool:
        """テストのセットアップ
        
        Returns:
            成功時True、失敗時False
        """
        self.logger.info(f"{self.get_test_name()} のセットアップを開始します")
        return True
    
    async def teardown(self) -> None:
        """テストのティアダウン"""
        self.logger.info(f"{self.get_test_name()} のティアダウンを実行します")
    
    @abstractmethod
    async def execute(self) -> TestResult:
        """テストを実行
        
        Returns:
            テスト結果
        """
        pass
    
    async def run(self) -> TestResult:
        """テストを実行（セットアップ、実行、ティアダウンを含む）
        
        Returns:
            テスト結果
        """
        self.logger.info("="*60)
        self.logger.info(f"{self.get_test_name()} を開始します")
        self.logger.info("="*60)
        
        self.result.start()
        
        try:
            # セットアップ
            if not await self.setup():
                self.result.fail("セットアップに失敗しました")
                return self.result
            
            # テスト実行
            self.result = await self.execute()
            
        except Exception as e:
            self.logger.error(f"テスト実行中にエラーが発生しました: {e}", exc_info=True)
            self.result.fail(f"予期しないエラー: {str(e)}")
            
            # エラー時のスクリーンショット
            if self.config.screenshot_on_failure:
                await self.browser.take_screenshot(f"{self.get_test_name()}_error")
        
        finally:
            # ティアダウン
            try:
                await self.teardown()
            except Exception as e:
                self.logger.error(f"ティアダウン中にエラーが発生しました: {e}")
                self.result.add_warning(f"ティアダウンエラー: {str(e)}")
        
        # 結果のログ出力
        self._log_result()
        
        return self.result
    
    def _log_result(self):
        """テスト結果をログ出力"""
        if self.result.status == "SUCCESS":
            self.logger.info(f"テスト成功: {self.get_test_name()}")
        elif self.result.status == "FAILED":
            self.logger.error(f"テスト失敗: {self.get_test_name()}")
            for error in self.result.errors:
                self.logger.error(f"  - {error}")
        elif self.result.status == "SKIPPED":
            self.logger.info(f"テストスキップ: {self.get_test_name()} - {self.result.details.get('skip_reason', 'N/A')}")
        
        if self.result.warnings:
            for warning in self.result.warnings:
                self.logger.warning(f"  - {warning}")
        
        if self.result.duration:
            self.logger.info(f"実行時間: {self.result.duration:.2f}秒")
    
    # ヘルパーメソッド
    
    async def navigate_to_endpoint_management(self, data_source_id: int = 1) -> bool:
        """APIエンドポイント管理画面へ遷移
        
        Args:
            data_source_id: データソースID
            
        Returns:
            成功時True
        """
        url = f"{self.config.base_url}/data-sources/{data_source_id}/endpoints"
        return await self.browser.goto(url)
    
    async def wait_and_click(self, selector: str, description: str = "", timeout: int = 5000) -> bool:
        """要素を待機してクリック
        
        Args:
            selector: セレクタ
            description: 操作の説明
            timeout: タイムアウト時間
            
        Returns:
            成功時True
        """
        if await self.browser.wait_for_element(selector, timeout):
            return await self.browser.safe_click(selector, description)
        return False
    
    async def wait_and_fill(self, selector: str, value: str, description: str = "", timeout: int = 5000) -> bool:
        """要素を待機して入力
        
        Args:
            selector: セレクタ
            value: 入力値
            description: 操作の説明
            timeout: タイムアウト時間
            
        Returns:
            成功時True
        """
        if await self.browser.wait_for_element(selector, timeout):
            return await self.browser.safe_fill(selector, value, description)
        return False
    
    async def check_element_text(self, selector: str, expected_text: str, timeout: int = 5000) -> bool:
        """要素のテキストが期待値と一致するかチェック
        
        Args:
            selector: セレクタ
            expected_text: 期待するテキスト
            timeout: タイムアウト時間
            
        Returns:
            一致する場合True
        """
        actual_text = await self.browser.get_text(selector, timeout)
        if actual_text and expected_text in actual_text:
            return True
        
        self.logger.warning(f"テキスト不一致 - 期待値: '{expected_text}', 実際: '{actual_text}'")
        return False
    
    async def wait_for_success_message(self, message_text: str, timeout: int = 30000) -> bool:
        """成功メッセージが表示されるまで待機
        
        Args:
            message_text: メッセージテキスト
            timeout: タイムアウト時間
            
        Returns:
            メッセージが表示された場合True
        """
        selector = f'text="{message_text}"'
        return await self.browser.wait_for_element(selector, timeout)