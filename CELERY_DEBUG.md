# Celery デバッグ手順

## 問題の概要

MANUAL_TEST.md に従ってスケジュールを作成したが、 Celery タスクが実行されていない。

## 確認された問題点

1. **Celery プロセスが起動していない**
   - Celery ワーカーとビートが実行されていない

2. **タスク名の登録**
   - データベースには`fetch_listed_info_task_asyncpg`として正しく登録されている
   - タスクも正しく実装されている

3. **設定ファイルの修正**
   - `app/core/config.py`に`extra="ignore"`を追加して、余分な環境変数を無視するよう修正済み

## 起動手順

### 1. Redis の起動確認

```bash
# Redis が起動しているか確認
redis-cli ping
# 応答: PONG

# 起動していない場合
brew services start redis
# または
redis-server
```

### 2. Celery ワーカーの起動

新しいターミナルを開いて以下を実行：

```bash
cd /Users/yosuke.kishi/workspace.gb/stockura
celery -A app.infrastructure.celery.app worker --loglevel=info
```

### 3. Celery Beat の起動

別の新しいターミナルを開いて以下を実行：

```bash
cd /Users/yosuke.kishi/workspace.gb/stockura
celery -A app.infrastructure.celery.app beat --loglevel=info
```

### 4. 動作確認

1. **スケジュールの確認**
   ```bash
   psql -U postgres -d stockura -c "SELECT id, name, cron_expression, enabled FROM celery_beat_schedules;"
   ```

2. **タスク実行ログの確認**
   ```bash
   psql -U postgres -d stockura -c "SELECT * FROM task_execution_logs ORDER BY started_at DESC LIMIT 5;"
   ```

3. **Celery ワーカーログの確認**
   Celery ワーカーのターミナルで、タスクの実行状況を確認

4. **手動でタスクを実行**
   ```python
   from app.infrastructure.celery.tasks import fetch_listed_info_task_asyncpg
   
   # 非同期実行
   result = fetch_listed_info_task_asyncpg.delay(
       period_type="yesterday"
   )
   
   # タスク ID を確認
   print(f"Task ID: {result.id}")
   
   # 結果を待つ
   print(result.get(timeout=300))
   ```

## トラブルシューティング

### Celery ワーカーが起動しない場合

1. **モジュールエラー**
   ```bash
   # 依存関係の再インストール
   pip install -r requirements.txt
   ```

2. **Redis 接続エラー**
   ```bash
   # Redis 接続を確認
   redis-cli -h localhost -p 6379 ping
   ```

3. **データベース接続エラー**
   ```bash
   # PostgreSQL 接続を確認
   psql -U postgres -d stockura -c "SELECT 1;"
   ```

### タスクが実行されない場合

1. **スケジュールが有効か確認**
   ```sql
   SELECT * FROM celery_beat_schedules WHERE enabled = true;
   ```

2. **Celery Beat のログを確認**
   - スケジューラーがスケジュールを読み込んでいるか
   - タスクがキューに追加されているか

3. **ワーカーのログを確認**
   - タスクを受信しているか
   - エラーが発生していないか

## 現在の状態

- スケジュール「 test_every_minute 」が作成済み（毎分実行）
- タスク名: `fetch_listed_info_task_asyncpg`
- パラメータ: `period_type="yesterday"`

## 次のステップ

1. 上記手順に従って Celery ワーカーとビートを起動
2. 1 分待ってタスクが実行されるか確認
3. 実行されない場合は、ログを確認してエラーを特定
4. 必要に応じて設定を調整