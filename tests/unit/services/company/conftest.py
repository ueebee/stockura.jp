"""
単体テスト用のconftest（DBを使わない）
"""

import pytest


@pytest.fixture(scope="function")
def setup_test_database():
    """単体テストではDBを使わないため、空のフィクスチャを定義"""
    pass