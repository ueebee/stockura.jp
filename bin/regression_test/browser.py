"""
ブラウザ制御モジュール
Playwrightを使用したブラウザ操作を提供
"""
import asyncio
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime

from .config import TestConfig
from .utils import setup_logger, ensure_dir

# Playwrightのインポート（インストールされている場合のみ）
try:
    from playwright.async_api import (
        Browser, BrowserContext, Page, async_playwright, Playwright
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any
    BrowserContext = Any
    Page = Any
    Playwright = Any


class BrowserController:
    """ブラウザ制御クラス"""
    
    def __init__(self, config: TestConfig):
        """
        Args:
            config: テスト設定
        """
        self.config = config
        self.logger = setup_logger(self.__class__.__name__, config.log_level, config.log_file)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # スクリーンショット用ディレクトリ
        self.screenshot_dir = ensure_dir(config.screenshot_dir)
        
    @property
    def is_available(self) -> bool:
        """Playwrightが利用可能かチェック"""
        return PLAYWRIGHT_AVAILABLE
    
    async def setup(self) -> bool:
        """ブラウザをセットアップ
        
        Returns:
            成功時True、失敗時False
        """
        if not self.is_available:
            self.logger.error("Playwrightがインストールされていません")
            self.logger.info("インストールするには: pip install playwright && playwright install chromium")
            return False
        
        self.logger.info(f"ブラウザを起動しています... (ヘッドレス: {self.config.headless})")
        
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']  # Docker環境用
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP'
            )
            self.page = await self.context.new_page()
            
            # コンソールメッセージのログ出力
            self.page.on("console", lambda msg: self.logger.debug(f"Console: {msg.text}"))
            
            self.logger.info("ブラウザの起動に成功しました")
            return True
            
        except Exception as e:
            self.logger.error(f"ブラウザの起動に失敗しました: {e}")
            return False
    
    async def cleanup(self):
        """ブラウザをクリーンアップ"""
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.context:
            await self.context.close()
            self.context = None
            
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            
        self.logger.info("ブラウザをクリーンアップしました")
    
    async def create_page(self) -> Optional[Page]:
        """新しいページを作成
        
        Returns:
            Pageオブジェクト、失敗時None
        """
        if not self.context:
            self.logger.error("ブラウザコンテキストが初期化されていません")
            return None
            
        try:
            page = await self.context.new_page()
            page.on("console", lambda msg: self.logger.debug(f"Console: {msg.text}"))
            return page
        except Exception as e:
            self.logger.error(f"ページの作成に失敗しました: {e}")
            return None
    
    async def goto(self, url: str, timeout: Optional[int] = None) -> bool:
        """指定URLに遷移
        
        Args:
            url: 遷移先URL
            timeout: タイムアウト時間（ミリ秒）
            
        Returns:
            成功時True、失敗時False
        """
        if not self.page:
            self.logger.error("ページが初期化されていません")
            return False
            
        if timeout is None:
            timeout = self.config.test_timeout * 1000
            
        try:
            self.logger.info(f"URL '{url}' に遷移します")
            await self.page.goto(url, timeout=timeout, wait_until='networkidle')
            self.logger.info(f"遷移完了: {self.page.url}")
            return True
        except Exception as e:
            self.logger.error(f"URL遷移に失敗しました: {e}")
            await self.take_screenshot("navigation_error")
            return False
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """要素が表示されるまで待機
        
        Args:
            selector: CSSセレクタまたはテキストセレクタ
            timeout: タイムアウト時間（ミリ秒）
            
        Returns:
            要素が見つかった場合True、タイムアウトした場合False
        """
        if not self.page:
            return False
            
        if timeout is None:
            timeout = 30000
            
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            self.logger.debug(f"要素が見つかりました: {selector}")
            return True
        except Exception as e:
            self.logger.warning(f"要素が見つかりませんでした: {selector} - {e}")
            return False
    
    async def safe_click(self, selector: str, description: str = "", timeout: int = 5000) -> bool:
        """安全なクリック操作（エラーハンドリング付き）
        
        Args:
            selector: クリック対象のセレクタ
            description: 操作の説明
            timeout: タイムアウト時間（ミリ秒）
            
        Returns:
            成功時True、失敗時False
        """
        if not self.page:
            return False
            
        try:
            await self.page.click(selector, timeout=timeout)
            self.logger.info(f"クリック成功: {description or selector}")
            return True
        except Exception as e:
            self.logger.error(f"クリック失敗: {description or selector} - {e}")
            await self.take_screenshot("click_error")
            return False
    
    async def safe_fill(self, selector: str, value: str, description: str = "", timeout: int = 5000) -> bool:
        """安全な入力操作（エラーハンドリング付き）
        
        Args:
            selector: 入力対象のセレクタ
            value: 入力値
            description: 操作の説明
            timeout: タイムアウト時間（ミリ秒）
            
        Returns:
            成功時True、失敗時False
        """
        if not self.page:
            return False
            
        try:
            await self.page.fill(selector, value, timeout=timeout)
            self.logger.info(f"入力成功: {description or selector} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"入力失敗: {description or selector} - {e}")
            await self.take_screenshot("fill_error")
            return False
    
    async def get_text(self, selector: str, timeout: int = 5000) -> Optional[str]:
        """要素のテキストを取得
        
        Args:
            selector: 対象要素のセレクタ
            timeout: タイムアウト時間（ミリ秒）
            
        Returns:
            テキスト内容、失敗時None
        """
        if not self.page:
            return None
            
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                return await element.text_content()
            return None
        except Exception as e:
            self.logger.error(f"テキスト取得失敗: {selector} - {e}")
            return None
    
    async def is_visible(self, selector: str) -> bool:
        """要素が表示されているかチェック
        
        Args:
            selector: 対象要素のセレクタ
            
        Returns:
            表示されている場合True
        """
        if not self.page:
            return False
            
        try:
            return await self.page.is_visible(selector)
        except Exception:
            return False
    
    async def select_option(self, selector: str, value: str, timeout: int = 5000) -> bool:
        """セレクトボックスのオプションを選択
        
        Args:
            selector: セレクトボックスのセレクタ
            value: 選択する値
            timeout: タイムアウト時間（ミリ秒）
            
        Returns:
            成功時True、失敗時False
        """
        if not self.page:
            return False
            
        try:
            await self.page.select_option(selector, value, timeout=timeout)
            self.logger.info(f"オプション選択成功: {selector} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"オプション選択失敗: {selector} - {e}")
            return False
    
    async def wait_for_load_state(self, state: str = "networkidle") -> bool:
        """ページの読み込み完了を待機
        
        Args:
            state: 待機する状態 ('load', 'domcontentloaded', 'networkidle')
            
        Returns:
            成功時True
        """
        if not self.page:
            return False
            
        try:
            await self.page.wait_for_load_state(state)
            return True
        except Exception as e:
            self.logger.error(f"ページ読み込み待機エラー: {e}")
            return False
    
    async def take_screenshot(self, name: str = "screenshot") -> Optional[str]:
        """スクリーンショットを撮影
        
        Args:
            name: ファイル名（拡張子なし）
            
        Returns:
            保存したファイルパス、失敗時None
        """
        if not self.page:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            await self.page.screenshot(path=str(filepath), full_page=True)
            self.logger.info(f"スクリーンショットを保存: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"スクリーンショット撮影失敗: {e}")
            return None
    
    async def wait_for_timeout(self, milliseconds: int):
        """指定時間待機
        
        Args:
            milliseconds: 待機時間（ミリ秒）
        """
        if self.page:
            await self.page.wait_for_timeout(milliseconds)
        else:
            await asyncio.sleep(milliseconds / 1000)