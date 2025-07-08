# Celeryレートリミット管理

## 概要

本システムでは、外部APIへのアクセスを適切に制御するため、Celeryのネイティブなレートリミット機能を活用しています。データソース（data_source）単位でレートリミットを管理することで、各APIプロバイダーの制限に従った安全なデータ取得を実現しています。

## アーキテクチャ

### 1. DataSourceモデル

`app/models/data_source.py`で定義されているDataSourceモデルには、レートリミット設定用のフィールドがあります：

```python
rate_limit_per_minute: int  # 分あたりの制限
rate_limit_per_hour: int    # 時間あたりの制限
rate_limit_per_day: int     # 日あたりの制限
```

### 2. RateLimitManager

`app/utils/rate_limit.py`で定義されているRateLimitManagerクラスが、データソースからレートリミット設定を取得します：

```python
# プロバイダータイプでレートリミットを取得
rate_limit = RateLimitManager.get_rate_limit_for_provider("jquants")
# => "10/m"

# データソースIDでレートリミットを取得
rate_limit = RateLimitManager.get_rate_limit_for_data_source(1)
# => "30/m"
```

### 3. Celery設定

`app/core/celery_app.py`で、各タスクにレートリミットを適用：

```python
task_annotations = {
    "app.tasks.daily_quotes_tasks.sync_daily_quotes_task": {
        "rate_limit": RateLimitManager.get_rate_limit_for_provider("jquants")
    },
}
```

## 使用方法

### 基本的な使い方

1. データソースのレートリミットを設定：

```sql
UPDATE data_sources 
SET rate_limit_per_minute = 10 
WHERE provider_type = 'jquants';
```

2. Celeryワーカーを再起動：

```bash
docker compose restart celery_worker
```

### カスタムデコレーターの使用

`app/utils/celery_decorators.py`のデコレーターを使用して、新しいタスクを作成：

```python
from app.utils.celery_decorators import data_source_rate_limited_task

@data_source_rate_limited_task(provider_type="jquants")
def my_jquants_task():
    # J-Quants APIを使用する処理
    pass
```

## 現在の設定

| プロバイダー | デフォルトレート | 説明 |
|------------|----------------|------|
| jquants    | 10/m          | J-Quants APIの制限に合わせて控えめに設定 |
| yfinance   | 30/m          | Yahoo Finance APIの一般的な制限 |
| その他      | 60/m          | デフォルト値 |

## 注意事項

### 1. ワーカーごとの制限

Celeryのレートリミットは**ワーカープロセスごと**に適用されます。複数のワーカーを起動している場合、実際のAPIコール数は以下のようになります：

```
実際のAPIコール数 = レートリミット × ワーカー数
```

例：`10/m`のレートリミットで4ワーカーの場合、最大40回/分のAPIコールが可能

### 2. 動的な変更の制限

Celeryのレートリミットはワーカー起動時に固定されるため、以下の制限があります：

- データベースのレートリミット設定を変更しても、ワーカー再起動まで反映されない
- 実行時に動的にレートリミットを変更することはできない

### 3. キューによる分離

異なるAPIプロバイダーのタスクは別々のキューで処理することを推奨：

```python
task_routes = {
    "app.tasks.stock_tasks.*": {"queue": "stock_data"},      # yfinance
    "app.tasks.company_tasks.*": {"queue": "jquants"},       # J-Quants
    "app.tasks.daily_quotes_tasks.*": {"queue": "jquants"},  # J-Quants
}
```

## モニタリング

### Flowerでの確認

Flowerを使用してタスクの実行状況を監視：

```bash
# Flowerにアクセス
http://localhost:5555

# タスクの実行レートを確認
# Tasks -> 対象のタスク -> Rate limit
```

### ログでの確認

レートリミットに達した場合、Celeryワーカーのログに以下のようなメッセージが出力されます：

```
Task app.tasks.daily_quotes_tasks.sync_daily_quotes_task 
is rate limited until 2024-01-20 12:34:56
```

## ベストプラクティス

1. **APIの制限を確認**：外部APIのドキュメントを確認し、適切なレートリミットを設定

2. **余裕を持った設定**：APIの制限ギリギリではなく、80%程度の余裕を持たせる

3. **エラーハンドリング**：レートリミットエラーが発生した場合のリトライ処理を実装

4. **モニタリング**：定期的にタスクの実行状況を確認し、必要に応じて調整

5. **テスト環境での検証**：本番環境に適用する前に、テスト環境で十分に検証

## トラブルシューティング

### レートリミットが効かない場合

1. ワーカーが再起動されているか確認
2. タスク名が正しく設定されているか確認
3. データソースのis_enabledがTrueになっているか確認

### APIエラーが頻発する場合

1. レートリミットをより厳しく設定
2. ワーカー数を減らす
3. リトライ間隔を長くする

## 今後の拡張案

### 1. 動的レートリミット（Redis活用）

現在のCeleryの制限を超えて、実行時に動的にレート制御を行う仕組み：

```python
# 案: カスタムレートリミッターの実装
class DynamicRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_and_increment(self, data_source_id: int) -> bool:
        """レート制限をチェックし、可能ならカウントをインクリメント"""
        key = f"rate_limit:{data_source_id}:{int(time.time() / 60)}"
        
        # データソースから現在のレート制限を取得
        limit = await self.get_current_limit(data_source_id)
        
        # Redisでカウントをチェック＆インクリメント
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 60)
        
        return current <= limit
```

### 2. 優先度ベースのタスク制御

重要度に応じてタスクの実行順序を制御：

