# テストガイド: スケジュールタスクのタイムアウト問題の修正（Docker 版）

## 修正内容の概要

### 1. イベントループ競合の解決
`DatabaseSchedulerAsyncPG.sync_schedules`メソッドで、 Redis subscriber スレッドのイベントループと競合していた問題を解決：
- データベース操作用に専用のイベントループを作成
- 既存のイベントループとの干渉を回避

```python
# 修正前: 同じイベントループを使用して TimeoutError 発生
if self._event_loop.is_running():
    future = asyncio.run_coroutine_threadsafe(
        self._load_schedules_from_db(),
        self._event_loop
    )
    schedules = future.result(timeout=10)  # TimeoutError!

# 修正後: 専用のイベントループを使用
db_loop = asyncio.new_event_loop()
asyncio.set_event_loop(db_loop)
try:
    schedules = db_loop.run_until_complete(
        self._load_schedules_from_db()
    )
finally:
    db_loop.close()
    asyncio.set_event_loop(None)
```

### 2. 詳細なログの追加
- データベース接続の各ステップの実行時間を測定
- Redis Sync 機能の動作状況を詳細に記録

## 実装した機能のテスト方法

### 0. 事前準備

#### Docker 環境の起動
```bash
# すべてのサービスを起動
make up

# または個別に起動
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

#### サービスの確認
```bash
# 実行中のコンテナを確認
docker ps

# 以下のコンテナが起動していることを確認:
# - stockura-app (FastAPI)
# - stockura-celery-worker
# - stockura-celery-beat
# - stockura-redis
# - stockura-postgres
# - stockura-flower
```

### 1. Redis Sync 機能の単体テスト

#### 1.1 Redis イベントのサブスクライブテスト

ターミナル 1 でサブスクライバーを起動:
```bash
docker compose exec app python scripts/test_redis_sync.py subscribe
```

#### 1.2 Redis イベントのパブリッシュテスト

ターミナル 2 でイベントを発行:
```bash
docker compose exec app python scripts/test_redis_sync.py
```

期待される結果: ターミナル 1 でイベントが受信される

### 2. 手動でのスケジュール同期テスト

データベースにスケジュールを作成して Redis イベントを発行:
```bash
docker compose exec app python scripts/test_manual_schedule_sync.py
```

クリーンアップ:
```bash
docker compose exec app python scripts/test_manual_schedule_sync.py cleanup
```

### 3. 完全な統合テスト

#### 前提条件の確認

Docker 環境が正しく起動しているか確認:
```bash
# サービスの状態確認
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

# ヘルスチェック
curl http://localhost:8000/  # FastAPI
curl http://localhost:5555/  # Flower (Celery monitoring)
```

#### テスト実行
```bash
docker compose exec -e AUTO_MODE=true app python scripts/test_scheduled_listed_info_api.py --wait-minutes 1
```

### 4. 即時実行テスト

スケジュールの即時同期と実行を確認:
```bash
docker compose exec app python scripts/test_immediate_schedule_execution.py
```

### 5. 動作確認済みの結果

以下の動作を確認しました：

1. **スケジュール作成と Redis イベント発行**: ✅
   - API でスケジュールを作成すると、 Redis Sync イベントが発行される
   - Celery Beat がイベントを受信し、即座にスケジュールを同期する

2. **タスク実行**: ✅
   - 毎分実行（`* * * * *`）のスケジュールが正常に実行される
   - 実行結果が task_execution_logs テーブルに記録される

3. **実行履歴の確認**: ✅
   - タスク ID: 529824a0-9de8-4fd1-94c3-486280ea966f
   - 実行時刻: 2025-08-09 15:32:00 UTC
   - ステータス: success
   - 取得件数: 4385 件
   - 保存件数: 4385 件

### 6. 環境変数の確認

以下の環境変数が設定されていることを確認:
```bash
# .env ファイルまたは環境変数
CELERY_BEAT_REDIS_SYNC_ENABLED=true
CELERY_BEAT_MIN_SYNC_INTERVAL=5
CELERY_BEAT_REDIS_CHANNEL=celery_beat_schedule_updates
```

### 7. ログの確認ポイント

#### Celery Beat のログ
```bash
docker compose logs -f celery-beat
```

以下のメッセージが表示されることを確認:
- "Redis Sync is ENABLED - Starting Redis subscriber thread"
- "✅ Subscribed to Redis channel: celery_beat_schedule_updates"
- "🔔 Received schedule event: schedule_created"
- "⚡ Triggering immediate schedule sync due to Redis event"
- "Using dedicated event loop for database operations"
- "Successfully loaded N schedules"

#### FastAPI のログ
```bash
docker compose logs -f app
```

以下のメッセージが表示されることを確認:
- "✅ Published schedule_created event for schedule {id}"

#### Redis イベントのモニタリング
別ターミナルで Redis イベントを監視:
```bash
docker compose exec app python scripts/monitor_redis_events.py
```

### 8. トラブルシューティング

#### 問題: Redis 接続エラー
- Redis が起動していることを確認
- Redis URL が正しいことを確認 (`REDIS_URL`環境変数)

#### 問題: イベントが受信されない
- `CELERY_BEAT_REDIS_SYNC_ENABLED=true`が設定されていることを確認
- Celery Beat が`DatabaseSchedulerAsyncPG`を使用していることを確認

#### 問題: TimeoutError: "This event loop is already running"
- **解決済み**: 専用のイベントループを使用することで解決
- Celery Beat を再起動して修正を反映させる

#### 問題: スケジュールが DB に保存されない
- API レスポンスで kwargs が空になっていないか確認
- task_params が正しく kwargs に変換されているか確認

### 9. パフォーマンステスト

多数のスケジュール作成時のテスト:
```python
# 100 個のスケジュールを同時に作成するテストスクリプトを実行
# (別途作成が必要)
```

### 10. 機能の無効化テスト

Redis sync 機能を無効にした場合の動作確認:
```bash
docker compose exec -e CELERY_BEAT_REDIS_SYNC_ENABLED=false celery-beat celery -A app.infrastructure.celery.app beat --loglevel=info
```

この場合、従来通り 60 秒ごとの同期のみが行われることを確認。

## まとめ

修正により、以下の問題が解決されました：
1. Celery Beat の TimeoutError（イベントループ競合）
2. スケジュール作成後の即時同期
3. タスクの正常な実行と履歴の記録

これにより、`test_scheduled_listed_info_api.py`のタイムアウト問題が解決され、スケジュールタスクが期待通りに動作するようになりました。