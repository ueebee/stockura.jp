# 手動Company情報取得タスク実行手順書

## 概要

J-Quants APIから手動で上場企業情報を取得し、データベースに同期するための手順を説明します。本システムは**Docker環境前提**で構築されており、複数の実行方法が用意されています。

## 前提条件

### 必要な環境
- Docker & Docker Compose
- J-Quants API アカウント（メールアドレス・パスワード）

### 事前準備
```bash
# 1. Docker環境の起動（全サービス起動）
docker-compose up -d

# 2. データベースマイグレーション（Dockerコンテナ内で実行）
docker-compose exec web alembic upgrade head

# 3. サービス状態確認
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
docker-compose exec web python test_jquants_sync.py
```

**実行内容**:
1. J-Quants API接続テスト
2. サンプルデータ取得テスト（トヨタ自動車等）
3. 企業データ同期実行（全上場企業データ）
4. データベース検索テスト

**メリット**:
- ✅ 一連の処理が自動実行される
- ✅ 各ステップごとの結果確認が可能
- ✅ エラー時の詳細な情報表示
- ✅ 初心者にも分かりやすい

**実行時間**: 約10-30分（企業数による）

### 方法2: Python直接実行

**概要**: Pythonコードを直接記述して実行する方法

**実行手順**:
```bash
# 1. 一時的なPythonファイルを作成
docker-compose exec web bash -c 'cat > manual_sync.py << EOF
import asyncio
from datetime import date
from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.company_sync_service import CompanySyncService

# 認証ストラテジーを登録
from app.services.auth import StrategyRegistry
from app.services.auth.strategies.jquants_strategy import JQuantsStrategy
StrategyRegistry.register("jquants", JQuantsStrategy)

async def manual_sync():
    async with async_session_maker() as db:
        # サービス初期化
        data_source_service = DataSourceService(db)
        client_manager = JQuantsClientManager(data_source_service)
        sync_service = CompanySyncService(db, data_source_service, client_manager)
        
        # 同期実行（J-QuantsデータソースID: 1）
        sync_history = await sync_service.sync_companies(
            data_source_id=1,
            sync_type="full"
        )
        
        print(f"同期完了 - ステータス: {sync_history.status}")
        print(f"総企業数: {sync_history.total_companies}")
        print(f"新規: {sync_history.new_companies}, 更新: {sync_history.updated_companies}")

# 実行
asyncio.run(manual_sync())
EOF'

# 2. 作成したスクリプトを実行
docker-compose exec web python manual_sync.py

# 3. 一時ファイルを削除
docker-compose exec web rm manual_sync.py
```

**メリット**:
- 🔧 カスタマイズが可能
- 🔧 必要な部分のみ実行可能

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
from app.tasks.company_tasks import sync_companies_task

