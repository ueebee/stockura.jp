"""
トークンマネージャーのテスト
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.token_manager import TokenManager, AutoTokenRefresh


class TestTokenManager:
    """TokenManagerクラスのテスト"""

    @pytest.fixture
    def token_manager(self):
        """TokenManagerのインスタンスを作成"""
        return TokenManager()

    @pytest.mark.asyncio
    async def test_store_and_get_refresh_token(self, token_manager):
        """リフレッシュトークンの保存と取得のテスト"""
        data_source_id = 1
        token = "test_refresh_token"
        expired_at = datetime.utcnow() + timedelta(days=7)
        
        # トークンを保存
        await token_manager.store_refresh_token(data_source_id, token, expired_at)
        
        # トークンを取得
        retrieved_token = await token_manager.get_valid_refresh_token(data_source_id)
        
        assert retrieved_token == token

    @pytest.mark.asyncio
    async def test_store_and_get_id_token(self, token_manager):
        """IDトークンの保存と取得のテスト"""
        data_source_id = 1
        token = "test_id_token"
        expired_at = datetime.utcnow() + timedelta(hours=24)
        
        # トークンを保存
        await token_manager.store_id_token(data_source_id, token, expired_at)
        
        # トークンを取得
        retrieved_token = await token_manager.get_valid_id_token(data_source_id)
        
        assert retrieved_token == token

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self, token_manager):
        """期限切れトークンがNoneを返すことのテスト"""
        data_source_id = 1
        token = "expired_token"
        expired_at = datetime.utcnow() - timedelta(hours=1)  # 1時間前に期限切れ
        
        # 期限切れトークンを保存
        await token_manager.store_refresh_token(data_source_id, token, expired_at)
        
        # トークンを取得（期限切れなのでNoneが返る）
        retrieved_token = await token_manager.get_valid_refresh_token(data_source_id)
        
        assert retrieved_token is None

    @pytest.mark.asyncio
    async def test_clear_tokens(self, token_manager):
        """トークンクリアのテスト"""
        data_source_id = 1
        refresh_token = "test_refresh_token"
        id_token = "test_id_token"
        expired_at = datetime.utcnow() + timedelta(hours=24)
        
        # トークンを保存
        await token_manager.store_refresh_token(data_source_id, refresh_token, expired_at)
        await token_manager.store_id_token(data_source_id, id_token, expired_at)
        
        # トークンをクリア
        await token_manager.clear_tokens(data_source_id)
        
        # トークンが取得できないことを確認
        assert await token_manager.get_valid_refresh_token(data_source_id) is None
        assert await token_manager.get_valid_id_token(data_source_id) is None

    @pytest.mark.asyncio
    async def test_get_token_status(self, token_manager):
        """トークン状態取得のテスト"""
        data_source_id = 1
        refresh_token = "test_refresh_token"
        id_token = "test_id_token"
        refresh_expired_at = datetime.utcnow() + timedelta(days=7)
        id_expired_at = datetime.utcnow() + timedelta(hours=24)
        
        # トークンを保存
        await token_manager.store_refresh_token(data_source_id, refresh_token, refresh_expired_at)
        await token_manager.store_id_token(data_source_id, id_token, id_expired_at)
        
        # トークン状態を取得
        status = await token_manager.get_token_status(data_source_id)
        
        assert status["data_source_id"] == data_source_id
        assert status["refresh_token"]["exists"] is True
        assert status["refresh_token"]["is_valid"] is True
        assert status["id_token"]["exists"] is True
        assert status["id_token"]["is_valid"] is True

    @pytest.mark.asyncio
    async def test_clear_expired_tokens(self, token_manager):
        """期限切れトークン一括削除のテスト"""
        # 有効なトークンと期限切れトークンを保存
        valid_data_source_id = 1
        expired_data_source_id = 2
        
        valid_expired_at = datetime.utcnow() + timedelta(hours=1)
        expired_expired_at = datetime.utcnow() - timedelta(hours=1)
        
        await token_manager.store_refresh_token(valid_data_source_id, "valid_token", valid_expired_at)
        await token_manager.store_refresh_token(expired_data_source_id, "expired_token", expired_expired_at)
        
        # 期限切れトークンを削除
        await token_manager.clear_expired_tokens()
        
        # 有効なトークンは残り、期限切れトークンは削除されることを確認
        assert await token_manager.get_valid_refresh_token(valid_data_source_id) == "valid_token"
        assert await token_manager.get_valid_refresh_token(expired_data_source_id) is None


class TestAutoTokenRefresh:
    """AutoTokenRefreshクラスのテスト"""

    @pytest.fixture
    def token_manager(self):
        return TokenManager()

    @pytest.fixture
    def mock_data_source_service(self):
        return Mock()

    @pytest.fixture
    def auto_refresh(self, token_manager, mock_data_source_service):
        return AutoTokenRefresh(token_manager, mock_data_source_service)

    @pytest.mark.asyncio
    async def test_ensure_valid_id_token_with_existing_token(self, auto_refresh, token_manager):
        """既存の有効なIDトークンがある場合のテスト"""
        data_source_id = 1
        existing_token = "existing_id_token"
        expired_at = datetime.utcnow() + timedelta(hours=23)
        
        # 既存のIDトークンを保存
        await token_manager.store_id_token(data_source_id, existing_token, expired_at)
        
        # 有効なIDトークンを取得
        result = await auto_refresh.ensure_valid_id_token(data_source_id)
        
        assert result == existing_token

    @pytest.mark.asyncio
    async def test_ensure_valid_id_token_with_refresh_token(self, auto_refresh, token_manager, mock_data_source_service):
        """リフレッシュトークンからIDトークンを取得する場合のテスト"""
        data_source_id = 1
        refresh_token = "valid_refresh_token"
        new_id_token = "new_id_token"
        
        # リフレッシュトークンを保存
        refresh_expired_at = datetime.utcnow() + timedelta(days=6)
        await token_manager.store_refresh_token(data_source_id, refresh_token, refresh_expired_at)
        
        # モックを設定
        mock_data_source = Mock()
        mock_data_source.provider_type = "jquants"
        mock_data_source.base_url = "https://api.jquants.com"
        mock_data_source_service.get_data_source = AsyncMock(return_value=mock_data_source)
        
        # J-Quantsストラテジーをモック
        with patch('app.services.token_manager.StrategyRegistry.get_strategy') as mock_get_strategy:
            mock_strategy_class = Mock()
            mock_strategy = Mock()
            mock_strategy.get_id_token.return_value = (new_id_token, datetime.utcnow() + timedelta(hours=24))
            mock_strategy_class.return_value = mock_strategy
            mock_get_strategy.return_value = mock_strategy_class
            
            # 有効なIDトークンを取得
            result = await auto_refresh.ensure_valid_id_token(data_source_id)
            
            assert result == new_id_token

    @pytest.mark.asyncio
    async def test_get_new_refresh_token_success(self, auto_refresh, mock_data_source_service):
        """新しいリフレッシュトークン取得成功のテスト"""
        data_source_id = 1
        new_refresh_token = "new_refresh_token"
        
        # モックを設定
        mock_data_source = Mock()
        mock_data_source.provider_type = "jquants"
        mock_data_source.base_url = "https://api.jquants.com"
        mock_data_source.get_credentials.return_value = {
            "mailaddress": "test@example.com",
            "password": "password"
        }
        mock_data_source_service.get_data_source = AsyncMock(return_value=mock_data_source)
        
        # J-Quantsストラテジーをモック
        with patch('app.services.token_manager.StrategyRegistry.get_strategy') as mock_get_strategy:
            mock_strategy_class = Mock()
            mock_strategy = Mock()
            mock_strategy.get_refresh_token.return_value = (new_refresh_token, datetime.utcnow() + timedelta(days=7))
            mock_strategy_class.return_value = mock_strategy
            mock_get_strategy.return_value = mock_strategy_class
            
            # 新しいリフレッシュトークンを取得
            result = await auto_refresh._get_new_refresh_token(data_source_id)
            
            assert result == new_refresh_token

    @pytest.mark.asyncio
    async def test_get_new_refresh_token_failure(self, auto_refresh, mock_data_source_service):
        """新しいリフレッシュトークン取得失敗のテスト"""
        data_source_id = 1
        
        # データソースが見つからない場合
        mock_data_source_service.get_data_source = AsyncMock(return_value=None)
        
        # 新しいリフレッシュトークンを取得
        result = await auto_refresh._get_new_refresh_token(data_source_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_new_id_token_success(self, auto_refresh, mock_data_source_service):
        """新しいIDトークン取得成功のテスト"""
        data_source_id = 1
        refresh_token = "refresh_token"
        new_id_token = "new_id_token"
        
        # モックを設定
        mock_data_source = Mock()
        mock_data_source.provider_type = "jquants"
        mock_data_source.base_url = "https://api.jquants.com"
        mock_data_source_service.get_data_source = AsyncMock(return_value=mock_data_source)
        
        # J-Quantsストラテジーをモック
        with patch('app.services.token_manager.StrategyRegistry.get_strategy') as mock_get_strategy:
            mock_strategy_class = Mock()
            mock_strategy = Mock()
            mock_strategy.get_id_token.return_value = (new_id_token, datetime.utcnow() + timedelta(hours=24))
            mock_strategy_class.return_value = mock_strategy
            mock_get_strategy.return_value = mock_strategy_class
            
            # 新しいIDトークンを取得
            result = await auto_refresh._get_new_id_token(data_source_id, refresh_token)
            
            assert result == new_id_token

    @pytest.mark.asyncio
    async def test_get_new_id_token_failure(self, auto_refresh, mock_data_source_service):
        """新しいIDトークン取得失敗のテスト"""
        data_source_id = 1
        refresh_token = "refresh_token"
        
        # データソースが見つからない場合
        mock_data_source_service.get_data_source = AsyncMock(return_value=None)
        
        # 新しいIDトークンを取得
        result = await auto_refresh._get_new_id_token(data_source_id, refresh_token)
        
        assert result is None