# Docker クイックスタートガイド

このガイドでは、 Stockura アプリケーションを Docker 環境で素早く起動し、動作確認を行う手順を説明します。

## 前提条件

- Docker Desktop がインストールされていること
- Docker Compose v2 以上がインストールされていること
- Git がインストールされていること

## クイックスタート（5 分で起動）

### 1. リポジトリのクローン

```bash
git clone https://github.com/ueebee/stockura.git
cd stockura
```

### 2. 環境変数の設定

```bash
# Docker 用の環境変数をコピー
cp .env.docker .env

# J-Quants API の認証情報を設定（必須）
# .env ファイルを編集して以下の値を設定：
# - JQUANTS_API_KEY=your-api-key
# - JQUANTS_EMAIL=your-email@example.com
# - JQUANTS_PASSWORD=your-password
```

### 3. Docker 環境の起動

```bash
# すべてのサービスを起動
make up

# または
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 4. データベースの初期化

```bash
# マイグレーションの実行
make migrate

# または
docker-compose exec app python scripts/db_migrate.py upgrade
```

### 5. 動作確認

以下の URL にアクセスして動作を確認：

- **API ドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/health
- **Flower（Celery 監視）**: http://localhost:5555

## 基本的な操作

### サービスの管理

```bash
# 起動
make up

# 停止
make down

# 再起動
make restart

# ログの確認
make logs

# 特定のサービスのログを確認
docker-compose logs -f app
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
```

### スケジュール登録のテスト

```bash
# 毎分実行するテストスケジュールを作成
curl -X POST http://localhost:8000/api/v1/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_schedule",
    "cron_expression": "* * * * *",
    "enabled": true,
    "description": "毎分実行するテスト",
    "task_params": {
      "period_type": "yesterday"
    }
  }'

# 登録されたスケジュールの確認
curl http://localhost:8000/api/v1/schedules/
```

### データベースへのアクセス

```bash
# PostgreSQL コンソールに接続
make shell-db

# SQL の実行例
SELECT * FROM celery_beat_schedules;
SELECT * FROM task_execution_logs ORDER BY started_at DESC LIMIT 5;
\q  # 終了
```

### コンテナ内での作業

```bash
# アプリケーションコンテナのシェルに接続
make shell

# Python シェルを起動
python

# タスクの手動実行例
from app.infrastructure.celery.tasks import fetch_listed_info_task_asyncpg
result = fetch_listed_info_task_asyncpg.delay(period_type="yesterday")
print(f"Task ID: {result.id}")
```

## トラブルシューティング

### コンテナが起動しない

```bash
# エラーログの確認
docker-compose logs app

# コンテナの状態確認
docker-compose ps -a

# 環境変数の確認
docker-compose config
```

### データベース接続エラー

```bash
# PostgreSQL が起動しているか確認
docker-compose ps postgres

# データベースが作成されているか確認
docker-compose exec postgres psql -U stockura -c '\l'
```

### Celery タスクが実行されない

```bash
# Redis の動作確認
docker-compose exec redis redis-cli ping

# Celery Worker の接続確認
docker-compose logs celery-worker | grep "Connected to"

# Celery Beat のスケジュール確認
docker-compose logs celery-beat | grep "Loaded"
```

## よくある質問

### Q: ポート 8000 が既に使用されている

A: 他のサービスがポート 8000 を使用している場合は、`docker-compose.dev.yml` の ports を変更してください：

```yaml
services:
  app:
    ports:
      - "8001:8000"  # 8001 に変更
```

### Q: メモリ不足エラーが発生する

A: Docker Desktop の設定でメモリ割り当てを増やしてください（推奨: 4GB 以上）

### Q: ホットリロードが効かない

A: 開発環境では自動的にホットリロードが有効になっています。ファイルを保存すると自動的に反映されます。

## 次のステップ

- [詳細な Docker セットアップガイド](./DOCKER_SETUP.md) を参照
- [テスト環境での実行方法](./DOCKER_TESTING.md) を確認
- [本番環境へのデプロイ](./DOCKER_PRODUCTION.md) について学ぶ