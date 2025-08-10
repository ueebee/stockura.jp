# 要件: Docker 環境での Redis Sync 設定不足による実行履歴確認問題の解決

## 背景

スケジュールタスクの実行履歴が確認できない問題が発生しています。スケジュール作成は成功し、 Celery Beat へのタスク登録も行われていますが、実行履歴の取得がタイムアウトしています。

### 現象
- スケジュール作成 API（POST /api/v1/schedules）は正常に動作
- スケジュール詳細の取得は成功
- タスクの実行履歴取得でタイムアウト（300 秒）
- エラーメッセージ：「実行履歴が取得できませんでした」「 Celery Beat が起動していることを確認してください」

### 調査結果
- 既存の Redis Sync 機能実装（fix-scheduled-task-timeout）は完了している
- .env.docker ファイルに Redis Sync 関連の環境変数が不足している
- Docker 環境で Celery Beat が Redis イベントを受信できていない可能性が高い

## 要件

### 1. 環境設定の修正
- Docker 環境用の環境変数ファイル（.env.docker）に Redis Sync 関連の設定を追加する
- 必要な環境変数：
  - `CELERY_BEAT_REDIS_SYNC_ENABLED=true`
  - `CELERY_BEAT_MIN_SYNC_INTERVAL=5`
  - `CELERY_BEAT_REDIS_CHANNEL=celery_beat_schedule_updates`

### 2. Docker Compose 設定の確認と修正
- Celery Beat コンテナが正しく環境変数を読み込めているか確認
- 必要に応じて docker-compose.yml または docker-compose.dev.yml を修正

### 3. Redis 接続設定の確認
- Docker 環境内での Redis 接続 URL が正しいことを確認
- Celery Beat コンテナから Redis コンテナへの接続が可能であることを確認

### 4. ログ出力の改善
- Redis Sync 機能が有効化されているかをログで確認できるようにする
- Redis イベントの送受信状況をログで追跡できるようにする

### 5. 動作確認
- test_scheduled_listed_info_api.py スクリプトで正常に実行履歴が取得できることを確認
- Celery Beat ログで以下のメッセージが表示されることを確認：
  - "Redis subscriber thread started for schedule updates"
  - "Subscribed to Redis channel: celery_beat_schedule_updates"
  - "Received schedule event: schedule_created"

## 制約事項
- 既存の Redis Sync 実装（fix-scheduled-task-timeout）を変更しない
- Docker 環境の基本構成を変更しない
- 既存の API インターフェースを変更しない

## 成功条件
- Docker 環境で test_scheduled_listed_info_api.py を実行した際、タイムアウトせずに実行履歴が取得できる
- スケジュール作成から 1 分以内に実行履歴が確認できる
- Celery Beat のログで Redis Sync が有効化されていることが確認できる