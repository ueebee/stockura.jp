# 外部 API レートリミット機能の設計書

## 1. アーキテクチャ概要

### レイヤー構成
```
Infrastructure Layer
├── rate_limiter/
│   ├── __init__.py
│   ├── rate_limiter.py          # 共通レートリミッター実装
│   └── token_bucket.py          # トークンバケットアルゴリズム
├── external_services/
│   ├── jquants/
│   │   └── base_client.py       # レートリミッター統合
│   └── yfinance/
│       └── base_client.py       # レートリミッター統合
└── config/
    └── settings.py              # レート制限設定
```

### クリーンアーキテクチャとの整合性
- **Infrastructure レイヤー**にレートリミッターを配置
- Domain レイヤーや Application レイヤーには影響を与えない
- 外部サービスとの通信時のみ適用される技術的な制約として実装

## 2. 主要コンポーネント

### 2.1 RateLimiter クラス
```python
class RateLimiter:
    """API 横断で使用可能な汎用レートリミッター"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Args:
            max_requests: 時間窓内の最大リクエスト数
            window_seconds: 時間窓の長さ（秒）
        """
        self._token_bucket = TokenBucket(max_requests, window_seconds)
    
    async def acquire(self) -> None:
        """トークンを取得（必要に応じて待機）"""
        await self._token_bucket.acquire()
    
    def try_acquire(self) -> bool:
        """トークンの取得を試みる（待機なし）"""
        return self._token_bucket.try_acquire()
```

### 2.2 TokenBucket クラス
```python
class TokenBucket:
    """トークンバケットアルゴリズムの実装"""
    
    def __init__(self, capacity: int, refill_period: int):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_period = refill_period
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
```

### 2.3 デコレーターパターンによる統合
```python
def with_rate_limit(rate_limiter: RateLimiter):
    """レート制限を適用するデコレーター"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            await rate_limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

## 3. 設定管理

### 3.1 環境変数
```python
# infrastructure/config/settings.py
class RateLimitSettings(BaseSettings):
    """レート制限設定"""
    
    # J-Quants 設定
    jquants_max_requests: int = Field(default=100, env="JQUANTS_RATE_LIMIT_REQUESTS")
    jquants_window_seconds: int = Field(default=60, env="JQUANTS_RATE_LIMIT_WINDOW")
    
    # yfinance 設定
    yfinance_max_requests: int = Field(default=2000, env="YFINANCE_RATE_LIMIT_REQUESTS")
    yfinance_window_seconds: int = Field(default=3600, env="YFINANCE_RATE_LIMIT_WINDOW")
```

### 3.2 設定の統合
```python
class InfrastructureSettings(BaseSettings):
    # 既存の設定...
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
```

## 4. 各 API クライアントへの統合

### 4.1 JQuantsBaseClient
```python
class JQuantsBaseClient:
    def __init__(self, credentials: Optional[JQuantsCredentials] = None):
        self._credentials = credentials
        self._session: Optional[ClientSession] = None
        
        # レートリミッターの初期化
        settings = get_infrastructure_settings()
        self._rate_limiter = RateLimiter(
            max_requests=settings.rate_limit.jquants_max_requests,
            window_seconds=settings.rate_limit.jquants_window_seconds
        )
    
    @with_rate_limit(lambda self: self._rate_limiter)
    async def _request_with_retry(self, ...):
        # 既存の実装
```

### 4.2 YfinanceBaseClient
```python
class YfinanceBaseClient:
    def __init__(self):
        # レートリミッターの初期化
        settings = get_infrastructure_settings()
        self._rate_limiter = RateLimiter(
            max_requests=settings.rate_limit.yfinance_max_requests,
            window_seconds=settings.rate_limit.yfinance_window_seconds
        )
    
    @with_rate_limit(lambda self: self._rate_limiter)
    async def download_data(self, ...):
        # 既存の実装
```

## 5. ログ出力

### 5.1 ログメッセージ
```python
# レート制限の状態
logger.debug(f"Rate limiter status: {remaining_tokens}/{max_tokens} tokens available")

# 待機時の警告
logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")

# トークン補充
logger.debug(f"Refilled {refilled_tokens} tokens")
```

## 6. エラーハンドリング

### 6.1 基本方針
- フェーズ 1 では待機のみ実装（RateLimitError は投げない）
- 待機時間が異常に長い場合のみ警告ログを出力

## 7. テスト戦略

### 7.1 単体テスト
- TokenBucket クラスのロジックテスト
- RateLimiter クラスの待機動作テスト
- モック時計を使用した時間依存テスト

### 7.2 統合テスト
- JQuantsBaseClient でのレート制限動作確認
- YfinanceBaseClient でのレート制限動作確認

## 8. 実装の利点

### 8.1 共通化のメリット
- 同一のレートリミッター実装を両 API で使用
- 将来的な拡張（新しい API 追加）が容易
- テストコードの共有

### 8.2 非侵襲的な設計
- 既存のクライアントコードへの変更は最小限
- デコレーターによる透過的な適用
- ビジネスロジックに影響なし

## 9. 将来の拡張ポイント

### 9.1 フェーズ 2 での拡張
- エンドポイント単位のレート制限
- Redis を使った分散環境対応
- 指数バックオフの実装
- より詳細なメトリクス収集