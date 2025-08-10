# Docker 環境での Redis Sync 修正のテスト手順

## 概要
Docker 環境でスケジュールタスクの実行履歴が確認できない問題を修正しました。以下の手順でテストを実施してください。

## 前提条件
- Docker 及び Docker Compose がインストールされていること
- プロジェクトのルートディレクトリで作業すること

## テスト手順

### 1. Docker コンテナの再起動
修正を反映させるため、コンテナを再起動します：

```bash
# 既存のコンテナを停止
docker compose down

# コンテナを起動（開発環境）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 2. 環境変数の確認
各コンテナに環境変数が正しく設定されているか確認：

```bash
# 環境変数確認スクリプトを実行
bash scripts/check_docker_env.sh
```

期待される出力：
- 各コンテナで CELERY_BEAT_REDIS_SYNC_ENABLED=true
- CELERY_BEAT_MIN_SYNC_INTERVAL=5
- CELERY_BEAT_REDIS_CHANNEL=celery_beat_schedule_updates

### 3. 診断スクリプトの実行
Redis Sync 機能の状態を診断：

```bash
docker compose exec app python scripts/diagnose_redis_sync_docker.py
```

すべての項目で✅が表示されることを確認してください。

### 4. 統合テストの実行
Redis Sync 機能の動作を確認：

```bash
docker compose exec app python scripts/test_docker_redis_sync.py
```

### 5. 実際のテストスクリプトの実行
最終的に、元の問題が解決されたことを確認：

```bash
docker compose exec -e AUTO_MODE=true app python scripts/test_scheduled_listed_info_api.py --wait-minutes 1
```

## 期待される結果

### Celery Beat ログの確認
以下のメッセージがログに表示されること：

```bash
docker compose logs celery-beat --tail=50 | grep -E "Redis|sync"
```

- "Redis Sync is ENABLED - Starting Redis subscriber thread"
- "Redis subscriber thread started for schedule updates"
- "✅ Subscribed to Redis channel: celery_beat_schedule_updates"
- "🔔 Received schedule event: schedule_created"
- "⚡ Triggering immediate schedule sync due to Redis event"

### test_scheduled_listed_info_api.py の結果
- タイムアウトせずに実行履歴が取得できる
- 実行時刻から 1 分以内に履歴が確認できる

## トラブルシューティング

### 問題: 環境変数が設定されていない
```bash
# .env ファイルを確認
cat .env | grep CELERY_BEAT_REDIS_SYNC

# 設定がない場合は追加
echo "" >> .env
echo "CELERY_BEAT_REDIS_SYNC_ENABLED=true" >> .env
echo "CELERY_BEAT_MIN_SYNC_INTERVAL=5" >> .env
echo "CELERY_BEAT_REDIS_CHANNEL=celery_beat_schedule_updates" >> .env
```

### 問題: Redis イベントが受信されない
```bash
# Redis イベントをモニタリング
docker compose exec app python scripts/monitor_redis_events.py
```

別ターミナルでスケジュールを作成し、イベントが表示されることを確認。

### 問題: Celery Beat が起動しない
```bash
# Celery Beat のログを詳細に確認
docker compose logs celery-beat -f
```

エラーメッセージを確認し、必要に応じて対処。

## 修正内容の概要

1. **診断ツールの追加**
   - `scripts/diagnose_redis_sync_docker.py`: Redis Sync 設定の診断
   - `scripts/check_docker_env.sh`: Docker 環境変数の確認

2. **ログ出力の改善**
   - DatabaseSchedulerAsyncPG: 初期化時とイベント処理時の詳細ログ
   - ScheduleEventPublisher: イベント発行時の詳細ログ

3. **Docker Compose 設定の修正**
   - 環境変数を明示的に各コンテナに渡すよう設定
   - docker-compose.yml と docker-compose.dev.yml の両方を更新

4. **テストツールの追加**
   - `scripts/test_docker_redis_sync.py`: 統合テストスクリプト

docker compose exec -e AUTO_MODE=true app python scripts/test_scheduled_listed_info_api.py
  --wait-minutes 1
