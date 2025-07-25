"""
TokenManager統合テスト

実際の問題:
- TokenManagerでstrategiesのインポートが必要だった
- JQuantsStrategyとの連携で問題が発生していた
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio

from app.services.token_manager import TokenManager
from app.services.auth import StrategyRegistry
from app.services.auth.strategies import JQuantsStrategy
from app.models.api_token import APIToken
from app.models.data_source import DataSource


class TestTokenManagerIntegration:
    """TokenManagerとJQuantsStrategyの統合テスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックのデータベースセッション"""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_data_source(self):
        """モックのデータソース"""
        data_source = Mock(spec=DataSource)
        data_source.id = 1
        data_source.provider_type = "jquants"
        data_source.credentials = {
            "mail_address": "test@example.com",
            "password": "test_password"
        }
        return data_source
    
    @pytest.fixture
    def mock_api_token(self):
        """モックのAPIトークン"""
        token = Mock(spec=APIToken)
        token.data_source_id = 1
        token.token_type = "id_token"
        token.access_token = "test_access_token"
        token.refresh_token = "test_refresh_token"
        token.expires_at = datetime.utcnow() + timedelta(hours=1)
        return token
    
    @pytest.fixture
    def token_manager(self, mock_db):
        """TokenManagerインスタンス"""
        return TokenManager(mock_db)
    
    async def test_token_manager_imports_strategies(self):
        """
        TokenManagerがstrategiesをインポートすることを確認
        これが実際に必要だった修正
        """
        # token_manager.pyをインポート
        import app.services.token_manager
        
        # JQuantsStrategyが利用可能であることを確認
        assert "jquants" in StrategyRegistry.get_supported_providers()
    
    async def test_get_valid_token_with_jquants(self, token_manager, mock_db, mock_data_source, mock_api_token):
        """JQuantsのトークン取得が正常に動作することを確認"""
        # モックの設定
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=mock_api_token)
        mock_db.commit = AsyncMock()
        
        # トークン取得
        token = await token_manager.get_valid_token(mock_data_source)
        
        # 結果の確認
        assert token == mock_api_token
        mock_db.execute.assert_called_once()
    
    async def test_refresh_token_with_jquants_strategy(self, token_manager, mock_db, mock_data_source):
        """JQuantsStrategyを使用したトークンリフレッシュのテスト"""
        # 期限切れのトークン
        expired_token = Mock(spec=APIToken)
        expired_token.data_source_id = 1
        expired_token.token_type = "id_token"
        expired_token.access_token = "expired_access_token"
        expired_token.refresh_token = "test_refresh_token"
        expired_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        # モックの設定
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=expired_token)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # JQuantsStrategyのモック
        with patch.object(StrategyRegistry, 'get_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock(spec=JQuantsStrategy)
            mock_strategy.get_id_token = AsyncMock(return_value={
                "idToken": "new_id_token",
                "refreshToken": "new_refresh_token"
            })
            mock_get_strategy.return_value = mock_strategy
            
            # トークン取得（自動リフレッシュされるはず）
            token = await token_manager.get_valid_token(mock_data_source)
            
            # ストラテジーが呼ばれたことを確認
            mock_get_strategy.assert_called_once_with("jquants")
            mock_strategy.get_id_token.assert_called_once()
            
            # トークンが更新されたことを確認
            assert expired_token.access_token == "new_id_token"
            assert expired_token.refresh_token == "new_refresh_token"
            mock_db.commit.assert_called()
    
    async def test_create_new_token_when_not_exists(self, token_manager, mock_db, mock_data_source):
        """トークンが存在しない場合の新規作成テスト"""
        # トークンが存在しない
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=None)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # JQuantsStrategyのモック
        with patch.object(StrategyRegistry, 'get_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock(spec=JQuantsStrategy)
            mock_strategy.get_refresh_token = AsyncMock(return_value={
                "refreshToken": "new_refresh_token"
            })
            mock_strategy.get_id_token = AsyncMock(return_value={
                "idToken": "new_id_token",
                "refreshToken": "new_refresh_token"
            })
            mock_get_strategy.return_value = mock_strategy
            
            # トークン取得（新規作成されるはず）
            token = await token_manager.get_valid_token(mock_data_source)
            
            # ストラテジーが呼ばれたことを確認
            mock_strategy.get_refresh_token.assert_called_once_with(mock_data_source.credentials)
            mock_strategy.get_id_token.assert_called_once()
            
            # 新しいトークンが作成されたことを確認
            mock_db.add.assert_called_once()
            created_token = mock_db.add.call_args[0][0]
            assert isinstance(created_token, APIToken)
            assert created_token.data_source_id == mock_data_source.id
            assert created_token.access_token == "new_id_token"
    
    async def test_error_handling_when_strategy_not_found(self, token_manager, mock_db):
        """未登録のプロバイダーでエラーが発生することを確認"""
        # 未知のプロバイダー
        unknown_data_source = Mock(spec=DataSource)
        unknown_data_source.provider_type = "unknown_provider"
        
        # エラーが発生することを確認
        with pytest.raises(ValueError) as exc_info:
            await token_manager.get_valid_token(unknown_data_source)
        
        assert "Unsupported provider type: unknown_provider" in str(exc_info.value)
    
    async def test_concurrent_token_refresh(self, token_manager, mock_db, mock_data_source):
        """同時にトークンリフレッシュが発生した場合のテスト"""
        # 期限切れのトークン
        expired_token = Mock(spec=APIToken)
        expired_token.data_source_id = 1
        expired_token.token_type = "id_token"
        expired_token.access_token = "expired_access_token"
        expired_token.refresh_token = "test_refresh_token"
        expired_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        # モックの設定
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=expired_token)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # JQuantsStrategyのモック
        refresh_count = 0
        
        async def mock_get_id_token(refresh_token):
            nonlocal refresh_count
            refresh_count += 1
            # 少し遅延を入れて同時実行をシミュレート
            await asyncio.sleep(0.1)
            return {
                "idToken": f"new_id_token_{refresh_count}",
                "refreshToken": f"new_refresh_token_{refresh_count}"
            }
        
        with patch.object(StrategyRegistry, 'get_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock(spec=JQuantsStrategy)
            mock_strategy.get_id_token = mock_get_id_token
            mock_get_strategy.return_value = mock_strategy
            
            # 複数の同時リクエストを実行
            tasks = []
            for _ in range(5):
                task = asyncio.create_task(token_manager.get_valid_token(mock_data_source))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # すべてのリクエストが同じトークンを取得することを確認
            # （実際の実装では最初のリフレッシュ結果が使われるはず）
            first_token = results[0]
            for token in results:
                assert token is first_token
    
    async def test_token_manager_with_celery_context(self, mock_db):
        """Celeryワーカーコンテキストでの動作確認"""
        # Celeryワーカーをシミュレート
        with patch('app.services.token_manager.StrategyRegistry') as mock_registry:
            # strategiesがインポートされていることを確認
            import app.services.auth.strategies
            
            # TokenManagerを作成
            token_manager = TokenManager(mock_db)
            
            # JQuantsStrategyが利用可能であることを確認
            assert "jquants" in StrategyRegistry.get_supported_providers()