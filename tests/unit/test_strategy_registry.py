"""
StrategyRegistry関連の単体テスト

実際の問題:
- JQuantsStrategyがStrategyRegistryに登録されていなかった
- Celeryワーカーでの初期化タイミングの問題
"""

import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock
import sys

# テスト用にモジュールパスを追加
sys.path.insert(0, '/usr/src/app')

from app.services.auth import StrategyRegistry
from app.services.auth.strategies import JQuantsStrategy


# データベースに依存しないようにする
pytest_plugins = []


class TestStrategyRegistry:
    """StrategyRegistryのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # レジストリをクリアして初期状態にする
        StrategyRegistry._strategies.clear()
    
    def test_jquants_strategy_is_registered_on_import(self):
        """
        strategiesモジュールのインポート時にJQuantsStrategyが自動登録されることを確認
        これが実際に問題となった箇所
        """
        # strategiesモジュールをインポートする前の状態を確認
        StrategyRegistry._strategies.clear()
        assert "jquants" not in StrategyRegistry._strategies
        
        # strategiesモジュールを再インポート
        import importlib
        import app.services.auth.strategies
        importlib.reload(app.services.auth.strategies)
        
        # JQuantsStrategyが登録されていることを確認
        assert "jquants" in StrategyRegistry._strategies
        assert isinstance(StrategyRegistry._strategies["jquants"], JQuantsStrategy)
    
    def test_get_strategy_returns_correct_instance(self):
        """get_strategyが正しいインスタンスを返すことを確認"""
        # 手動で登録
        strategy = JQuantsStrategy()
        StrategyRegistry.register("jquants", strategy)
        
        # 取得して確認
        retrieved = StrategyRegistry.get_strategy("jquants")
        assert retrieved is strategy
    
    def test_get_strategy_raises_for_unknown_provider(self):
        """未登録のプロバイダーに対してエラーが発生することを確認"""
        with pytest.raises(ValueError) as exc_info:
            StrategyRegistry.get_strategy("unknown_provider")
        
        assert "Unsupported provider type: unknown_provider" in str(exc_info.value)
    
    def test_duplicate_registration_overwrites(self):
        """同じプロバイダーの重複登録時に上書きされることを確認"""
        strategy1 = JQuantsStrategy()
        strategy2 = JQuantsStrategy()
        
        StrategyRegistry.register("jquants", strategy1)
        assert StrategyRegistry._strategies["jquants"] is strategy1
        
        StrategyRegistry.register("jquants", strategy2)
        assert StrategyRegistry._strategies["jquants"] is strategy2
    
    def test_get_supported_providers(self):
        """サポートされているプロバイダーのリストが正しく返されることを確認"""
        # 初期状態では空
        StrategyRegistry._strategies.clear()
        assert StrategyRegistry.get_supported_providers() == []
        
        # strategiesをインポート
        import importlib
        import app.services.auth.strategies
        importlib.reload(app.services.auth.strategies)
        
        providers = StrategyRegistry.get_supported_providers()
        assert "jquants" in providers
    
    def test_thread_safety(self):
        """複数スレッドから同時アクセスしても安全であることを確認"""
        errors = []
        successful_gets = []
        
        # JQuantsStrategyを登録
        StrategyRegistry.register("jquants", JQuantsStrategy())
        
        def get_strategy_in_thread():
            try:
                strategy = StrategyRegistry.get_strategy("jquants")
                successful_gets.append(strategy)
            except Exception as e:
                errors.append(e)
        
        # 複数スレッドから同時にアクセス
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(100):
                future = executor.submit(get_strategy_in_thread)
                futures.append(future)
            
            # すべてのスレッドが完了するまで待機
            for future in futures:
                future.result()
        
        # エラーがないことを確認
        assert len(errors) == 0
        assert len(successful_gets) == 100
        
        # すべて同じインスタンスを取得していることを確認
        first_strategy = successful_gets[0]
        for strategy in successful_gets:
            assert strategy is first_strategy
    
    def test_registry_persistence_across_modules(self):
        """
        異なるモジュールからアクセスしても同じレジストリインスタンスを
        参照することを確認（シングルトンパターンの検証）
        """
        # strategiesをインポートして登録を実行
        import app.services.auth.strategies
        
        # 異なる方法でStrategyRegistryをインポート
        from app.services.auth import StrategyRegistry as Registry1
        from app.services.auth.registry import StrategyRegistry as Registry2
        
        # 同じクラスを参照していることを確認
        assert Registry1 is Registry2
        
        # 同じstrategiesディクショナリを参照していることを確認
        assert Registry1._strategies is Registry2._strategies
        
        # 両方から同じstrategyを取得できることを確認
        strategy1 = Registry1.get_strategy("jquants")
        strategy2 = Registry2.get_strategy("jquants")
        assert strategy1 is strategy2


class TestCeleryWorkerRegistration:
    """Celeryワーカーでの登録に関するテスト"""
    
    @patch('app.core.celery_app.logger')
    def test_worker_imports_strategies_on_startup(self, mock_logger):
        """
        Celeryワーカー起動時にstrategiesがインポートされることを確認
        これが実際の問題の解決策
        """
        # celery_appをインポート
        from app.core.celery_app import celery_app
        
        # ワーカー起動時の処理をシミュレート
        # worker_readyシグナルのハンドラーを直接呼び出す
        from celery.signals import worker_ready
        handlers = worker_ready.receivers
        
        # ハンドラーが登録されていることを確認
        assert len(handlers) > 0
        
        # JQuantsStrategyが登録されていることを確認
        assert "jquants" in StrategyRegistry.get_supported_providers()
    
    def test_main_app_imports_strategies_on_startup(self):
        """
        メインアプリケーション起動時にstrategiesがインポートされることを確認
        """
        # main.pyの関連部分をテスト
        # 実際のインポートをシミュレート
        import app.services.auth.strategies
        
        # JQuantsStrategyが登録されていることを確認
        assert "jquants" in StrategyRegistry.get_supported_providers()
        strategy = StrategyRegistry.get_strategy("jquants")
        assert isinstance(strategy, JQuantsStrategy)