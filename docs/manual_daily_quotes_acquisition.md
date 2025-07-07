# 手動株価データ取得タスク実行手順書

## 概要

J-Quants APIから手動で株価データ（日次株価）を取得し、データベースに同期するための手順を説明します。本システムは**Docker環境前提**で構築されており、複数の実行方法が用意されています。

## 前提条件

### 必要な環境
- Docker & Docker Compose
- J-Quants API アカウント（メールアドレス・パスワード）
- 企業マスタデータが同期済みであること

### 事前準備
```bash
# 1. Docker環境の起動（全サービス起動）
docker-compose up -d

# 2. データベースマイグレーション（Dockerコンテナ内で実行）
docker-compose exec web alembic upgrade head

# 3. 企業マスタデータの同期確認
docker-compose exec db psql -U postgres -d stockura -c "SELECT COUNT(*) FROM companies WHERE is_active = true;"

# 4. サービス状態確認
docker-compose ps
```

**起動されるサービス**:
- `web`: FastAPIアプリケーション (ポート8000)
- `worker`: Celeryワーカー
- `db`: PostgreSQL (ポート5432)
- `redis`: Redis (ポート6379)
- `flower`: Celery監視ツール (ポート5555)

## 実行方法一覧

### 方法1: テストスクリプトによる手動実行（推奨）

**概要**: 開発・テスト用に作成された専用スクリプトを使用した最も簡単な方法

**実行手順**:
```bash
# Dockerコンテナ内でスクリプト実行
docker-compose exec web python test_daily_quotes_sync.py
```

**実行内容**:
1. J-Quants API接続テスト
2. サンプルデータ取得テスト（特定銘柄の株価）
3. 株価データ同期実行（指定期間のデータ）
4. データベース検索テスト

**メリット**:
- ✅ 一連の処理が自動実行される
- ✅ 各ステップごとの結果確認が可能
- ✅ エラー時の詳細な情報表示
- ✅ 初心者にも分かりやすい

**実行時間**: 約5-20分（対象銘柄数と期間による）

### 方法2: Python直接実行

**概要**: Pythonコードを直接記述して実行する方法

**実行手順**:
```bash
# 1. 一時的なPythonファイルを作成
docker-compose exec web bash -c 'cat > manual_daily_sync.py << EOF
import asyncio
from datetime import date, timedelta
from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.daily_quotes_sync_service import DailyQuotesSyncService

# 認証ストラテジーを登録
from app.services.auth import StrategyRegistry
from app.services.auth.strategies.jquants_strategy import JQuantsStrategy
StrategyRegistry.register("jquants", JQuantsStrategy)

async def manual_sync():
    async with async_session_maker() as db:
        # サービス初期化
        data_source_service = DataSourceService(db)
        client_manager = JQuantsClientManager(data_source_service)
        sync_service = DailyQuotesSyncService(data_source_service, client_manager)
        
        # 同期実行（過去7日間のデータ）
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        sync_history = await sync_service.sync_daily_quotes(
            data_source_id=1,
            sync_type="date_range",
            from_date=start_date,
            to_date=end_date
        )
        
        await db.commit()
        
        print(f"同期完了 - ステータス: {sync_history.status}")
        print(f"対象期間: {sync_history.start_date} ~ {sync_history.end_date}")
        print(f"総レコード数: {sync_history.total_records}")
        print(f"新規: {sync_history.new_records}, 更新: {sync_history.updated_records}")

# 実行
asyncio.run(manual_sync())
EOF'

# 2. 作成したスクリプトを実行
docker-compose exec web python manual_daily_sync.py

# 3. 一時ファイルを削除
docker-compose exec web rm manual_daily_sync.py
```

**メリット**:
- 🔧 カスタマイズが可能
- 🔧 必要な期間のみ実行可能

### 方法3: Celeryタスクによる実行

**概要**: バックグラウンドタスクとして実行する方法（Dockerコンテナで既に起動済み）

