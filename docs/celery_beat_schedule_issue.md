# Celery Beat スケジュール設定の現状と課題

## 現在の実装

### 仕組み
1. UIから設定した時刻は`api_endpoint_schedules`テーブルに保存
2. Celery Beat起動時にデータベースから設定を読み込み
3. JST時刻をUTCに変換してCelery Beatに設定

### 動作確認
- UIで設定した8:08（JST）は正しくUTC 23:08に変換される
- Celery Beatは設定通りに動作する

## 課題

### 動的更新の非対応
- UIから設定を変更してもCelery Beatに即座に反映されない
- Beatの再起動が必要

### 原因
- `celery_app.conf.beat_schedule`への変更は実行中のBeatプロセスに反映されない
- PersistentSchedulerはメモリ上の設定変更を認識しない

## 解決策

### 1. 短期的対応（現在実装済み）
- Beat起動時にデータベースから設定を読み込む
- 設定変更時はBeatの再起動が必要

### 2. 中期的対応（推奨）
- Celery Beat Schedulerを動的対応のものに変更
  - `celery-redbeat`: Redisベースの動的スケジューラー
  - カスタムDatabaseSchedulerの実装

### 3. 運用での対応
- スケジュール変更時にBeatを自動再起動する機能を追加
- 定期的なBeat再起動（例：毎日深夜）

## 実装例：Beat自動再起動

```python
# app/services/schedule_service.py に追加
async def restart_celery_beat(self):
    """Celery Beatを再起動"""
    import subprocess
    subprocess.run(["docker", "compose", "restart", "beat"])
```

これにより、UIからの設定変更を確実に反映できるようになります。