# API レートリミット実装ガイド

## 概要

j-Quants と yfinance の API クライアントに対して、 API 単位でのレート制限機能を実装しました。この実装により、 API プロバイダーのレート制限を遵守し、安定したデータ取得が可能になります。

## アーキテクチャ

### 主要コンポーネント

1. **TokenBucketRateLimiter** - Redis ベースのトークンバケットアルゴリズム実装
2. **InMemoryRateLimiter** - 開発/テスト用のインメモリ実装
3. **RateLimitedHTTPClient** - レート制限機能付き HTTP クライアント
4. **YFinanceClient** - yfinance 用のレート制限付きラッパー

### レート制限設定

- **j-Quants**: 10 リクエスト/分
- **yfinance**: 30 リクエスト/分

## 使用方法

### j-Quants クライアント

```python
from app.infrastructure.rate_limiting import RateLimiterFactory
from app.infrastructure.jquants import JQuantsClientFactory

# データソースからレートリミッターを作成
rate_limiter = await RateLimiterFactory.create_for_data_source(data_source)

# レート制限付き HTTP クライアントを使用して j-Quants クライアントを作成
# (JQuantsClientFactory で自動的に適用されます)
client = await JQuantsClientFactory.create(
    data_source_service=data_source_service,
    data_source_id=data_source_id
)

# API コールは自動的にレート制限される
companies = await client.get_listed_companies()
```

### yfinance クライアント

```python
from app.infrastructure.yfinance import YFinanceClient
from app.infrastructure.rate_limiting import RateLimiterFactory

# プロバイダー用のレートリミッターを作成
rate_limiter = await RateLimiterFactory.create_for_provider("yfinance")

# レート制限付き yfinance クライアントを作成
yf_client = YFinanceClient(rate_limiter)

# API コールは自動的にレート制限される
history = await yf_client.get_history("AAPL", period="1mo")
ticker_info = await yf_client.get_ticker_info("AAPL")
```

## 実装詳細

### トークンバケットアルゴリズム

- **容量**: レート制限の 2 倍（バースト対応）
- **補充レート**: 設定されたレート制限に基づく
- **待機**: トークンが不足している場合、自動的に待機

### Redis 統合

```python
# Lua スクリプトによるアトミック操作
- トークンの確認と消費を 1 つのアトミック操作で実行
- 複数のワーカー間でのレート制限を共有
- TTL 設定により古いデータを自動削除
```

### 環境変数設定

```bash
# Redis レートリミッターの使用を制御
USE_REDIS_RATE_LIMITER=true  # 本番環境
USE_REDIS_RATE_LIMITER=false # 開発/テスト環境
```

## テスト

```bash
# レート制限のテストを実行
python -m pytest tests/unit/infrastructure/rate_limiting/ -v
```

## 注意事項

1. **Celery ワーカーとの連携**: API クライアントレベルのレート制限は、 Celery タスクレベルの制限と併用可能
2. **エラー処理**: API エラー時もレート制限のカウントに含まれる
3. **分散環境**: Redis 使用時は複数のプロセス/サーバー間でレート制限を共有

## 今後の拡張

1. **動的レート調整**: API レスポンスヘッダーからレート制限情報を取得
2. **優先度制御**: 重要なリクエストを優先的に処理
3. **メトリクス収集**: レート制限の使用状況を監視