"""TokenBucket クラスのテスト"""
import asyncio
import time
from unittest.mock import patch

import pytest

from app.infrastructure.rate_limiter.token_bucket import TokenBucket


class TestTokenBucket:
    """TokenBucket クラスのテスト"""
    
    def test_init_valid_params(self):
        """正常なパラメータでの初期化"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10.0
        assert bucket.refill_period == 1.0
        assert bucket.refill_rate == 10.0
    
    def test_init_invalid_capacity(self):
        """無効な容量での初期化"""
        with pytest.raises(ValueError, match="Capacity must be positive"):
            TokenBucket(capacity=0, refill_period=1.0)
        
        with pytest.raises(ValueError, match="Capacity must be positive"):
            TokenBucket(capacity=-5, refill_period=1.0)
    
    def test_init_invalid_refill_period(self):
        """無効な補充期間での初期化"""
        with pytest.raises(ValueError, match="Refill period must be positive"):
            TokenBucket(capacity=10, refill_period=0)
        
        with pytest.raises(ValueError, match="Refill period must be positive"):
            TokenBucket(capacity=10, refill_period=-1.0)
    
    def test_try_acquire_success(self):
        """try_acquire: トークンが十分ある場合"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)
        
        # 1 トークン取得
        assert bucket.try_acquire(1) is True
        assert 8.9 <= bucket.tokens <= 9.1  # 微小な時間経過を考慮
        
        # 5 トークン取得
        assert bucket.try_acquire(5) is True
        assert 3.9 <= bucket.tokens <= 4.1  # 微小な時間経過を考慮
    
    def test_try_acquire_failure(self):
        """try_acquire: トークンが不足している場合"""
        bucket = TokenBucket(capacity=5, refill_period=1.0)
        
        # 全トークンを消費
        assert bucket.try_acquire(5) is True
        assert bucket.tokens <= 0.1  # 微小な時間経過を考慮
        
        # 追加のトークン取得失敗
        assert bucket.try_acquire(1) is False
        assert bucket.tokens <= 0.2  # 微小な時間経過を考慮
    
    def test_try_acquire_exceeds_capacity(self):
        """try_acquire: 容量を超えるトークン要求"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)
        assert bucket.try_acquire(11) is False
        assert bucket.tokens == 10.0  # トークンは消費されない
    
    @pytest.mark.asyncio
    async def test_acquire_immediate(self):
        """acquire: トークンが十分ある場合（即座に取得）"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)
        
        # 待機なしで取得できる
        start = time.monotonic()
        await bucket.acquire(5)
        elapsed = time.monotonic() - start
        
        assert elapsed < 0.1  # ほぼ即座
        assert bucket.tokens == 5.0
    
    @pytest.mark.asyncio
    async def test_acquire_with_wait(self):
        """acquire: トークン不足で待機が必要な場合"""
        bucket = TokenBucket(capacity=2, refill_period=1.0)
        
        # 全トークンを消費
        await bucket.acquire(2)
        assert bucket.tokens == 0.0
        
        # 追加トークンを要求（待機が必要）
        start = time.monotonic()
        await bucket.acquire(1)
        elapsed = time.monotonic() - start
        
        # 0.5 秒程度待機するはず（許容誤差を考慮）
        assert 0.4 < elapsed < 0.6
    
    @pytest.mark.asyncio
    async def test_acquire_exceeds_capacity(self):
        """acquire: 容量を超えるトークン要求"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)
        
        with pytest.raises(ValueError, match="Cannot acquire 11 tokens from bucket with capacity 10"):
            await bucket.acquire(11)
    
    def test_refill_logic(self):
        """トークン補充ロジックのテスト"""
        bucket = TokenBucket(capacity=10, refill_period=2.0)  # 5 tokens/s
        
        # 初期状態
        assert bucket.tokens == 10.0
        
        # 5 トークン消費
        bucket.try_acquire(5)
        assert bucket.tokens == 5.0
        
        # モック時間を進める
        with patch('time.monotonic') as mock_time:
            mock_time.return_value = bucket.last_refill + 1.0
            
            # refill をトリガー
            bucket._refill()
            
            # 1 秒で 5 トークン補充されるはず
            assert bucket.tokens == 10.0  # 容量上限でキャップ
    
    def test_refill_partial(self):
        """部分的なトークン補充のテスト"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)  # 10 tokens/s
        
        # 8 トークン消費
        bucket.try_acquire(8)
        assert bucket.tokens == 2.0
        
        # モック時間を 0.5 秒進める
        with patch('time.monotonic') as mock_time:
            mock_time.return_value = bucket.last_refill + 0.5
            
            # refill をトリガー
            bucket._refill()
            
            # 0.5 秒で 5 トークン補充
            assert bucket.tokens == 7.0
    
    def test_get_wait_time(self):
        """待機時間計算のテスト"""
        bucket = TokenBucket(capacity=10, refill_period=2.0)  # 5 tokens/s
        
        # 即座に取得可能
        assert bucket.get_wait_time(5) == 0.0
        
        # 全トークン消費
        bucket.try_acquire(10)
        
        # 1 トークンには 0.2 秒必要
        wait_time = bucket.get_wait_time(1)
        assert abs(wait_time - 0.2) < 0.01
        
        # 5 トークンには 1 秒必要
        wait_time = bucket.get_wait_time(5)
        assert abs(wait_time - 1.0) < 0.01
        
        # 容量超過
        assert bucket.get_wait_time(11) is None
    
    @pytest.mark.asyncio
    async def test_concurrent_acquire(self):
        """並行アクセスのテスト"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)
        results = []
        
        async def acquire_tokens(n):
            await bucket.acquire(n)
            results.append(n)
        
        # 並行して複数のタスクがトークンを取得
        tasks = [
            acquire_tokens(3),
            acquire_tokens(3),
            acquire_tokens(3),
        ]
        
        await asyncio.gather(*tasks)
        
        # 全タスクが正常に完了
        assert len(results) == 3
        assert sum(results) == 9
        assert 0.9 <= bucket.tokens <= 1.1  # 10 - 9 = 1（微小な時間経過を考慮）
    
    def test_available_tokens_property(self):
        """available_tokens プロパティのテスト"""
        bucket = TokenBucket(capacity=10, refill_period=1.0)
        
        assert 9.9 <= bucket.available_tokens <= 10.0
        
        bucket.try_acquire(3)
        assert 6.9 <= bucket.available_tokens <= 7.1
        
        # 時間経過をシミュレート
        with patch('time.monotonic') as mock_time:
            mock_time.return_value = bucket.last_refill + 0.5
            
            # プロパティアクセス時に自動的に refill される
            tokens = bucket.available_tokens
            assert tokens == 10.0  # 7 + 5 = 12 だが容量でキャップ