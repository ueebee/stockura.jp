"""
Token bucket rate limiter tests
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.rate_limiting import TokenBucketRateLimiter


@pytest.fixture
async def mock_redis():
    """モック Redis クライアント"""
    redis = AsyncMock()
    
    # eval メソッドのモックを設定
    redis.eval = AsyncMock()
    
    return redis


@pytest.fixture
async def rate_limiter(mock_redis):
    """テスト用レートリミッター"""
    return TokenBucketRateLimiter(
        redis_client=mock_redis,
        key_prefix="test",
        capacity=10,
        refill_rate=10.0 / 60,  # 10 リクエスト/分
        ttl=3600
    )


class TestTokenBucketRateLimiter:
    """TokenBucketRateLimiter のテスト"""
    
    async def test_check_rate_limit_allowed(self, rate_limiter, mock_redis):
        """レート制限内でリクエストが許可されることを確認"""
        # Redis の応答をモック（許可）
        mock_redis.eval.return_value = [1, 9.0, 0.0]
        
        result = await rate_limiter.check_rate_limit()
        
        assert result is True
        mock_redis.eval.assert_called_once()
    
    async def test_check_rate_limit_denied(self, rate_limiter, mock_redis):
        """レート制限を超えてリクエストが拒否されることを確認"""
        # Redis の応答をモック（拒否）
        mock_redis.eval.return_value = [0, 0.0, 6.0]
        
        result = await rate_limiter.check_rate_limit()
        
        assert result is False
        mock_redis.eval.assert_called_once()
    
    async def test_wait_if_needed_immediate(self, rate_limiter, mock_redis):
        """待機不要な場合、即座に返ることを確認"""
        # Redis の応答をモック（許可）
        mock_redis.eval.return_value = [1, 9.0, 0.0]
        
        start_time = time.time()
        await rate_limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        assert elapsed < 0.1  # 即座に返る
        mock_redis.eval.assert_called_once()
    
    async def test_wait_if_needed_with_delay(self, rate_limiter, mock_redis):
        """待機が必要な場合、適切に待機することを確認"""
        # 最初は拒否、次に許可
        mock_redis.eval.side_effect = [
            [0, 0.0, 0.1],  # 0.1 秒待機
            [1, 9.0, 0.0]   # 許可
        ]
        
        start_time = time.time()
        await rate_limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        assert 0.1 <= elapsed < 0.2  # 約 0.1 秒待機
        assert mock_redis.eval.call_count == 2
    
    async def test_get_remaining_requests(self, rate_limiter, mock_redis):
        """残りリクエスト数を正しく取得できることを確認"""
        # Redis の応答をモック
        mock_redis.eval.return_value = [1, 5.5, 0.0]
        
        remaining = await rate_limiter.get_remaining_requests()
        
        assert remaining == 5  # 切り捨て
        mock_redis.eval.assert_called_once()
    
    async def test_get_reset_time_when_full(self, rate_limiter, mock_redis):
        """バケットが満タンの場合、リセット時刻が None になることを確認"""
        # Redis の応答をモック（満タン）
        mock_redis.eval.return_value = [1, 10.0, 0.0]
        
        reset_time = await rate_limiter.get_reset_time()
        
        assert reset_time is None
        mock_redis.eval.assert_called_once()
    
    async def test_get_reset_time_when_not_full(self, rate_limiter, mock_redis):
        """バケットが満タンでない場合、リセット時刻を計算することを確認"""
        # Redis の応答をモック（半分）
        mock_redis.eval.return_value = [1, 5.0, 0.0]
        
        with patch('time.time', return_value=1000.0):
            reset_time = await rate_limiter.get_reset_time()
        
        # 5 トークン不足、レート 10/60 秒 → 30 秒後に満タン
        expected_reset_time = 1000.0 + 30.0
        assert abs(reset_time - expected_reset_time) < 0.1
    
    async def test_lua_script_execution(self, rate_limiter, mock_redis):
        """Lua スクリプトが正しいパラメータで実行されることを確認"""
        mock_redis.eval.return_value = [1, 9.0, 0.0]
        
        await rate_limiter.wait_if_needed()
        
        # eval 呼び出しの引数を確認
        call_args = mock_redis.eval.call_args
        assert call_args[0][1] == 1  # キー数
        assert call_args[0][2] == "test:bucket"  # キー
        assert call_args[0][3] == 10  # capacity
        assert abs(call_args[0][4] - 10.0/60) < 0.001  # refill_rate
        assert call_args[0][5] == 1  # tokens_requested
        assert call_args[0][7] == 3600  # ttl
    
    async def test_concurrent_requests(self, rate_limiter, mock_redis):
        """複数の同時リクエストが正しく処理されることを確認"""
        # 各リクエストでトークンが減っていく
        responses = [
            [1, 9.0, 0.0],
            [1, 8.0, 0.0],
            [1, 7.0, 0.0],
            [1, 6.0, 0.0],
            [1, 5.0, 0.0]
        ]
        mock_redis.eval.side_effect = responses
        
        # 5 つの同時リクエスト
        tasks = [rate_limiter.wait_if_needed() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        assert mock_redis.eval.call_count == 5
    
    async def test_error_handling(self, rate_limiter, mock_redis):
        """Redis 接続エラー時の動作を確認"""
        mock_redis.eval.side_effect = Exception("Redis connection error")
        
        with pytest.raises(Exception) as exc_info:
            await rate_limiter.check_rate_limit()
        
        assert "Redis connection error" in str(exc_info.value)