```python
# 案: 優先度付きタスクキューの実装
CELERY_TASK_ROUTES = {
    # 高優先度：リアルタイムデータ
    "realtime_quotes_task": {"queue": "high_priority", "routing_key": "high"},
    
    # 中優先度：日次データ更新
    "daily_quotes_sync": {"queue": "normal_priority", "routing_key": "normal"},
    
    # 低優先度：バックフィル、過去データ
    "historical_backfill": {"queue": "low_priority", "routing_key": "low"},
}

# ワーカー起動時の優先度設定
# celery worker -Q high_priority,normal_priority,low_priority --max-tasks-per-child=100
```

### 3. APIレスポンスベースの自動調整

APIのレスポンスヘッダーやエラーから自動的にレート調整：

```python
# 案: 適応的レート制御
class AdaptiveRateLimiter:
    async def adjust_rate_based_on_response(self, response, data_source_id):
        # X-RateLimit-Remaining ヘッダーをチェック
        if 'X-RateLimit-Remaining' in response.headers:
            remaining = int(response.headers['X-RateLimit-Remaining'])
            if remaining < 10:
                # レートを一時的に下げる
                await self.temporary_reduce_rate(data_source_id, factor=0.5)
        
        # 429 Too Many Requests の場合
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', 60)
            await self.pause_data_source(data_source_id, int(retry_after))
```

### 4. 詳細なメトリクスとモニタリング

Prometheus/Grafanaと連携した高度な監視：

```python
# 案: メトリクス収集の実装
from prometheus_client import Counter, Histogram, Gauge

# メトリクス定義
task_executions = Counter('celery_task_executions_total', 
                         'Total task executions', 
                         ['task_name', 'data_source', 'status'])

api_call_duration = Histogram('api_call_duration_seconds',
                             'API call duration',
                             ['provider', 'endpoint'])

rate_limit_remaining = Gauge('rate_limit_remaining',
                           'Remaining rate limit',
                           ['data_source'])

# タスクデコレーターでメトリクス収集
@track_metrics
async def sync_quotes_with_metrics(data_source_id):
    # 実行時間とステータスを自動記録
    pass
```

### 5. インテリジェントなバックオフ戦略

エラー率に基づく賢いリトライ戦略：

```python
# 案: エクスポネンシャルバックオフ with ジッター
class IntelligentBackoff:
    def calculate_delay(self, attempt: int, error_rate: float) -> float:
        base_delay = 2 ** attempt
        jitter = random.uniform(0, base_delay * 0.1)
        
        # エラー率が高い場合は追加の遅延
        if error_rate > 0.5:
            base_delay *= 2
        
        return min(base_delay + jitter, 300)  # 最大5分
```

### 6. データソースのヘルスチェックと自動無効化

問題のあるデータソースを自動的に検出・無効化：

```python
# 案: ヘルスチェックシステム
class DataSourceHealthMonitor:
    async def monitor_health(self):
        for data_source in active_data_sources:
            error_rate = await self.calculate_error_rate(data_source.id)
            response_time = await self.get_avg_response_time(data_source.id)
            
            if error_rate > 0.8 or response_time > 30:
                await self.disable_data_source_temporarily(
                    data_source.id,
                    duration_minutes=30
                )
                await self.send_alert(data_source)
```

### 7. マルチテナント対応

組織やユーザーごとに異なるレート制限：

```python
# 案: テナント別レート制限
class TenantRateLimiter:
    def get_rate_limit(self, data_source_id: int, tenant_id: int) -> str:
        # プレミアムプランのテナントは高いレート
        if self.is_premium_tenant(tenant_id):
            return "100/m"
        
        # 無料プランは厳しい制限
        return "10/m"
```

### 8. レート制限の可視化ダッシュボード

管理者向けのリアルタイムダッシュボード：

```yaml
# 案: Grafanaダッシュボードの構成
dashboards:
  - name: "API Rate Limits Overview"
    panels:
      - title: "Current API Usage by Provider"
        type: graph
        query: "rate(api_calls_total[5m]) by (provider)"
      
      - title: "Rate Limit Utilization %"
        type: gauge
        query: "(api_calls_current / api_calls_limit) * 100"
      
      - title: "429 Errors by Data Source"
        type: table
        query: "increase(http_errors_total{status='429'}[1h])"
```

### 9. コスト最適化機能

API使用量とコストの追跡：

```python
# 案: コスト追跡システム
class APIUsageCostTracker:
    costs_per_call = {
        "jquants": 0.001,  # 仮の値
        "yfinance": 0.0,   # 無料
    }
    
    async def track_usage_and_cost(self, data_source, calls_count):
        monthly_cost = calls_count * self.costs_per_call.get(
            data_source.provider_type, 0
        )
        
        # 予算超過アラート
        if monthly_cost > data_source.monthly_budget:
            await self.send_budget_alert(data_source)
```

### 10. スマートキャッシング戦略

レート制限を考慮したインテリジェントなキャッシュ：

```python
# 案: レート制限対応キャッシュ
class RateLimitAwareCache:
    async def get_or_fetch(self, key: str, fetcher, data_source_id: int):
        # キャッシュをチェック
        cached = await self.redis.get(key)
        if cached:
            return cached
        
        # レート制限の余裕をチェック
        rate_limit_status = await self.check_rate_limit_headroom(data_source_id)
        
        if rate_limit_status.remaining_percent < 20:
            # レート制限に余裕がない場合は古いキャッシュでも使用
            stale_cache = await self.redis.get(f"{key}:stale")
            if stale_cache:
                return stale_cache
        
        # 新規取得
        data = await fetcher()
        await self.cache_with_ttl(key, data, ttl=3600)
        return data
```

これらの拡張案は、システムの成長に応じて段階的に実装することができます。各機能は独立して実装可能なため、ニーズに応じて優先順位を付けて開発を進めることができます。