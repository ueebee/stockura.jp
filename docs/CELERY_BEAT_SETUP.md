# Celery Beat セットアップガイド

## 概要

このドキュメントでは、 Celery Beat を使用して listed_info（上場銘柄情報）を定期的に取得する機能のセットアップ方法を説明します。

## 必要な環境

- Redis (Celery のブローカーとして使用)
- PostgreSQL (スケジュール管理とデータ保存)
- Python 3.9+

## インストール

1. 必要なパッケージをインストール:

```bash
pip install -r requirements.txt
```

2. データベースマイグレーションを実行:

```bash
python scripts/db_migrate.py upgrade
```

## 環境変数の設定

`.env`ファイルに以下の設定を追加:

```env
# Celery 設定
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TIMEZONE=Asia/Tokyo
```

## 起動方法

### 1. Redis を起動

```bash
redis-server
```

### 2. Celery Worker を起動

```bash
celery -A app.infrastructure.celery.app worker --loglevel=info
```

### 3. Celery Beat を起動

```bash
celery -A app.infrastructure.celery.app beat --loglevel=info
```

### 4. Flower (監視ツール) を起動 (オプション)

```bash
celery -A app.infrastructure.celery.app flower
```

Flower は http://localhost:5555 でアクセスできます。

## スケジュール管理 API

### スケジュールの作成

```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily_listed_info_fetch",
    "cron_expression": "0 9 * * *",
    "enabled": true,
    "description": "毎日午前 9 時に上場銘柄情報を取得",
    "task_params": {
      "period_type": "yesterday"
    }
  }'
```

### 利用可能なパラメータ

- `period_type`: 
  - `"yesterday"`: 昨日のデータを取得（デフォルト）
  - `"7days"`: 昨日から 7 日前までのデータを取得
  - `"30days"`: 昨日から 30 日前までのデータを取得
  - `"custom"`: カスタム期間（from_date, to_date が必要）
- `from_date`: 開始日（YYYY-MM-DD 形式、 period_type="custom"の場合必須）
- `to_date`: 終了日（YYYY-MM-DD 形式、 period_type="custom"の場合必須）
- `codes`: 特定銘柄のリスト（例: ["7203", "9984"]）
- `market`: 市場コード

### スケジュール一覧の取得

```bash
curl http://localhost:8000/api/v1/schedules
```

### スケジュールの更新

```bash
curl -X PUT http://localhost:8000/api/v1/schedules/{schedule_id} \
  -H "Content-Type: application/json" \
  -d '{
    "cron_expression": "0 18 * * *"
  }'
```

### スケジュールの有効化/無効化

```bash
# 有効化
curl -X POST http://localhost:8000/api/v1/schedules/{schedule_id}/enable

# 無効化
curl -X POST http://localhost:8000/api/v1/schedules/{schedule_id}/disable
```

### スケジュールの削除

```bash
curl -X DELETE http://localhost:8000/api/v1/schedules/{schedule_id}
```

## Cron 式の例

- `"0 9 * * *"`: 毎日午前 9 時
- `"0 9 * * 1-5"`: 平日の午前 9 時
- `"0 9,18 * * *"`: 毎日午前 9 時と午後 6 時
- `"*/30 * * * *"`: 30 分ごと
- `"0 0 * * 0"`: 毎週日曜日の午前 0 時

## タスクの手動実行

Celery タスクを手動で実行することも可能です:

```python
from app.infrastructure.celery.tasks import fetch_listed_info_task

# 非同期実行
result = fetch_listed_info_task.delay(
    period_type="yesterday",
    codes=["7203", "9984"]
)

# 結果の取得
print(result.get())
```

## トラブルシューティング

### スケジュールが実行されない

1. Celery Beat と Worker が両方起動していることを確認
2. データベースのスケジュールが有効になっていることを確認
3. Redis が正常に動作していることを確認

### タスクがエラーになる

1. Celery Worker のログを確認
2. `task_execution_logs`テーブルでエラー詳細を確認
3. J-Quants API の認証情報が正しく設定されているか確認

### メモリ使用量が多い

大量データを処理する場合は、`batch_size`を調整してください。

## 監視とログ

### タスク実行ログの確認

```sql
-- 最近の実行ログ
SELECT * FROM task_execution_logs 
ORDER BY started_at DESC 
LIMIT 10;

-- 失敗したタスク
SELECT * FROM task_execution_logs 
WHERE status = 'failed' 
ORDER BY started_at DESC;
```

### Flower での監視

Flower (http://localhost:5555) では以下が確認できます:

- アクティブなワーカー
- 実行中のタスク
- タスクの成功/失敗率
- タスクの実行時間

## セキュリティ考慮事項

1. プロダクション環境では、 Redis と Celery の認証を設定してください
2. スケジュール管理 API には適切な認証・認可を実装してください
3. J-Quants API の認証情報は環境変数で管理してください