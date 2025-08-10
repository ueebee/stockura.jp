# 要件ファイル: listed_info タスクの cron 形式スケジューリング機能

## 1. 概要
既存の `listed_info` タスク（上場銘柄一覧データ取得）に対して、 cron 形式でのスケジューリング機能を実装する。現在は period_type による期間指定のみだが、より柔軟なスケジューリングを可能にする。

## 2. 背景
現在の実装状況：
- `fetch_listed_info_task` が Celery タスクとして実装済み
- `celery_beat_schedules` テーブルに `cron_expression` カラムが存在
- period_type パラメータ（"yesterday", "7days", "30days", "custom"）で期間を指定
- DatabaseSchedulerAsyncPG を使用したデータベースベースのスケジューラ実装

## 3. 機能要件

### 3.1 cron 形式でのスケジュール登録
- cron 形式（例: "0 9 * * *" = 毎日 9 時）でスケジュールを登録できる
- 既存の period_type パラメータと併用可能

### 3.2 スケジュール管理機能
- スケジュールの作成・更新・削除・一覧表示
- スケジュールの有効/無効の切り替え
- 実行履歴の確認

### 3.3 実行パターンの例
- 毎日 9:00 に前日分のデータを取得: `"0 9 * * *"` + `period_type="yesterday"`
- 毎週月曜 8:00 に過去 7 日分を取得: `"0 8 * * 1"` + `period_type="7days"`
- 毎月 1 日 6:00 に前月分を取得: `"0 6 1 * *"` + `period_type="30days"`

### 3.4 API エンドポイント
- POST `/api/v1/schedules/listed-info` - スケジュール作成
- GET `/api/v1/schedules/listed-info` - スケジュール一覧
- PUT `/api/v1/schedules/listed-info/{schedule_id}` - スケジュール更新
- DELETE `/api/v1/schedules/listed-info/{schedule_id}` - スケジュール削除
- GET `/api/v1/schedules/listed-info/{schedule_id}/history` - 実行履歴

### 3.5 CLI コマンド
- `python scripts/manage_listed_info_schedule.py create --cron "0 9 * * *" --period-type yesterday`
- `python scripts/manage_listed_info_schedule.py list`
- `python scripts/manage_listed_info_schedule.py enable/disable {schedule_id}`

## 4. 非機能要件

### 4.1 パフォーマンス
- スケジュール登録・更新は即座に反映される
- 大量のスケジュールがあっても処理に影響しない

### 4.2 信頼性
- スケジュールの重複実行を防ぐ
- 実行失敗時のリトライ機能
- エラー通知機能

### 4.3 保守性
- 既存の実装を最大限活用
- テストコードの充実
- ログとモニタリング

## 5. 制約事項
- 既存の `fetch_listed_info_task` の実装を変更しない
- 既存のデータベーススキーマ（`celery_beat_schedules`）を活用
- 後方互換性を保つ

## 6. 成功基準
1. cron 形式でスケジュールを登録し、指定時刻に listed_info タスクが実行される
2. API/CLI 経由でスケジュールの CRUD 操作ができる
3. 実行履歴が確認でき、エラー時の原因が特定できる
4. 既存の手動実行やその他の実行方法に影響がない