**確認**:
```bash
# Celeryワーカーが起動中か確認
docker-compose ps worker

# Celeryワーカーのログ確認
docker-compose logs worker
```

**実行手順**:
```bash
# Dockerコンテナ内でCeleryタスクを実行
docker-compose exec web python -c "
from app.tasks.daily_quotes_tasks import sync_daily_quotes_task
from datetime import date, timedelta

# 過去7日間のデータを同期
end_date = date.today()
start_date = end_date - timedelta(days=7)

# タスクをキューに送信
result = sync_daily_quotes_task.delay(
    data_source_id=1,
    sync_type='date_range',
    from_date=start_date.isoformat(),
    to_date=end_date.isoformat()
)

# 結果を取得（ブロッキング）
sync_result = result.get()
print(f'同期結果: {sync_result}')
"
```

**Celery監視ツール（Flower）**:
```bash
# ブラウザでCeleryタスクの状況を監視
# http://localhost:5555 にアクセス
```

**メリット**:
- 🚀 バックグラウンド実行
- 📊 進捗管理が可能
- 🔄 リトライ機能あり

### 方法4: REST API経由での実行

**概要**: FastAPI経由でHTTP APIとして実行（Dockerコンテナで既に起動済み）

**確認**:
```bash
# FastAPIサーバーが起動中か確認
docker-compose ps web

# FastAPIサーバーのログ確認
docker-compose logs web

# APIが利用可能か確認
curl http://localhost:8000/health
```

**実行手順**:
```bash
# API経由で同期実行（過去7日間）
curl -X POST "http://localhost:8000/api/v1/daily-quotes/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "sync_type": "date_range",
    "from_date": "'$(date -v-7d +%Y-%m-%d)'",
    "to_date": "'$(date +%Y-%m-%d)'"
  }'

# 特定日のデータのみ同期
curl -X POST "http://localhost:8000/api/v1/daily-quotes/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "sync_type": "single_date",
    "target_date": "'$(date +%Y-%m-%d)'"
  }'

# 特定銘柄のデータのみ同期
curl -X POST "http://localhost:8000/api/v1/daily-quotes/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "sync_type": "by_code",
    "codes": ["72030", "67580"],
    "from_date": "'$(date -v-30d +%Y-%m-%d)'",
    "to_date": "'$(date +%Y-%m-%d)'"
  }'
```

**API ドキュメント**:
```bash
# ブラウザでAPI仕様を確認
# http://localhost:8000/docs にアクセス（Swagger UI）
# http://localhost:8000/redoc にアクセス（ReDoc）
```

**メリット**:
- 🌐 Web UIから実行可能
- 📡 外部システムからの呼び出し可能

## データソース情報

### J-Quantsデータソース設定
データソースID `1` がJ-Quants APIに設定されています。

**設定確認方法**:
```bash
# Dockerコンテナ内でデータベースに接続してデータソース確認
docker-compose exec db psql -U postgres -d stockura -c "
SELECT id, name, provider_type, base_url, is_enabled 
FROM data_sources 
WHERE provider_type = 'jquants';
"
```

## 同期パラメータ詳細

### sync_type オプション
- **`"full"`**: 全期間の完全同期（大量データ注意）
- **`"date_range"`**: 指定期間のデータ同期（推奨）
- **`"single_date"`**: 特定日のデータのみ同期
- **`"by_code"`**: 特定銘柄のデータのみ同期

### 実行タイミング
- **初回**: `"date_range"`で過去1ヶ月程度のデータ同期
- **日次**: `"single_date"`で当日データ更新
- **週次**: `"date_range"`で過去1週間のデータ再同期（修正データ対応）

## 取得されるデータ

### 株価情報
- 銘柄コード
- 取引日
- 始値（円）
- 高値（円）
- 安値（円）
- 終値（円）
- 出来高（株）
- 売買代金（円）
- 調整後終値（円）
- 調整係数

### データ更新タイミング
- J-Quants APIは通常、取引日の18:00頃にデータが更新されます
- 土日祝日は取引がないため、データは更新されません

