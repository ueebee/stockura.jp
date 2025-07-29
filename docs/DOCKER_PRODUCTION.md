# Docker 本番環境デプロイガイド

このガイドでは、 Stockura アプリケーションを本番環境にデプロイする方法について説明します。

## 本番環境の構成

### アーキテクチャ

```
Internet
    ↓
Nginx (SSL/TLS 終端)
    ↓
FastAPI App (Gunicorn)
    ↓
PostgreSQL / Redis
    ↓
Celery Worker / Beat
```

### セキュリティ対策

- HTTPS 通信の強制
- 非 root ユーザーでの実行
- 環境変数の安全な管理
- ネットワークの分離
- 定期的なセキュリティアップデート

## デプロイ準備

### 1. 環境変数の設定

```bash
# 本番用環境変数ファイルを作成
cp .env.docker .env.production

# 以下の値を本番環境用に設定
vim .env.production
```

**必須設定項目：**

```bash
# アプリケーション設定
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# データベース設定（本番用の強力なパスワードを使用）
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql+asyncpg://stockura:<strong-password>@postgres:5432/stockura

# Redis 設定（必要に応じてパスワードを設定）
REDIS_URL=redis://redis:6379/0

# セキュリティ設定（必ず変更すること）
SECRET_KEY=<generate-strong-secret-key>

# J-Quants API（本番用の認証情報）
JQUANTS_API_KEY=<production-api-key>
JQUANTS_EMAIL=<production-email>
JQUANTS_PASSWORD=<production-password>

# CORS 設定（本番環境のドメインのみ許可）
CORS_ORIGINS=["https://yourdomain.com"]
```

### 2. SSL/TLS 証明書の準備

```bash
# Let's Encrypt を使用する場合
mkdir -p nginx/certs
certbot certonly --standalone -d yourdomain.com
```

### 3. Nginx 設定の更新

```bash
# nginx/nginx.prod.conf を編集
sed -i 's/yourdomain.com/実際のドメイン名/g' nginx/nginx.prod.conf
```

## デプロイ手順

### 1. サーバーへのデプロイ

```bash
# コードをサーバーにデプロイ
rsync -avz --exclude='.git' --exclude='__pycache__' ./ user@server:/opt/stockura/

# サーバーに SSH 接続
ssh user@server
cd /opt/stockura
```

### 2. Docker イメージのビルド

```bash
# 本番用イメージをビルド
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
```

### 3. データベースの初期化

```bash
# データベースマイグレーション
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm app python scripts/db_migrate.py upgrade
```

### 4. サービスの起動

```bash
# すべてのサービスを起動
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# ログを確認
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### 5. ヘルスチェック

```bash
# API のヘルスチェック
curl https://yourdomain.com/health

# Nginx のステータス確認
curl http://localhost/nginx_status
```

## 監視とロギング

### ログの管理

```bash
# ログの確認
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f app

# ログのローテーション設定
cat > /etc/logrotate.d/stockura << EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF
```

### メトリクスの収集

```bash
# Prometheus エクスポーターの有効化
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d prometheus-exporter
```

### アラート設定

```bash
# ヘルスチェックスクリプト
cat > /opt/stockura/scripts/healthcheck.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8000/health; then
    echo "Health check failed" | mail -s "Stockura Alert" admin@example.com
fi
EOF

# cron で定期実行
echo "*/5 * * * * /opt/stockura/scripts/healthcheck.sh" | crontab -
```

## バックアップ

### データベースバックアップ

```bash
# バックアップスクリプト
cat > /opt/stockura/scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U stockura stockura | gzip > /backup/stockura_$DATE.sql.gz
find /backup -name "stockura_*.sql.gz" -mtime +7 -delete
EOF

# 日次バックアップの設定
echo "0 2 * * * /opt/stockura/scripts/backup.sh" | crontab -
```

### ボリュームバックアップ

```bash
# Docker ボリュームのバックアップ
docker run --rm -v stockura_postgres_data:/data -v /backup:/backup alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz -C /data .
```

## スケーリング

### 水平スケーリング

```bash
# Celery Worker を増やす
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale celery-worker=3

# FastAPI アプリケーションを増やす
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale app=2
```

### リソース制限

```yaml
# docker-compose.prod.yml でリソース制限を設定
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## セキュリティアップデート

### 定期的なアップデート

```bash
# システムパッケージのアップデート
apt update && apt upgrade -y

# Docker イメージの更新
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 脆弱性スキャン

```bash
# Docker イメージの脆弱性スキャン
docker scan stockura_app:latest
```

## トラブルシューティング

### サービスが起動しない

```bash
# コンテナの状態確認
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 詳細なエラーログ
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=100 app
```

### パフォーマンス問題

```bash
# リソース使用状況の確認
docker stats

# PostgreSQL のスロークエリ確認
docker-compose exec postgres psql -U stockura -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### 緊急時のロールバック

```bash
# 前のバージョンにロールバック
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
git checkout <previous-version>
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## チェックリスト

デプロイ前の確認事項：

- [ ] 環境変数がすべて設定されている
- [ ] SSL/TLS 証明書が設定されている
- [ ] バックアップが設定されている
- [ ] 監視が設定されている
- [ ] セキュリティアップデートが適用されている
- [ ] ログローテーションが設定されている
- [ ] ファイアウォールが適切に設定されている
- [ ] リソース制限が設定されている