# 手動テストガイド

## Celery Beat 定期実行機能の動作確認

### 1. 環境準備

#### 1.1 必要なサービスの起動

```bash
# Terminal 1: Redis を起動
redis-server

# Terminal 2: PostgreSQL が起動していることを確認
psql -U postgres -d stockura -c "SELECT 1;"
```

#### 1.2 データベースマイグレーションの確認

```bash
# マイグレーションを実行
python scripts/db_migrate.py upgrade

# テーブルが作成されていることを確認
psql -U postgres -d stockura -c "\dt celery_beat_schedules;"
psql -U postgres -d stockura -c "\dt task_execution_logs;"
```

### 2. Celery の起動

#### 2.1 Celery Worker を起動

```bash
# Terminal 3: Worker を起動（asyncpg 対応版）
celery -A app.infrastructure.celery.app worker --loglevel=info
```

ワーカー起動時に以下のログが表示されることを確認：
```
[INFO/MainProcess] Setting up event loop for worker process
```

#### 2.2 Celery Beat を起動

```bash
# Terminal 4: Beat を起動（asyncpg 対応版）
celery -A app.infrastructure.celery.app beat --loglevel=info
```

Beat 起動時に以下のログが表示されることを確認：
```
[INFO/MainProcess] Event loop setup for database scheduler
[INFO/MainProcess] Syncing schedules from database
```

#### 2.3 Flower（監視ツール）を起動（オプション）

```bash
# Terminal 5: Flower を起動
celery -A app.infrastructure.celery.app flower
```

ブラウザで http://localhost:5555 にアクセス

### 3. FastAPI サーバーの起動

```bash
# Terminal 6: FastAPI を起動
uvicorn app.main:app --reload
```

API ドキュメント: http://localhost:8000/docs

### 4. スケジュール管理 API のテスト

#### 4.1 スケジュールの作成

```bash
# 毎分実行するテストスケジュールを作成
curl -X POST http://localhost:8000/api/v1/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_every_minute",
    "cron_expression": "* * * * *",
    "enabled": true,
    "description": "毎分実行するテスト",
    "task_params": {
      "period_type": "yesterday"
    }
  }'
```

レスポンス例:
```json
{
  "id": "12345678-1234-1234-1234-123456789012",
  "name": "test_every_minute",
  "cron_expression": "* * * * *",
  "enabled": true,
  "description": "毎分実行するテスト",
  "created_at": "2025-07-29T10:00:00",
  "updated_at": "2025-07-29T10:00:00",
  "task_params": {
    "period_type": "yesterday",
    "from_date": null,
    "to_date": null,
    "codes": null,
    "market": null
  }
}
```

#### 4.2 スケジュール一覧の確認

```bash
curl http://localhost:8000/api/v1/schedules/
```

#### 4.3 スケジュールの詳細確認

```bash
# {schedule_id} は作成時のレスポンスから取得
curl http://localhost:8000/api/v1/schedules/{schedule_id}
```

### 5. タスク実行の確認

#### 5.1 Celery Worker のログを確認

Worker のターミナルで以下のようなログが表示されることを確認:

```
[2025-07-29 10:01:00,123: INFO/MainProcess] Received task: fetch_listed_info_task_asyncpg[task-id]
[2025-07-29 10:01:00,456: INFO/ForkPoolWorker-1] Starting fetch_listed_info_task - task_id: task-id, schedule_id: schedule-id, period_type: yesterday
[2025-07-29 10:01:05,789: INFO/ForkPoolWorker-1] Task completed - status: success, fetched: 100, saved: 100
```

#### 5.2 データベースで実行ログを確認

```sql
-- PostgreSQL で実行
psql -U postgres -d stockura

-- 最新の実行ログを確認
SELECT
    id,
    task_name,
    status,
    started_at,
    finished_at,
    result::text
FROM task_execution_logs
ORDER BY started_at DESC
LIMIT 5;
```

