# JQuantsクライアントのクリーンアーキテクチャ化 - 設計書

## 1. アーキテクチャ概要

### 1.1 レイヤー構成

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  (CompanySyncService, DailyQuotesSyncService)                  │
├─────────────────────────────────────────────────────────────────┤
│                      Domain Layer                                │
│  (Interfaces, DTOs, Exceptions)                                 │
├─────────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │  HTTP Client    │  │ Authentication  │  │ Rate Limiter   │ │
│  │  Abstraction   │  │    Service      │  │   Service      │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              JQuants API Implementation                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 主要コンポーネント

1. **Domain Layer**
   - `IAPIClient`: API通信の抽象インターフェース
   - `IAuthenticationService`: 認証サービスインターフェース
   - `IRateLimiter`: レート制限インターフェース
   - DTOクラス: データ転送オブジェクト
   - カスタム例外クラス

2. **Infrastructure Layer**
   - `HTTPClient`: httpxを使用した汎用HTTPクライアント
   - `JQuantsAPIClient`: J-Quants API固有の実装
   - `AuthenticationService`: トークン管理の実装
   - `RateLimiter`: レート制限の実装
   - `RetryHandler`: リトライ機構の実装

## 2. インターフェース設計

### 2.1 IAPIClient インターフェース

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import date

