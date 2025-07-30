# Docker 環境での Celery デバッグ結果

## 問題の概要

MANUAL_TEST.md に従ってスケジュールを作成したが、 Celery タスクが実行されていない問題について調査しました。

## 確認された状況

### 1. Docker コンテナの状態
すべてのコンテナは正常に起動しています：
- stockura-postgres（正常稼働）
- stockura-redis（正常稼働）  
- stockura-app（正常稼働）
- stockura-celery-worker（正常稼働）
- stockura-celery-beat（正常稼働）
- stockura-flower（正常稼働）

### 2. データベースマイグレーション
最初は celery_beat_schedules テーブルが存在しませんでしたが、以下の手順で解決：
```bash
docker exec stockura-app python scripts/db_migrate.py upgrade
```

マイグレーション適用後、以下のテーブルが存在することを確認：
- alembic_version
- celery_beat_schedules
- listed_info
- task_execution_logs

### 3. スケジュールの登録
直接データベースにスケジュールを挿入：
```sql
INSERT INTO celery_beat_schedules (
    id,
    name, 
    task_name, 
    cron_expression, 
    enabled, 
    args, 
    kwargs, 
    description, 
    created_at, 
    updated_at
) VALUES (
    gen_random_uuid(),
    'test_every_minute',
    'fetch_listed_info_task_asyncpg',
    '* * * * *',
    true,
    '[]',
    '{"schedule_id": 1, "from_date": "20250729", "to_date": "20250730"}',
    'Test schedule - runs every minute',
    NOW(),
    NOW()
);
```

### 4. Celery Beat の状態
- スケジュールは正常に読み込まれています（「 Loaded 1 schedules from database 」）
- しかし、タスクがワーカーに送信されていない模様

## 考えられる原因

1. **タスク名の不一致**
   - 登録されたタスク名: `fetch_listed_info_task_asyncpg`
   - Celery に登録されているタスクの確認が必要

2. **スケジューラーの実装問題**
   - カスタムデータベーススケジューラーがタスクを正しく送信していない可能性

3. **Celery 設定の問題**
   - タスクの自動発見が機能していない可能性

## 次のステップ

### 1. タスク登録の確認
```bash
# Celery に登録されているタスクの一覧確認
docker exec stockura-celery-worker celery -A app.infrastructure.celery.app inspect registered
```

### 2. デバッグログの有効化
Celery Beat をより詳細なログレベルで再起動：
```bash
docker-compose stop celery-beat
docker-compose run --rm celery-beat celery -A app.infrastructure.celery.app beat --loglevel=debug
```

### 3. 手動タスク実行テスト
タスクが正しく動作するか手動で確認：
```bash
docker exec -it stockura-app python -c "
from app.infrastructure.celery.app import app
result = app.send_task('fetch_listed_info_task_asyncpg', kwargs={
    'schedule_id': 1,
    'from_date': '20250729',
    'to_date': '20250730'
})
print(f'Task ID: {result.id}')
"
```

### 4. Flower での監視
Flower で詳細を確認：
- http://localhost:5555

## 推奨される修正

1. **スケジューラーの実装確認**
   - `app/infrastructure/celery/schedulers/database_scheduler_asyncpg.py`の実装を確認
   - タスクが正しくキューに送信されているか検証

2. **タスクの登録確認**
   - `app/infrastructure/celery/app.py`でタスクが正しく登録されているか確認
   - autodiscover_tasks が正しく設定されているか確認

3. **API 統合の修正**
   - 現在の API エンドポイントが Celery Beat テーブルと連携していない
   - 適切なスキーマとエンドポイントの実装が必要

## 一時的な回避策

開発中は以下の方法でタスクを手動実行できます：

```bash
# Celery タスクを直接実行
docker exec stockura-celery-worker celery -A app.infrastructure.celery.app call fetch_listed_info_task_asyncpg --kwargs='{"schedule_id": 1, "from_date": "20250729", "to_date": "20250730"}'
```

## 更新: デバッグ結果

### 解決された問題
1. **DB マイグレーション**: `celery_beat_schedules`テーブルが作成されました
2. **スケジュール読み込み**: スケジュールが DB から正しく読み込まれています
3. **is_due 判定**: タスクが実行時刻になると`is_due=True`を返しています

### 残っている問題
**タスクが送信されない**: `is_due=True`になってもタスクがワーカーに送信されていません。

### 問題の原因分析
カスタムスケジューラー (`DatabaseSchedulerAsyncPG`) の実装に問題がある可能性：
1. `last_run_at`の管理が正しくない
2. 親クラスの`tick()`メソッドがタスクを送信する際に必要な情報が不足している
3. `ScheduleEntry`の初期化が不完全

### 推奨される次のステップ

1. **標準スケジューラーの使用を検討**
   ```python
   # celeryconfig.py で標準の PersistentScheduler を使用
   beat_scheduler = 'celery.beat:PersistentScheduler'
   ```

2. **カスタムスケジューラーの修正**
   - `apply_entry()`メソッドの実装確認
   - `last_run_at`の更新処理を追加
   - タスク送信のログを追加

3. **一時的な回避策**
   - 標準の crontab スケジュール定義を使用
   - Celery Beat の設定ファイルでスケジュールを定義

## まとめ

Docker 環境自体は正常に動作していますが、 Celery Beat のカスタムスケジューラーがタスクを正しく送信していない可能性があります。カスタムスケジューラーの実装を見直すか、標準のスケジューラーを使用することを検討してください。

## 更新: 問題解決 (2025-07-30)

### 解決した問題
カスタムスケジューラー `DatabaseSchedulerAsyncPG` がタスクを送信しない問題を修正しました。

### 実施した修正
1. **tick() メソッドのオーバーライド**
   - 各スケジュールエントリーの`is_due`チェックを明示的に実装
   - due なタスクに対して`apply_entry`を呼び出すように修正

2. **apply_entry() メソッドの実装**
   - 親クラスの`apply_entry`を呼び出してタスクを送信
   - タスク送信のログを追加

3. **DatabaseScheduleEntry クラスの改善**
   - `__next__()`メソッドを実装
   - `is_due()`のログ出力を改善

### 動作確認結果
- スケジュールがデータベースから正常に読み込まれる
- 指定時刻になるとタスクがワーカーに送信される
- Celery Beat ログに「 Task sent successfully 」が表示される
- 1 分ごとのスケジュールが正常に動作する

### 今後の推奨事項
1. **本番環境への適用前にテストを実施**
   - 様々なスケジュールパターンでのテスト
   - 長時間稼働テスト

2. **監視の強化**
   - Flower でのタスク実行状況の監視
   - task_execution_logs テーブルの定期的な確認

3. **将来的な改善案**
   - `last_run_at`のデータベースへの永続化
   - より詳細なエラーハンドリング
   - パフォーマンスの最適化