# タスクをキューに送信
result = sync_companies_task.delay(
    data_source_id=1,
    sync_date=None,  # Noneで当日
    sync_type='full'
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
# API経由で同期実行
curl -X POST "http://localhost:8000/api/v1/companies/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "sync_type": "full"
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
SELECT id, name, data_source_type, api_base_url, is_active 
FROM data_sources 
WHERE data_source_type = 'jquants';
"
```

## 同期パラメータ詳細

### sync_type オプション
- **`"full"`**: 全データの完全同期（推奨）
- **`"incremental"`**: 差分同期（実装予定）

### 実行タイミング
- **初回**: `"full"`で全データ同期
- **日次**: `"full"`で最新データ更新
- **リアルタイム**: `"incremental"`で差分更新（将来実装）

## 取得されるデータ

### 企業基本情報
- 銘柄コード（4桁）
- 会社名（日本語・英語）
- 業種分類（17業種・33業種）
- 市場区分
- 規模区分
- 信用区分

### マスターデータ
- 17業種マスター（18種類）
- 33業種マスター（34種類）
- 市場マスター（10種類）

## エラー対処法

### よくあるエラーとその対処

#### 1. J-Quants API認証エラー
**エラー**: `Authentication failed`

**対処法**:
```bash
# 認証情報を確認
docker-compose exec db psql -U postgres -d stockura -c "SELECT * FROM data_sources WHERE id = 1;"

# 必要に応じて認証情報を更新
docker-compose exec db psql -U postgres -d stockura -c "
UPDATE data_sources 
SET config = jsonb_set(config, '{email}', '\"your-email@example.com\"')
WHERE id = 1;
"
```

#### 2. データベース接続エラー
**エラー**: `Connection refused`

**対処法**:
```bash
# Dockerコンテナの状態確認
docker-compose ps

# PostgreSQLコンテナの再起動
docker-compose restart postgres
```

#### 3. レート制限エラー
**エラー**: `Rate limit exceeded`

**対処法**:
- しばらく待ってから再実行
- J-Quantsのプランを確認
- リトライ間隔を調整

#### 4. メモリ不足エラー
**エラー**: `Memory error`

**対処法**:
```bash
# Dockerのメモリ制限を拡張
# docker-compose.ymlを編集してmem_limitを追加
```

## 監視・確認方法

### 同期状況の確認
```bash
# 最新の同期履歴を確認
docker-compose exec db psql -U postgres -d stockura -c "
SELECT 
    id, sync_date, sync_type, status, 
    total_companies, new_companies, updated_companies,
    started_at, completed_at, error_message
FROM company_sync_history 
ORDER BY started_at DESC 
LIMIT 5;
"
```

### 企業データの確認
```bash
# 企業数の確認
docker-compose exec db psql -U postgres -d stockura -c "
SELECT COUNT(*) as total_companies FROM companies WHERE is_active = true;
"

# 市場別企業数
docker-compose exec db psql -U postgres -d stockura -c "
SELECT m.name as market_name, COUNT(*) as company_count
FROM companies c
JOIN market_masters m ON c.market_code = m.code
WHERE c.is_active = true
GROUP BY m.name, m.display_order
ORDER BY m.display_order;
"

# 業種別企業数（17業種）
docker-compose exec db psql -U postgres -d stockura -c "
SELECT s.name as sector_name, COUNT(*) as company_count
FROM companies c
JOIN sector17_masters s ON c.sector17_code = s.code
WHERE c.is_active = true
GROUP BY s.name, s.display_order
ORDER BY s.display_order;
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
BATCH_SIZE = 1000  # 一度に処理する企業数

# 同時接続数の制限
MAX_CONCURRENT_REQUESTS = 5  # J-Quants APIへの同時リクエスト数
```

### キャッシュの活用
```python
# Redisキャッシュを有効活用
USE_CACHE = True
CACHE_TTL = 3600  # 1時間
```

## セキュリティ注意事項

### 認証情報の管理
- J-Quants APIの認証情報は環境変数で管理
- データベースに平文で保存しない
- 定期的なパスワード変更を推奨

### アクセス制御
- API実行権限の適切な設定
- ログ監視の実施
- 異常なアクセスパターンの検知

## トラブルシューティング

### 完全リセット手順
```bash
# 1. 企業データの全削除
docker-compose exec db psql -U postgres -d stockura -c "TRUNCATE companies, company_sync_history RESTART IDENTITY;"

# 2. Redisキャッシュのクリア
docker-compose exec redis redis-cli FLUSHDB

# 3. 再同期実行
docker-compose exec web python test_jquants_sync.py
```

### データ整合性チェック
```bash
# 外部キー制約違反のチェック
docker-compose exec db psql -U postgres -d stockura -c "
SELECT c.code, c.company_name
FROM companies c
LEFT JOIN market_masters m ON c.market_code = m.code
WHERE c.market_code IS NOT NULL AND m.code IS NULL;
"

# 重複データのチェック
docker-compose exec db psql -U postgres -d stockura -c "
SELECT code, COUNT(*) as count
FROM companies
GROUP BY code
HAVING COUNT(*) > 1;
"
```

## 定期実行の設定（オプション）

### Crontabでの定期実行
```bash
# ホストマシンのcrontabを編集
crontab -e

# 平日の18時に自動実行（Docker経由）
0 18 * * 1-5 cd /path/to/stockura.jp && docker-compose exec -T web python test_jquants_sync.py > logs/daily_sync.log 2>&1
```

### Celery Beatでのスケジュール実行
```python
# app/core/celery_config.py
CELERYBEAT_SCHEDULE = {
    'daily-company-sync': {
        'task': 'app.tasks.company_tasks.daily_company_sync',
        'schedule': crontab(hour=18, minute=0, day_of_week='1-5'),  # 平日18時
        'args': ([1],)  # J-QuantsデータソースID
    },
}
```

## まとめ

**Docker環境前提**での手動Company情報取得の最も簡単で推奨される方法は、**方法1のテストスクリプト実行**です：

```bash
# 1. Docker環境起動
docker-compose up -d

# 2. データベースマイグレーション
docker-compose exec web alembic upgrade head

# 3. Company情報同期実行
docker-compose exec web python test_jquants_sync.py
```

このスクリプトは：
- ✅ 接続テストから実際の同期まで一貫して実行
- ✅ 詳細な進捗表示とエラーハンドリング
- ✅ 結果の分かりやすい表示
- ✅ Docker環境で安全に実行可能

**実行時間**: 初回は全上場企業データ（約3,000-4,000社）の取得のため10-30分程度

**監視ツール**:
- Celery監視: http://localhost:5555 (Flower)
- API仕様: http://localhost:8000/docs (Swagger UI)
- アプリケーション: http://localhost:8000