## エラー対処法

### よくあるエラーとその対処

#### 1. J-Quants API認証エラー
**エラー**: `Authentication failed`

**対処法**:
```bash
# 認証情報を確認
docker-compose exec db psql -U postgres -d stockura -c "SELECT * FROM data_sources WHERE id = 1;"

# トークンの有効期限を確認
docker-compose exec web python -c "
from app.services.token_manager import TokenManager
import asyncio

async def check_token():
    manager = TokenManager()
    token_info = await manager.get_token_info('jquants', 1)
    print(f'Token expires at: {token_info.get(\"expires_at\")}')

asyncio.run(check_token())
"
```

#### 2. データベース接続エラー
**エラー**: `Connection refused`

**対処法**:
```bash
# Dockerコンテナの状態確認
docker-compose ps

# PostgreSQLコンテナの再起動
docker-compose restart db
```

#### 3. レート制限エラー
**エラー**: `Rate limit exceeded`

**対処法**:
- しばらく待ってから再実行
- J-Quantsのプランを確認
- 同期対象を絞って実行（特定銘柄や期間を限定）

#### 4. メモリ不足エラー
**エラー**: `Memory error`

**対処法**:
```bash
# Dockerのメモリ制限を拡張
# docker-compose.ymlを編集してmem_limitを追加

# または、バッチサイズを小さくして実行
docker-compose exec web python -c "
# 環境変数でバッチサイズを調整
import os
os.environ['DAILY_QUOTES_BATCH_SIZE'] = '100'
# その後、同期処理を実行
"
```

## 監視・確認方法

### 同期状況の確認
```bash
# 最新の同期履歴を確認
docker-compose exec db psql -U postgres -d stockura -c "
SELECT 
    id, sync_type, status, 
    start_date, end_date,
    total_records, new_records, updated_records,
    started_at, completed_at, error_message
FROM daily_quotes_sync_history 
ORDER BY started_at DESC 
LIMIT 5;
"
```

### 株価データの確認
```bash
# 株価データ件数の確認
docker-compose exec db psql -U postgres -d stockura -c "
SELECT COUNT(*) as total_quotes FROM daily_quotes;
"

# 最新の株価データ確認（トヨタ自動車）
docker-compose exec db psql -U postgres -d stockura -c "
SELECT 
    dq.trade_date, dq.open, dq.high, dq.low, dq.close, dq.volume
FROM daily_quotes dq
JOIN companies c ON dq.code = c.code
WHERE c.company_name LIKE '%トヨタ自動車%'
ORDER BY dq.trade_date DESC
LIMIT 10;
"

# 日付別のデータ件数
docker-compose exec db psql -U postgres -d stockura -c "
SELECT trade_date, COUNT(*) as quote_count
FROM daily_quotes
GROUP BY trade_date
ORDER BY trade_date DESC
LIMIT 10;
"
```

### ログの確認
```bash
# Webアプリケーションログ
docker-compose logs -f web

# Celeryワーカーログ
docker-compose logs -f worker

# 全サービスのログ
docker-compose logs -f

# PostgreSQLログ
docker-compose logs -f db

# Redisログ
docker-compose logs -f redis
```

## パフォーマンス最適化

### 大量データ処理時の推奨設定
```python
# バッチサイズの調整
BATCH_SIZE = 500  # 一度に処理する銘柄数

# 同時接続数の制限
MAX_CONCURRENT_REQUESTS = 3  # J-Quants APIへの同時リクエスト数

# 期間を分割して処理
MAX_DAYS_PER_REQUEST = 30  # 一度に取得する最大日数
```

### キャッシュの活用
```python
# Redisキャッシュを有効活用
USE_CACHE = True
CACHE_TTL = 3600  # 1時間
```

## セキュリティ注意事項

### 認証情報の管理
- J-Quants APIの認証情報は暗号化して保存
- トークンは自動更新されるが、定期的な確認を推奨
- 定期的なパスワード変更を推奨

