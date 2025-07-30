# Celery Beat タスク実行問題修正の設計

## 概要

カスタムスケジューラー `DatabaseSchedulerAsyncPG` がタスクを正しく送信できない問題を修正する設計。

## 問題分析

### 現在の実装の問題点

1. **ScheduleEntry の不完全な実装**
   - `DatabaseScheduleEntry`クラスが`ScheduleEntry`を継承しているが、親クラスの期待する動作を完全に実装していない
   - 特に`__next__()`メソッドや`update()`メソッドが適切にオーバーライドされていない

2. **last_run_at の管理問題**
   - `last_run_at`が None に初期化されているが、タスク実行後に更新されていない
   - これにより、同じタスクが重複して実行される可能性がある

3. **apply_entry() メソッドの欠如**
   - Celery のスケジューラーは`apply_entry()`メソッドを呼び出してタスクを送信するが、このメソッドが実装されていない

## 設計方針

### 1. 最小限の修正アプローチ

既存のコードベースへの影響を最小限に抑えながら、問題を解決する。

### 2. Celery 標準の動作に準拠

Celery の標準的な Scheduler クラスの動作に準拠し、互換性を保つ。

## 詳細設計

### 1. DatabaseScheduleEntry クラスの修正

```python
class DatabaseScheduleEntry(ScheduleEntry):
    """Schedule entry that reads from database."""
    
    def __init__(self, schedule_model: CeleryBeatSchedule, app=None):
        # 既存の初期化処理
        ...
        # last_run_at をデータベースから復元（永続化対応）
        self.last_run_at = schedule_model.last_run_at
    
    def __next__(self):
        """Calculate next run time."""
        # 親クラスのメソッドを呼び出す
        return self.__class__(self.model, app=self.app)
    
    next = __next__  # Python 2/3 互換性のため
```

### 2. DatabaseSchedulerAsyncPG クラスの修正

```python
class DatabaseSchedulerAsyncPG(Scheduler):
    """Custom scheduler that reads schedules from database using asyncpg."""
    
    def apply_entry(self, entry, producer=None):
        """Apply schedule entry - send task to worker."""
        # タスク送信のログ
        logger.info(f"Sending task {entry.name} to worker")
        
        # 親クラスの apply_entry を呼び出す
        result = super().apply_entry(entry, producer)
        
        # last_run_at をデータベースに保存
        self._update_last_run_at(entry)
        
        return result
    
    def _update_last_run_at(self, entry):
        """Update last_run_at in database."""
        # 非同期でデータベースを更新
        asyncio.run_coroutine_threadsafe(
            self._update_last_run_at_async(entry.name, entry.last_run_at),
            self._event_loop
        )
```

### 3. データベーススキーマの考慮

現在の`celery_beat_schedules`テーブルに`last_run_at`カラムがない場合の対応：

1. **Option A**: メモリ内でのみ管理（再起動時にリセット）
2. **Option B**: 別テーブルで管理
3. **Option C**: 既存テーブルにカラム追加（マイグレーション必要）

推奨：**Option A**（最小限の変更で問題を解決）

### 4. エラーハンドリングとログ

```python
def tick(self):
    """Run one iteration of the scheduler."""
    try:
        # スケジュール再読み込み
        if self._should_reload_schedules():
            self.sync_schedules()
        
        # 各エントリーを処理
        for entry in self.schedule.values():
            is_due, next_run_seconds = entry.is_due()
            if is_due:
                logger.debug(f"Task {entry.name} is due, sending to worker")
                try:
                    self.apply_entry(entry)
                except Exception as e:
                    logger.error(f"Failed to send task {entry.name}: {e}")
        
        # 次回実行までの待機時間を計算
        return self.max_interval
        
    except Exception as e:
        logger.error(f"Error in scheduler tick: {e}", exc_info=True)
        return self.max_interval
```

## 実装の優先順位

1. **高優先度**
   - `apply_entry()`メソッドの実装
   - `tick()`メソッドのオーバーライド
   - エラーハンドリングとログの追加

2. **中優先度**
   - `last_run_at`の管理改善
   - `__next__()`メソッドの実装

3. **低優先度**
   - データベースへの`last_run_at`永続化
   - パフォーマンスの最適化

## テスト戦略

1. **単体テスト**
   - スケジューラーの各メソッドのテスト
   - エラーケースのテスト

2. **統合テスト**
   - Docker 環境での動作確認
   - 実際のタスク実行確認

3. **手動テスト**
   - 1 分ごとのスケジュール設定でのテスト
   - Flower での監視
   - ログの確認

## リスクと対策

1. **リスク**: 既存のスケジューラー動作への影響
   - **対策**: 最小限の変更に留める、十分なテスト

2. **リスク**: タスクの重複実行
   - **対策**: `last_run_at`の適切な管理

3. **リスク**: パフォーマンスの低下
   - **対策**: 非同期処理の活用、適切なログレベル