class IAPIClient(ABC):
    """API通信の抽象インターフェース"""
    
    @abstractmethod
    async def get_listed_companies(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """上場企業情報を取得"""
        pass
    
    @abstractmethod
    async def get_daily_quotes(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """日次株価データを取得"""
        pass
```

### 2.2 IAuthenticationService インターフェース

```python
class IAuthenticationService(ABC):
    """認証サービスインターフェース"""
    
    @abstractmethod
    async def get_access_token(self) -> str:
        """有効なアクセストークンを取得"""
        pass
    
    @abstractmethod
    async def refresh_token(self) -> str:
        """トークンをリフレッシュ"""
        pass
```

### 2.3 IRateLimiter インターフェース

```python
class IRateLimiter(ABC):
    """レート制限インターフェース"""
    
    @abstractmethod
    async def check_rate_limit(self) -> bool:
        """レート制限をチェック"""
        pass
    
    @abstractmethod
    async def wait_if_needed(self) -> None:
        """必要に応じて待機"""
        pass
```

## 3. データ転送オブジェクト (DTO)

### 3.1 企業情報DTO

```python
@dataclass
class CompanyInfoDTO:
    """企業情報DTO"""
    code: str
    company_name: str
    company_name_english: Optional[str]
    sector17_code: Optional[str]
    sector17_code_name: Optional[str]
    sector33_code: Optional[str]
    sector33_code_name: Optional[str]
    scale_category: Optional[str]
    market_code: Optional[str]
    market_code_name: Optional[str]
```

### 3.2 株価データDTO

```python
@dataclass
class DailyQuoteDTO:
    """日次株価DTO"""
    code: str
    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]
    turnover_value: Optional[float]
    adjustment_factor: Optional[float]
    adjustment_open: Optional[float]
    adjustment_high: Optional[float]
    adjustment_low: Optional[float]
    adjustment_close: Optional[float]
    adjustment_volume: Optional[float]
```

## 4. エラーハンドリング設計

### 4.1 カスタム例外クラス

```python
class JQuantsAPIException(Exception):
    """J-Quants API基底例外"""
    pass

class AuthenticationError(JQuantsAPIException):
    """認証エラー"""
    pass

class RateLimitError(JQuantsAPIException):
    """レート制限エラー"""
    pass

class NetworkError(JQuantsAPIException):
    """ネットワークエラー"""
    pass

class DataValidationError(JQuantsAPIException):
    """データ検証エラー"""
    pass
```

### 4.2 エラーハンドリング戦略

1. **リトライ可能なエラー**
   - ネットワークタイムアウト
   - 一時的なサーバーエラー (5xx)
   - レート制限エラー

2. **リトライ不可能なエラー**
   - 認証エラー (401)
   - 権限エラー (403)
   - データ検証エラー (400)

## 5. リトライ機構設計

### 5.1 リトライ設定

```python
@dataclass
class RetryConfig:
    """リトライ設定"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
```

### 5.2 指数バックオフ実装

```python
class ExponentialBackoff:
    """指数バックオフ戦略"""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """遅延時間を計算"""
        delay = min(
            config.initial_delay * (config.exponential_base ** attempt),
            config.max_delay
        )
        if config.jitter:
            delay *= random.uniform(0.5, 1.5)
        return delay
```

## 6. 実装の詳細設計

### 6.1 HTTPClient クラス

```python
class HTTPClient:
    """汎用HTTPクライアント"""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self._session: Optional[httpx.AsyncClient] = None
    
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """HTTPリクエストを実行（リトライ機能付き）"""
        # 実装詳細...
```

### 6.2 JQuantsAPIClient クラス

```python
class JQuantsAPIClient(IAPIClient):
    """J-Quants API実装"""
    
    def __init__(
        self,
        http_client: HTTPClient,
        auth_service: IAuthenticationService,
        rate_limiter: IRateLimiter
    ):
        self.http_client = http_client
        self.auth_service = auth_service
        self.rate_limiter = rate_limiter
    
    async def get_listed_companies(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> List[CompanyInfoDTO]:
        """上場企業情報を取得"""
        # レート制限チェック
        await self.rate_limiter.wait_if_needed()
        
        # 認証トークン取得
        token = await self.auth_service.get_access_token()
        
        # APIリクエスト
        response = await self.http_client.request(
            "GET",
            "/v1/listed/info",
            headers={"Authorization": f"Bearer {token}"},
            params=self._build_params(code, target_date)
        )
        
        # レスポンス変換
        return self._parse_company_response(response)
```

## 7. 依存性注入の設計

### 7.1 ファクトリーパターン

```python
class JQuantsClientFactory:
    """JQuantsクライアントのファクトリー"""
    
    @staticmethod
    async def create(
        data_source_service: DataSourceService,
        data_source_id: int
    ) -> IAPIClient:
        """クライアントインスタンスを生成"""
        # データソース情報取得
        data_source = await data_source_service.get_data_source(data_source_id)
        
        # 各コンポーネントを生成
        http_client = HTTPClient(
            base_url=data_source.base_url,
            retry_config=RetryConfig()
        )
        
        auth_service = JQuantsAuthenticationService(
            data_source_service=data_source_service,
            data_source_id=data_source_id
        )
        
        rate_limiter = JQuantsRateLimiter(
            requests_per_minute=data_source.rate_limit_per_minute
        )
        
        # クライアントを組み立て
        return JQuantsAPIClient(
            http_client=http_client,
            auth_service=auth_service,
            rate_limiter=rate_limiter
        )
```

## 8. 既存システムとの統合

### 8.1 移行戦略

1. **Phase 1**: 新しいクライアントを並行実装
2. **Phase 2**: フィーチャーフラグで段階的切り替え
3. **Phase 3**: 旧実装の削除

### 8.2 後方互換性の維持

```python
class JQuantsClientManager:
    """後方互換性を保つマネージャー"""
    
    def __init__(self, data_source_service: DataSourceService):
        self.data_source_service = data_source_service
        self._clients: Dict[int, IAPIClient] = {}
        self._use_new_implementation = True  # フィーチャーフラグ
    
    async def get_client(self, data_source_id: int) -> IAPIClient:
        """クライアントを取得（新旧切り替え可能）"""
        if self._use_new_implementation:
            return await self._get_new_client(data_source_id)
        else:
            return await self._get_legacy_client(data_source_id)
```

## 9. テスト設計

### 9.1 ユニットテスト

- 各インターフェースのモック実装
- 個別コンポーネントのテスト
- エラーケースのテスト

### 9.2 統合テスト

- 実際のAPIとの統合テスト
- エンドツーエンドのシナリオテスト
- パフォーマンステスト

## 10. パフォーマンス最適化

### 10.1 コネクションプーリング

- httpxのコネクションプール設定
- Keep-Aliveの活用

### 10.2 非同期処理の最適化

- 並行リクエストの制御
- バッチ処理の実装

### 10.3 キャッシュ戦略（オプション）

- 短期間のレスポンスキャッシュ
- キャッシュ無効化戦略