### アクセス制御
- API実行権限の適切な設定
- ログ監視の実施
- 異常なアクセスパターンの検知

## トラブルシューティング

### 完全リセット手順
```bash
# 1. 株価データの全削除
docker-compose exec db psql -U postgres -d stockura -c "TRUNCATE daily_quotes, daily_quotes_sync_history RESTART IDENTITY;"

# 2. Redisキャッシュのクリア
docker-compose exec redis redis-cli FLUSHDB

# 3. 再同期実行
docker-compose exec web python test_daily_quotes_sync.py
```

### データ整合性チェック
```bash
# 外部キー制約違反のチェック
docker-compose exec db psql -U postgres -d stockura -c "
SELECT dq.code, dq.trade_date
FROM daily_quotes dq
LEFT JOIN companies c ON dq.code = c.code
WHERE c.code IS NULL
LIMIT 10;
"

# 重複データのチェック
docker-compose exec db psql -U postgres -d stockura -c "
SELECT code, trade_date, COUNT(*) as count
FROM daily_quotes
GROUP BY code, trade_date
HAVING COUNT(*) > 1
LIMIT 10;
"

# データ欠損のチェック（営業日のみ）
docker-compose exec db psql -U postgres -d stockura -c "
WITH date_series AS (
    SELECT generate_series(
        (SELECT MIN(trade_date) FROM daily_quotes),
        (SELECT MAX(trade_date) FROM daily_quotes),
        '1 day'::interval
    )::date AS date
),
trading_days AS (
    SELECT DISTINCT trade_date FROM daily_quotes
)
SELECT ds.date
FROM date_series ds
LEFT JOIN trading_days td ON ds.date = td.trade_date
WHERE td.trade_date IS NULL
  AND EXTRACT(DOW FROM ds.date) BETWEEN 1 AND 5  -- 平日のみ
ORDER BY ds.date DESC
LIMIT 10;
"
```

## 定期実行の設定（オプション）

### Crontabでの定期実行
```bash
# ホストマシンのcrontabを編集
crontab -e

# 平日の19時に自動実行（Docker経由）
0 19 * * 1-5 cd /path/to/stockura.jp && docker-compose exec -T web python test_daily_quotes_sync.py > logs/daily_quotes_sync.log 2>&1
```

### Celery Beatでのスケジュール実行
```python
# app/core/celery_config.py
CELERYBEAT_SCHEDULE = {
    'daily-quotes-sync': {
        'task': 'app.tasks.daily_quotes_tasks.sync_daily_quotes_task',
        'schedule': crontab(hour=19, minute=0, day_of_week='1-5'),  # 平日19時
        'args': ([1],),  # J-QuantsデータソースID
        'kwargs': {
            'sync_type': 'single_date',
            'target_date': None  # Noneで当日
        }
    },
}
```

## まとめ

**Docker環境前提**での手動株価データ取得の最も簡単で推奨される方法は、**方法1のテストスクリプト実行**です：

```bash
# 1. Docker環境起動
docker-compose up -d

# 2. データベースマイグレーション
docker-compose exec web alembic upgrade head

# 3. 企業マスタが未同期の場合は先に同期
docker-compose exec web python test_jquants_sync.py

# 4. 株価データ同期実行
docker-compose exec web python test_daily_quotes_sync.py
```

このスクリプトは：
- ✅ 接続テストから実際の同期まで一貫して実行
- ✅ 詳細な進捗表示とエラーハンドリング
- ✅ 結果の分かりやすい表示
- ✅ Docker環境で安全に実行可能

**実行時間**: 初回は過去1ヶ月分のデータ取得のため10-30分程度

**監視ツール**:
- Celery監視: http://localhost:5555 (Flower)
- API仕様: http://localhost:8000/docs (Swagger UI)
- アプリケーション: http://localhost:8000

**注意事項**:
- 企業マスタデータが同期済みであることが前提
- J-Quants APIの更新は通常18:00頃のため、19:00以降の実行を推奨
- 大量データの同期は負荷が高いため、期間を区切って実行することを推奨