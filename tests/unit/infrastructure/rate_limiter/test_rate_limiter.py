"""RateLimiter クラスのテスト"""
import asyncio
from unittest.mock import Mock, patch, AsyncMock

import pytest

from app.infrastructure.rate_limiter import RateLimiter, with_rate_limit


class TestRateLimiter:
    """RateLimiter クラスのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        limiter = RateLimiter(max_requests=100, window_seconds=60, name="Test API")
        
        assert limiter.name == "Test API"
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60
        assert limiter._token_bucket is not None
    
    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """acquire: 正常なトークン取得"""
        limiter = RateLimiter(max_requests=10, window_seconds=1)
        
        # トークンがあるので即座に取得
        await limiter.acquire()
        
        # 複数トークンも取得可能
        await limiter.acquire(3)
        
        assert 5.9 <= limiter.available_tokens <= 6.1
    
    @pytest.mark.asyncio
    async def test_acquire_exceeds_capacity(self):
        """acquire: 容量を超えるトークン要求"""
        limiter = RateLimiter(max_requests=10, window_seconds=1)
        
        with pytest.raises(ValueError, match="Cannot acquire 11 tokens: exceeds capacity"):
            await limiter.acquire(11)
    
    def test_try_acquire(self):
        """try_acquire のテスト"""
        limiter = RateLimiter(max_requests=5, window_seconds=1)
        
        # 成功ケース
        assert limiter.try_acquire(3) is True
        assert 1.9 <= limiter.available_tokens <= 2.1
        
        # 失敗ケース
        assert limiter.try_acquire(3) is False
        assert 1.9 <= limiter.available_tokens <= 2.1
    
    def test_get_status(self):
        """get_status のテスト"""
        limiter = RateLimiter(max_requests=100, window_seconds=60, name="Test")
        
        status = limiter.get_status()
        
        assert status["name"] == "Test"
        assert status["available_tokens"] == 100.0
        assert status["max_tokens"] == 100
        assert status["window_seconds"] == 60
        assert status["requests_per_second"] == pytest.approx(100 / 60)
    
    @pytest.mark.asyncio
    async def test_with_rate_limit_decorator_async(self):
        """with_rate_limit デコレーター: 非同期関数"""
        limiter = RateLimiter(max_requests=5, window_seconds=1)
        call_count = 0
        
        class TestClass:
            def __init__(self):
                self._rate_limiter = limiter
            
            @with_rate_limit(lambda self: self._rate_limiter)
            async def api_call(self, value):
                nonlocal call_count
                call_count += 1
                return value * 2
        
        obj = TestClass()
        
        # 正常に動作
        result = await obj.api_call(5)
        assert result == 10
        assert call_count == 1
        
        # レート制限が適用される
        assert 3.9 <= limiter.available_tokens <= 4.1
    
    def test_with_rate_limit_decorator_sync(self):
        """with_rate_limit デコレーター: 同期関数"""
        limiter = RateLimiter(max_requests=5, window_seconds=1)
        call_count = 0
        
        class TestClass:
            def __init__(self):
                self._rate_limiter = limiter
            
            @with_rate_limit(lambda self: self._rate_limiter)
            def sync_api_call(self, value):
                nonlocal call_count
                call_count += 1
                return value * 2
        
        obj = TestClass()
        
        # 正常に動作
        result = obj.sync_api_call(5)
        assert result == 10
        assert call_count == 1
        
        # レート制限が適用される（try_acquire 使用）
        assert 3.9 <= limiter.available_tokens <= 4.1
    
    def test_with_rate_limit_sync_exceeded(self):
        """with_rate_limit デコレーター: 同期関数でレート制限超過"""
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        
        class TestClass:
            def __init__(self):
                self._rate_limiter = limiter
            
            @with_rate_limit(lambda self: self._rate_limiter)
            def sync_api_call(self):
                return "success"
        
        obj = TestClass()
        
        # 1 回目は成功
        assert obj.sync_api_call() == "success"
        
        # 2 回目も実行されるが警告が出る（実際のテストではログ出力を確認）
        with patch('app.infrastructure.rate_limiter.rate_limiter.logger') as mock_logger:
            result = obj.sync_api_call()
            assert result == "success"
            mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_logging_with_wait(self):
        """待機時のログ出力テスト"""
        limiter = RateLimiter(max_requests=1, window_seconds=1, name="TestAPI")
        
        # 全トークン消費
        await limiter.acquire()
        
        # ログ出力を確認
        with patch('app.infrastructure.rate_limiter.rate_limiter.logger') as mock_logger:
            # モック時間で待機時間をシミュレート
            with patch.object(limiter._token_bucket, 'get_wait_time', return_value=0.5):
                # 実際の待機はモックで回避
                with patch.object(limiter._token_bucket, 'acquire', new_callable=AsyncMock):
                    await limiter.acquire()
                    
                    # 警告ログが出力されることを確認
                    mock_logger.info.assert_called_with(
                        "TestAPI: Rate limit approaching. "
                        "Waiting 0.50s for 1 token(s). "
                        "Current: 0.0/1"
                    )