# Celery Beat タスク実行問題修正の実装計画

## 実装手順

### Phase 1: コアの修正（高優先度）

#### 1.1 DatabaseSchedulerAsyncPG クラスの修正
**ファイル**: `app/infrastructure/celery/schedulers/database_scheduler_asyncpg.py`

1. `tick()`メソッドのオーバーライド
   - 各スケジュールエントリーの`is_due`チェック
   - due なタスクの`apply_entry`呼び出し
   - エラーハンドリングの追加

2. `apply_entry()`メソッドの実装
   - 親クラスの`apply_entry`を呼び出してタスク送信
   - タスク送信ログの追加
   - エラーハンドリング

**推定作業時間**: 30 分

### Phase 2: ScheduleEntry の改善（中優先度）

#### 2.1 DatabaseScheduleEntry クラスの修正
**ファイル**: `app/infrastructure/celery/schedulers/database_scheduler_asyncpg.py`

1. `__next__()`メソッドの実装
   - 次回実行時刻の計算
   - Python 2/3 互換性の考慮

2. `is_due()`メソッドの改善
   - より詳細なログ出力
   - デバッグ情報の追加

**推定作業時間**: 20 分

### Phase 3: テストと検証

#### 3.1 手動テスト
1. Docker 環境での動作確認
   ```bash
   docker-compose up -d
   docker-compose logs -f celery-beat
   ```

2. テストスケジュールの作成
   - 1 分ごとに実行されるスケジュール
   - データベースへの直接挿入

3. 動作確認
   - Celery Beat のログ確認
   - Flower でのタスク実行確認
   - task_execution_logs テーブルの確認

**推定作業時間**: 30 分

### Phase 4: ドキュメント更新

#### 4.1 進捗ドキュメントの作成
**ファイル**: `cckiro/specs/fix-celery-beat-task-execution/progress.md`

1. 実装の進捗状況を記録
2. 発見した問題と解決策を記録
3. テスト結果を記録

#### 4.2 DOCKER_CELERY_DEBUG.md の更新
1. 解決した問題の記録
2. 今後の推奨事項の追加

**推定作業時間**: 15 分

## 実装の詳細

### 1. tick() メソッドの実装例

```python
def tick(self):
    """Run one iteration of the scheduler."""
    # スケジュール再読み込み
    if self._should_reload_schedules():
        self.sync_schedules()
    
    # 次回実行までの最小待機時間
    min_interval = self.max_interval
    
    # 各エントリーを処理
    for entry in self.schedule.values():
        is_due, next_run_seconds = entry.is_due()
        
        if is_due:
            logger.info(f"Task {entry.name} is due, applying entry")
            try:
                self.apply_entry(entry)
            except Exception as e:
                logger.error(f"Failed to apply entry {entry.name}: {e}", exc_info=True)
        
        # 次回実行までの最小時間を更新
        min_interval = min(min_interval, next_run_seconds)
    
    return min_interval
```

### 2. apply_entry() メソッドの実装例

```python
def apply_entry(self, entry, producer=None):
    """Apply schedule entry - send task to worker."""
    logger.info(f"Applying entry: {entry.name}, task: {entry.task}, "
                f"args: {entry.args}, kwargs: {entry.kwargs}")
    
    try:
        # 親クラスの apply_entry を呼び出す
        result = super().apply_entry(entry, producer)
        logger.info(f"Task {entry.name} sent successfully")
        return result
    except Exception as e:
        logger.error(f"Failed to send task {entry.name}: {e}", exc_info=True)
        raise
```

## 成功基準

1. **機能面**
   - スケジュールに登録されたタスクが実行される
   - Celery Beat ログに"Applying entry"メッセージが表示される
   - Flower でタスクの実行が確認できる

2. **品質面**
   - エラーが発生してもスケジューラーが停止しない
   - 適切なログが出力される
   - 既存の機能に影響がない

## リスクと対処

1. **リスク**: 親クラスのメソッドとの互換性問題
   - **対処**: Celery のソースコードを参照して実装
   - **確認方法**: デバッグログで動作確認

2. **リスク**: タスクの重複実行
   - **対処**: entry.last_run_at の適切な管理
   - **確認方法**: task_execution_logs で重複チェック

## 総作業時間見積もり

- Phase 1: 30 分
- Phase 2: 20 分
- Phase 3: 30 分
- Phase 4: 15 分
- **合計**: 約 1 時間 35 分