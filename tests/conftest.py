"""
グローバル pytest 設定とフィクスチャ

このファイルは pytest の設定とすべてのテストで使用可能な
グローバルフィクスチャを定義します。
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from _pytest.config import Config
from _pytest.python import Module

# プロジェクトルートを Python パスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# テスト設定をインポート
from tests.settings.test_config import override_app_settings, test_settings

# ログ設定
logging.basicConfig(
    level=getattr(logging, test_settings.log_level),
    format="%(asctime) s - %(name) s - %(levelname) s - %(message) s",
)
logger = logging.getLogger(__name__)


def pytest_configure(config: Config) -> None:
    """pytest 設定のカスタマイズ"""
    # カスタムマーカーの登録
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may use external resources)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (full system tests)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async (handled by pytest-asyncio)"
    )

    # テスト環境設定を適用
    override_app_settings()

    logger.info("Test configuration initialized")


def pytest_sessionstart(session) -> None:
    """テストセッション開始時の処理"""
    logger.info("Starting test session")
    
    # 環境変数の確認
    assert os.getenv("TEST_MODE") == "true", "TEST_MODE should be set to 'true'"
    assert os.getenv("ENV") == "test", "ENV should be set to 'test'"


def pytest_sessionfinish(session, exitstatus) -> None:
    """テストセッション終了時の処理"""
    logger.info(f"Test session finished with exit status: {exitstatus}")


def pytest_collection_modifyitems(config, items):
    """テスト項目の収集後の処理"""
    # 並列実行時のワーカー ID 取得
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id:
        # ワーカー ID をテスト設定に反映
        worker_num = int(worker_id.replace("gw", ""))
        test_settings.test_db_schema = f"test_{worker_num}"
        test_settings.test_redis_db = worker_num + 1
        logger.info(f"Worker {worker_id} initialized with schema: {test_settings.test_db_schema}")


@pytest.fixture(scope="session")
def event_loop():
    """
    セッションスコープの非同期イベントループ
    
    すべての非同期テストで共有されるイベントループを提供します。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    
    asyncio.set_event_loop(loop)
    yield loop
    
    # クリーンアップ
    try:
        _cancel_all_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
    finally:
        loop.close()


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """イベントループ内のすべてのタスクをキャンセル"""
    tasks = asyncio.all_tasks(loop) if hasattr(asyncio, "all_tasks") else asyncio.Task.all_tasks(loop)
    for task in tasks:
        task.cancel()
    
    # キャンセルされたタスクの完了を待つ
    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))


@pytest.fixture(scope="session")
def app_settings():
    """テスト用アプリケーション設定"""
    return test_settings


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    各テストの前にシングルトンをリセット
    
    シングルトンパターンを使用しているオブジェクトが
    テスト間で状態を共有しないようにします。
    """
    # 必要に応じてシングルトンのリセット処理を追加
    yield


@pytest.fixture
def anyio_backend():
    """非同期バックエンドの指定（asyncio を使用）"""
    return "asyncio"


@pytest.fixture(scope="function")
def mock_env_vars(monkeypatch):
    """
    環境変数をモックするためのフィクスチャ
    
    使用例:
        def test_something(mock_env_vars):
            mock_env_vars("API_KEY", "test_key")
            # テストコード
    """
    def _mock_env(key: str, value: str):
        monkeypatch.setenv(key, value)
    
    return _mock_env


@pytest.fixture
def temp_dir(tmp_path):
    """
    一時ディレクトリを提供するフィクスチャ
    
    テスト終了後に自動的にクリーンアップされます。
    """
    return tmp_path


# テストのスキップ条件を定義
skip_if_no_db = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Database URL not configured"
)

skip_if_no_redis = pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="Redis URL not configured"
)

skip_in_ci = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipped in CI environment"
)


# 共通のテストデータ
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "test_password_123"
TEST_STOCK_SYMBOL = "7203"  # トヨタ自動車