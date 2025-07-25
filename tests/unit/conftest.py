"""
単体テスト用の設定ファイル
データベースに依存しないテストを実行するための設定
"""

import pytest
import os
import sys

# テスト環境の設定
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"  # インメモリデータベースを使用


@pytest.fixture(scope="function", autouse=True)
def reset_registry():
    """各テストの前後でレジストリをリセット"""
    from app.services.auth import StrategyRegistry
    # テスト前にレジストリをクリア
    StrategyRegistry._strategies.clear()
    yield
    # テスト後にもクリア
    StrategyRegistry._strategies.clear()


@pytest.fixture(scope="session", autouse=True)
def mock_database_dependencies():
    """データベースに依存するモジュールをモック"""
    import unittest.mock as mock
    
    # SQLAlchemyの非同期エンジンをモック
    with mock.patch('sqlalchemy.ext.asyncio.create_async_engine'):
        with mock.patch('sqlalchemy.ext.asyncio.AsyncSession'):
            yield


# データベースフィクスチャを無効化
@pytest.fixture
def setup_test_database():
    """データベースセットアップを無効化"""
    pass


@pytest.fixture
def teardown_test_database():
    """データベースティアダウンを無効化"""
    pass