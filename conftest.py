"""
プロジェクト全体のpytest設定ファイル

このファイルはプロジェクト全体で共有されるフィクスチャ、
設定、ヘルパー関数を定義します。
"""
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPYTHONPATHに追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# テスト環境用の.env.testファイルを読み込む
env_test_path = Path(__file__).parent / ".env.test"
if env_test_path.exists():
    load_dotenv(dotenv_path=env_test_path, override=True)
    print(f"Loaded test environment from {env_test_path}")
else:
    print(f"Warning: {env_test_path} not found. Using default environment.")

# テスト環境であることを確実にする
os.environ["APP_ENV"] = "test"

from app.core.config import settings
from app.db.base_class import Base
# モデルをインポートして、メタデータに登録されるようにする
from app.models import *  # noqa: F401, F403


# テスト用データベースURL（非同期ドライバを使用）
import os

# 環境変数から直接取得、または設定から取得
db_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)

# 非同期ドライバに変換
if "postgresql://" in db_url and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

# すでにテスト用DBの場合はそのまま使用
if "stockura_test" not in db_url:
    # stockuraをstockura_testに置換
    TEST_DATABASE_URL = db_url.replace("/stockura", "/stockura_test")
else:
    TEST_DATABASE_URL = db_url


@pytest.fixture(scope="session")
def event_loop():
    """
    セッションスコープのイベントループを作成
    
    これにより、セッション全体で同じイベントループを使用し、
    非同期フィクスチャの問題を回避します。
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_db_engine():
    """
    テスト用の非同期データベースエンジンを作成
    
    各テスト関数ごとに新しいエンジンを作成し、
    テスト間の独立性を保証します。
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # テスト用にコネクションプールを無効化
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    テスト用の非同期データベースセッションを作成
    
    各テストで独立したトランザクションを使用し、
    テスト終了時に自動的にロールバックします。
    """
    async_session_maker = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        async with session.begin():
            yield session
            # トランザクションは自動的にロールバック


@pytest.fixture
def override_get_db(async_session: AsyncSession):
    """
    FastAPIの依存性注入をオーバーライドするためのフィクスチャ
    
    テスト用のデータベースセッションを使用するように
    get_db関数を置き換えます。
    """
    async def _override_get_db():
        yield async_session
    
    return _override_get_db


@pytest.fixture
def test_data_dir() -> str:
    """テストデータディレクトリのパスを返す"""
    return os.path.join(os.path.dirname(__file__), "tests", "data")


@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    環境変数をモックするためのフィクスチャ
    
    使用例:
        def test_something(mock_env_vars):
            mock_env_vars("API_KEY", "test_key")
    """
    def _mock_env_vars(key: str, value: str):
        monkeypatch.setenv(key, value)
    
    return _mock_env_vars


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    シングルトンオブジェクトをリセットするフィクスチャ
    
    テスト間でシングルトンの状態が共有されないようにします。
    """
    # 必要に応じてシングルトンのリセット処理を追加
    yield
    # クリーンアップ処理


def pytest_configure(config):
    """
    pytestの設定をカスタマイズ
    
    カスタムマーカーの登録や、プラグインの設定を行います。
    """
    config.addinivalue_line(
        "markers", "slow: 実行に時間がかかるテスト"
    )
    config.addinivalue_line(
        "markers", "integration: 統合テスト"
    )
    config.addinivalue_line(
        "markers", "e2e: エンドツーエンドテスト"
    )
    config.addinivalue_line(
        "markers", "performance: パフォーマンステスト"
    )
    config.addinivalue_line(
        "markers", "external_api: 外部APIを使用するテスト"
    )


def pytest_collection_modifyitems(config, items):
    """
    収集されたテストアイテムを修正
    
    テストの実行順序の調整や、自動的なマーカーの付与を行います。
    """
    for item in items:
        # tests/integrationディレクトリのテストに自動的にintegrationマーカーを付与
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # tests/e2eディレクトリのテストに自動的にe2eマーカーを付与
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # tests/performanceディレクトリのテストに自動的にperformanceマーカーを付与
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)


# テスト実行時の共通設定
def pytest_runtest_setup(item):
    """
    各テストの実行前のセットアップ
    
    環境変数の設定や、ログレベルの調整などを行います。
    """
    # テスト環境であることを示す環境変数を設定
    os.environ["TESTING"] = "1"
    
    # ログレベルをDEBUGに設定（必要に応じて調整）
    import logging
    logging.getLogger("app").setLevel(logging.DEBUG)


def pytest_runtest_teardown(item):
    """
    各テストの実行後のクリーンアップ
    
    一時ファイルの削除や、リソースの解放を行います。
    """
    # テスト環境フラグをクリア
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


# 共通のアサーションヘルパー
class AssertionHelpers:
    """テストで使用する共通のアサーションヘルパー"""
    
    @staticmethod
    def assert_valid_uuid(value: str):
        """有効なUUID形式かどうかを検証"""
        import uuid
        try:
            uuid.UUID(value)
        except ValueError:
            pytest.fail(f"Invalid UUID format: {value}")
    
    @staticmethod
    def assert_datetime_recent(dt, seconds=60):
        """日時が最近のものかどうかを検証"""
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        if not (now - timedelta(seconds=seconds) <= dt <= now):
            pytest.fail(f"Datetime {dt} is not within {seconds} seconds of now")
    
    @staticmethod
    def assert_response_ok(response):
        """HTTPレスポンスが成功しているかを検証"""
        assert 200 <= response.status_code < 300, (
            f"Expected successful response, got {response.status_code}: "
            f"{response.text}"
        )


@pytest.fixture
def assert_helpers():
    """アサーションヘルパーを提供するフィクスチャ"""
    return AssertionHelpers()


# パフォーマンステスト用のフィクスチャ
@pytest.fixture
def benchmark_timer():
    """
    簡易的なベンチマークタイマー
    
    使用例:
        def test_performance(benchmark_timer):
            with benchmark_timer("operation_name", max_seconds=1.0):
                # テスト対象の処理
    """
    import time
    from contextlib import contextmanager
    
    @contextmanager
    def timer(operation_name: str, max_seconds: float = None):
        start = time.time()
        yield
        elapsed = time.time() - start
        print(f"\n{operation_name} took {elapsed:.3f} seconds")
        if max_seconds and elapsed > max_seconds:
            pytest.fail(
                f"{operation_name} took {elapsed:.3f} seconds, "
                f"exceeding limit of {max_seconds} seconds"
            )
    
    return timer