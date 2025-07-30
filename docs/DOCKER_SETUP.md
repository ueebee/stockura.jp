# Docker 環境セットアップガイド

## 概要

Stockura アプリケーションは Docker 環境で実行することを推奨しています。このガイドでは、開発環境から本番環境まで、各種 Docker 環境のセットアップと使用方法について説明します。

## アーキテクチャ

### コンテナ構成

```
stockura-network
├── app (FastAPI アプリケーション)
├── postgres (PostgreSQL データベース)
├── redis (Redis キャッシュ)
├── celery-worker (Celery ワーカー)
├── celery-beat (Celery スケジューラー)
├── flower (Celery 監視ツール)
└── nginx (リバースプロキシ - 本番環境のみ)
```

### ポート構成

| サービス | 開発環境 | 本番環境 | 説明 |
|---------|---------|---------|------|
| FastAPI | 8000 | 8000 (内部) | API サーバー |
| PostgreSQL | 5432 | - | データベース |
| Redis | 6379 | - | キャッシュ・メッセージブローカー |
| Flower | 5555 | - | Celery 監視 UI |
| Nginx | - | 80/443 | リバースプロキシ |

## 開発環境

### 初回セットアップ

1. **環境変数の設定**
```bash
cp .env.docker .env
```

2. **必要な認証情報の設定**
`.env`ファイルを編集して、以下の値を設定してください：
- `JQUANTS_EMAIL`: J-Quants メールアドレス
- `JQUANTS_PASSWORD`: J-Quants パスワード

3. **開発環境の起動**
```bash
make up
# または
./scripts/docker/start-dev.sh
```

### 日常的な操作

#### サービスの起動・停止
```bash
# 起動
make up

# 停止
make down

# ログの確認
make logs
```

#### データベース操作
```bash
# マイグレーションの実行
make migrate

# PostgreSQL コンソールへの接続
make shell-db

# 新しいマイグレーションの作成
make migrate-create MSG="add new table"
```

#### デバッグ
```bash
# アプリケーションコンテナのシェルに接続
make shell

# Redis コンソールへの接続
make redis-cli

# Celery ワーカーのログ確認
docker-compose logs -f celery-worker
```

### ホットリロード

開発環境では、以下のディレクトリがボリュームマウントされており、ファイルの変更が即座に反映されます：
- `./app` → `/app/app`
- `./alembic` → `/app/alembic`
- `./scripts` → `/app/scripts`
- `./tests` → `/app/tests`

## テスト環境

### テストの実行

```bash
# Docker でテストを実行
make test

# または直接実行
./scripts/docker/run-tests.sh
```

### テスト環境の特徴

- 独立したデータベースと Redis インスタンス
- テスト実行後に自動的にクリーンアップ
- カバレッジレポートの生成（`htmlcov/`ディレクトリ）

## 本番環境

### 本番環境の構築

1. **本番用環境変数の設定**
```bash
cp .env.docker .env.prod
# .env.prod を編集して本番環境の設定を行う
```

2. **SSL 証明書の配置**（HTTPS 使用時）
```bash
mkdir -p docker/nginx/ssl
# cert.pem と key.pem を配置
```

3. **イメージのビルドと起動**
```bash
make prod-build
make prod-up
```

### 本番環境の特徴

- Gunicorn による複数ワーカープロセス
- Nginx によるリバースプロキシ
- 最適化された PostgreSQL と Redis 設定
- ヘルスチェックによる自動復旧

### バックアップとリストア

```bash
# PostgreSQL のバックアップ
docker-compose exec postgres pg_dump -U stockura stockura > backup.sql

# リストア
docker-compose exec -T postgres psql -U stockura stockura < backup.sql
```

## トラブルシューティング

### よくある問題と解決方法

1. **ポートが既に使用されている**
```bash
# 使用中のポートを確認
lsof -i :8000
# プロセスを終了するか、 docker-compose.yml でポートを変更
```

2. **データベース接続エラー**
```bash
# PostgreSQL の状態確認
docker-compose ps postgres
# ログの確認
docker-compose logs postgres
```

3. **Celery タスクが実行されない**
```bash
# Celery ワーカーの状態確認
docker-compose logs celery-worker
# Flower UI で確認
open http://localhost:5555
```

### クリーンアップ

```bash
# コンテナとボリュームの削除
make clean

# すべてのイメージも含めて削除
make clean-all
```

## 性能チューニング

### Docker Desktop の設定（macOS/Windows）

Docker Desktop の設定で以下を調整：
- CPU: 4 コア以上
- Memory: 8GB 以上
- Disk image size: 60GB 以上

### docker-compose.yml の調整

必要に応じて以下を調整：
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

## セキュリティ考慮事項

1. **本番環境では必ず.env ファイルを適切に管理**
   - Git にコミットしない
   - 適切なファイルパーミッションを設定

2. **デフォルトパスワードの変更**
   - PostgreSQL パスワード
   - Redis パスワード（本番環境）
   - SECRET_KEY

3. **ネットワークの分離**
   - 本番環境では内部ネットワークを使用
   - 必要最小限のポートのみ公開
