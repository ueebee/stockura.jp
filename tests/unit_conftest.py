"""
単体テスト用の設定ファイル

データベース接続を必要としない単体テストのための設定
"""
import pytest


@pytest.fixture(autouse=True)
def no_database_setup(monkeypatch):
    """
    データベースセットアップを無効化するフィクスチャ
    """
    # setup_test_databaseフィクスチャの自動実行を無効化
    monkeypatch.setattr("conftest.setup_test_database", lambda: None)
    yield