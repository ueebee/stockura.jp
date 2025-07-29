# Docker トラブルシューティングガイド

このガイドでは、 Docker 環境で発生する可能性のある問題と解決方法について説明します。

## よくある問題と解決方法

### 起動時の問題

#### 問題: docker-compose up でエラーが発生する

**症状:**
```
ERROR: for app  Cannot start service app: driver failed programming external connectivity
```

**解決方法:**
```bash
# ポートが既に使用されているか確認
lsof -i :8000

# 使用中の場合は、別のポートに変更
# docker-compose.dev.yml を編集
ports:
  - "8001:8000"  # 8001 に変更
```

#### 問題: データベース接続エラー

**症状:**
```
sqlalchemy.exc.OperationalError: (asyncpg.exceptions.InvalidCatalogNameError) database "stockura" does not exist
```

**解決方法:**
```bash
# データベースを手動で作成
docker-compose exec postgres createdb -U stockura stockura

# マイグレーションを再実行
make migrate
```

#### 問題: Permission denied エラー

**症状:**
```
PermissionError: [Errno 13] Permission denied: '/app/logs'
```

**解決方法:**
```bash
# ホストマシンでディレクトリの権限を変更
sudo chown -R 1000:1000 ./logs

# または Docker 内で実行
docker-compose exec app chown -R appuser:appuser /app/logs
```

### Celery 関連の問題

#### 問題: Celery Worker が起動しない

**症状:**
```
celery.exceptions.ImproperlyConfigured: The specified broker transport 'redis' is not available
```

**解決方法:**
```bash
# Redis が起動しているか確認
docker-compose ps redis

# Redis に接続できるか確認
docker-compose exec redis redis-cli ping

# Redis を再起動
docker-compose restart redis
```

#### 問題: タスクが実行されない

**症状:**
Celery Beat は動作しているが、タスクが実行されない

**解決方法:**
```bash
# Worker のログを確認
docker-compose logs -f celery-worker

# タスクが登録されているか確認
docker-compose exec celery-worker celery -A app.infrastructure.celery.app inspect registered

# スケジュールが登録されているか確認
docker-compose exec postgres psql -U stockura -d stockura -c "SELECT * FROM celery_beat_schedules;"
```

#### 問題: Event loop エラー

**症状:**
```
RuntimeError: There is no current event loop in thread
```

**解決方法:**
```bash
# Celery Worker を再起動
docker-compose restart celery-worker

# ログを確認して event loop が初期化されているか確認
docker-compose logs celery-worker | grep "Setting up event loop"
```

### データベース関連の問題

#### 問題: マイグレーションが失敗する

**症状:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxx'
```

**解決方法:**
```bash
# 現在のリビジョンを確認
docker-compose exec app alembic current

# ヘッドを確認
docker-compose exec app alembic heads

# 履歴を確認
docker-compose exec app alembic history

# 必要に応じてダウングレード
docker-compose exec app alembic downgrade -1
```

#### 問題: PostgreSQL のディスク容量不足

**症状:**
```
PANIC: could not write to file "pg_wal/xlogtemp.xxx": No space left on device
```

**解決方法:**
```bash
# Docker ボリュームの使用状況を確認
docker system df

# 不要なボリュームを削除
docker volume prune

# WAL ファイルをクリーンアップ
docker-compose exec postgres vacuumdb -U stockura -d stockura --full
```

### パフォーマンス問題

#### 問題: コンテナが遅い（Mac/Windows）

**解決方法:**
```bash
# Docker Desktop の設定でリソースを増やす
# Settings > Resources で以下を調整:
# - CPUs: 4 以上
# - Memory: 8GB 以上
# - Swap: 2GB 以上

# ボリュームマウントを最適化（開発時）
# docker-compose.dev.yml で cached オプションを使用
volumes:
  - ./app:/app/app:cached
```

#### 問題: ビルドが遅い

**解決方法:**
```bash
# BuildKit を有効化
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# キャッシュを活用してビルド
docker-compose build --build-arg BUILDKIT_INLINE_CACHE=1
```

### ネットワーク関連の問題

#### 問題: コンテナ間で通信できない

**症状:**
```
Failed to establish a new connection: [Errno -2] Name or service not known
```

**解決方法:**
```bash
# ネットワークを確認
docker network ls
docker network inspect stockura_default

# コンテナが同じネットワークにいるか確認
docker inspect app | grep NetworkMode
docker inspect postgres | grep NetworkMode

# ネットワークを再作成
docker-compose down
docker network prune
docker-compose up -d
```

### ログとデバッグ

#### ログが見つからない

```bash
# すべてのログを確認
docker-compose logs

# 特定のサービスのログを確認（フォロー）
docker-compose logs -f app

# タイムスタンプ付きでログを確認
docker-compose logs -t

# 最新の 100 行のみ表示
docker-compose logs --tail=100
```

#### デバッグモードで起動

```bash
# 環境変数でデバッグを有効化
DEBUG=true docker-compose up

# Python デバッガーを使用
docker-compose exec app python -m pdb
```

### クリーンアップとリセット

#### 完全リセット

```bash
# すべてを停止して削除
docker-compose down -v

# イメージも含めて削除
docker-compose down -v --rmi all

# システム全体のクリーンアップ
docker system prune -a --volumes
```

#### 特定のサービスのみリセット

```bash
# 特定のサービスを再作成
docker-compose up -d --force-recreate app

# 特定のボリュームのみ削除
docker volume rm stockura_postgres_data
```

## 診断コマンド集

### システム状態の確認

```bash
# Docker の情報
docker info

# ディスク使用量
docker system df

# リソース使用状況
docker stats

# コンテナの詳細情報
docker inspect <container_name>
```

### ヘルスチェック

```bash
# アプリケーションのヘルスチェック
curl http://localhost:8000/health

# データベースの接続確認
docker-compose exec postgres pg_isready

# Redis の接続確認
docker-compose exec redis redis-cli ping
```

### プロセス確認

```bash
# コンテナ内のプロセス
docker-compose exec app ps aux

# ポートの使用状況
docker-compose exec app netstat -tulpn
```

## 緊急時の対応

### サービスが応答しない

1. **ログを確認**
   ```bash
   docker-compose logs --tail=100 app
   ```

2. **リソースを確認**
   ```bash
   docker stats
   ```

3. **再起動を試みる**
   ```bash
   docker-compose restart app
   ```

4. **強制的に再作成**
   ```bash
   docker-compose up -d --force-recreate app
   ```

### データの復旧

```bash
# バックアップからデータベースを復元
docker-compose exec -T postgres psql -U stockura stockura < backup.sql

# ボリュームのバックアップから復元
docker run --rm -v stockura_postgres_data:/data -v /backup:/backup alpine tar xzf /backup/postgres_data_backup.tar.gz -C /data
```

## サポート

問題が解決しない場合は、以下の情報を含めて Issue を作成してください：

1. エラーメッセージの全文
2. `docker-compose logs` の出力
3. `docker info` の出力
4. 使用している OS とバージョン
5. 実行したコマンドの履歴