### 6. 他の期間タイプのテスト

#### 6.1 7 日間のデータ取得

```bash
curl -X POST http://localhost:8000/api/v1/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_7days",
    "cron_expression": "0 10 * * *",
    "enabled": true,
    "description": "7 日間のデータ取得テスト",
    "task_params": {
      "period_type": "7days"
    }
  }'
```

#### 6.2 特定銘柄のデータ取得

```bash
curl -X POST http://localhost:8000/api/v1/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_specific_codes",
    "cron_expression": "0 11 * * *",
    "enabled": true,
    "description": "特定銘柄のデータ取得テスト",
    "task_params": {
      "period_type": "yesterday",
      "codes": ["7203", "9984"]
    }
  }'
```

#### 6.3 カスタム期間のデータ取得

```bash
curl -X POST http://localhost:8000/api/v1/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_custom_period",
    "cron_expression": "0 12 * * *",
    "enabled": true,
    "description": "カスタム期間のデータ取得テスト",
    "task_params": {
      "period_type": "custom",
      "from_date": "2025-01-01",
      "to_date": "2025-01-07"
    }
  }'
```

### 7. スケジュールの管理操作

#### 7.1 スケジュールの無効化

```bash
curl -X POST http://localhost:8000/api/v1/schedules/{schedule_id}/disable
```

#### 7.2 スケジュールの有効化

```bash
curl -X POST http://localhost:8000/api/v1/schedules/{schedule_id}/enable
```

#### 7.3 スケジュールの更新

```bash
curl -X PUT http://localhost:8000/api/v1/schedules/{schedule_id} \
  -H "Content-Type: application/json" \
  -d '{
    "cron_expression": "0 9,18 * * *",
    "description": "朝夕 2 回実行に変更"
  }'
```

#### 7.4 スケジュールの削除

```bash
curl -X DELETE http://localhost:8000/api/v1/schedules/{schedule_id}
```

### 8. タスクの手動実行

Python シェルから直接タスクを実行:

```python
# python コマンドで Python REPL を起動
python

# タスクをインポートして実行
from app.infrastructure.celery.tasks import fetch_listed_info_task

# 非同期でタスクを実行
result = fetch_listed_info_task.delay(
    period_type="yesterday"
)

# タスク ID を確認
print(f"Task ID: {result.id}")

# 結果を取得（タスクが完了するまで待機）
print(result.get(timeout=300))
```

### 9. トラブルシューティング

#### 9.1 スケジュールが実行されない場合

1. Celery Beat のログを確認し、スケジュールが読み込まれているか確認
2. データベースでスケジュールが有効になっているか確認:

```sql
SELECT name, enabled, cron_expression
FROM celery_beat_schedules;
```

#### 9.2 タスクがエラーになる場合

1. Worker のログでエラー詳細を確認
2. データベースでエラーメッセージを確認:

```sql
SELECT task_name, status, error_message
FROM task_execution_logs
WHERE status = 'failed'
ORDER BY started_at DESC
LIMIT 5;
```

#### 9.3 J-Quants API 関連のエラー

環境変数が正しく設定されているか確認:

```bash
# .env ファイルの確認
cat .env | grep JQUANTS

# 環境変数が読み込まれているか確認
python -c "from app.core.config import settings; print(settings.jquants_api_key)"
```

### 10. クリーンアップ

テスト後のクリーンアップ:

```bash
# すべてのスケジュールを削除
psql -U postgres -d stockura -c "DELETE FROM celery_beat_schedules;"

# 実行ログを削除
psql -U postgres -d stockura -c "DELETE FROM task_execution_logs;"

# Celery プロセスを停止
# 各ターミナルで Ctrl+C
```

## 注意事項

- 本番環境では適切な認証・認可を実装してください
- 大量データを扱う場合は、バッチサイズやメモリ使用量に注意してください
- J-Quants API のレート制限に注意してください
