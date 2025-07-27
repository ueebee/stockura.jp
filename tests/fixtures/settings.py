"""
テスト用設定フィクスチャ

アプリケーション設定をテスト用にオーバーライドするフィクスチャを提供します。
"""

import pytest
from unittest.mock import patch

from tests.settings.test_config import test_settings


@pytest.fixture
def app_settings():
    """
    テスト用のアプリケーション設定
    
    テスト環境用に設定された Settings オブジェクトを返します。
    """
    return test_settings


@pytest.fixture
def mock_env_vars():
    """
    環境変数をモックするフィクスチャ
    
    使用例:
        mock_env_vars("API_KEY", "test_key")
    """
    def _mock_env(key: str, value: str):
        with patch.dict("os.environ", {key: value}):
            return value
    
    return _mock_env


@pytest.fixture
def override_settings():
    """
    設定を一時的にオーバーライドするフィクスチャ
    
    使用例:
        with override_settings(debug=True):
            # デバッグモードでテスト実行
    """
    def _override(**kwargs):
        original_values = {}
        for key, value in kwargs.items():
            if hasattr(test_settings, key):
                original_values[key] = getattr(test_settings, key)
                setattr(test_settings, key, value)
        
        yield test_settings
        
        # 元の値に戻す
        for key, value in original_values.items():
            setattr(test_settings, key, value)
    
    return _override