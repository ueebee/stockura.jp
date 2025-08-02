"""
In-memory rate limiter tests
"""

import asyncio
import time
from unittest.mock import patch

import pytest

from app.infrastructure.rate_limiting import InMemoryRateLimiter


@pytest.fixture
async def rate_limiter():
    """テスト用レートリミッター"""
    return InMemoryRateLimiter(
        capacity=10,
        refill_rate=10.0 / 60  # 10 リクエスト/分
    )


class TestInMemoryRateLimiter:
    """InMemoryRateLimiter のテスト"""
    
    async def test_initial_state(self, rate_limiter):
        """初期状態でフル容量があることを確認"""
        assert await rate_limiter.check_rate_limit() is True
        assert await rate_limiter.get_remaining_requests() == 10
        assert await rate_limiter.get_reset_time() is None
    
    async def test_token_consumption(self, rate_limiter):
        """トークンが正しく消費されることを確認"""
        # 5 つのリクエストを実行
        for _ in range(5):
            await rate_limiter.wait_if_needed()
        
        remaining = await rate_limiter.get_remaining_requests()
        assert remaining == 5
    
    async def test_token_refill(self, rate_limiter):
        """トークンが時間経過で補充されることを確認"""
        # すべてのトークンを消費
        for _ in range(10):
            await rate_limiter.wait_if_needed()
        
        assert await rate_limiter.get_remaining_requests() == 0
        
        # 6 秒待機（1 トークン補充される）
        with patch('time.time') as mock_time:
            # 現在時刻を設定
            mock_time.return_value = rate_limiter.last_refill + 6
            
            remaining = await rate_limiter.get_remaining_requests()
            assert remaining == 1  # 6 秒で 1 トークン補充
    
    async def test_wait_when_no_tokens(self, rate_limiter):
        """トークンがない場合に待機することを確認"""
        # すべてのトークンを消費
        for _ in range(10):
            await rate_limiter.wait_if_needed()
        
        # 待機が必要
        start_time = time.time()
        
        # モックで時間を進める
        with patch('time.time') as mock_time:
            call_count = 0
            
            def time_side_effect():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return start_time
                else:
                    return start_time + 6  # 6 秒後
            
            mock_time.side_effect = time_side_effect
            
            with patch('asyncio.sleep') as mock_sleep:
                await rate_limiter.wait_if_needed()
                mock_sleep.assert_called_once()
                
                # 約 6 秒待機することを確認
                sleep_time = mock_sleep.call_args[0][0]
                assert 5.9 < sleep_time < 6.1
    
    async def test_capacity_limit(self, rate_limiter):
        """容量を超えてトークンが増えないことを確認"""
        # 60 秒待機（理論上 10 トークン補充）
        with patch('time.time') as mock_time:
            mock_time.return_value = rate_limiter.last_refill + 60
            
            remaining = await rate_limiter.get_remaining_requests()
            assert remaining == 10  # 容量の上限
    
    async def test_reset_time_calculation(self, rate_limiter):
        """リセット時刻が正しく計算されることを確認"""
        # 5 トークン消費
        for _ in range(5):
            await rate_limiter.wait_if_needed()
        
        # 現在の時刻を基準に計算
        current_time = time.time()
        reset_time = await rate_limiter.get_reset_time()
        
        # 5 トークン不足、レート 10/60 秒 → 約30秒後に満タン
        # 実際の経過時間を考慮して、25-35秒の範囲で確認
        time_to_full = reset_time - current_time
        assert 25 < time_to_full < 35
    
    async def test_concurrent_access(self, rate_limiter):
        """同時アクセス時の整合性を確認"""
        async def consume_token():
            await rate_limiter.wait_if_needed()
            return 1
        
        # 10 個の同時リクエスト
        tasks = [consume_token() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert sum(results) == 10
        assert await rate_limiter.get_remaining_requests() == 0
    
    async def test_thread_safety(self, rate_limiter):
        """スレッドセーフティを確認（ロックが機能すること）"""
        consumed = []
        
        async def consume_with_delay():
            async with rate_limiter._lock:
                rate_limiter._refill_tokens()
                if rate_limiter.tokens >= 1:
                    await asyncio.sleep(0.01)  # 少し待機
                    rate_limiter.tokens -= 1
                    consumed.append(1)
        
        # 5 つの同時タスク
        tasks = [consume_with_delay() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # 5 つすべてが正常に消費される
        assert len(consumed) == 5
        # トークンは整数ではなく浮動小数点数になる可能性があるため、範囲で確認
        assert 4.9 < rate_limiter.tokens < 5.1