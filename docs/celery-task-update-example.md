# Celeryタスクの更新例

## 推奨される修正方法

既存のCeleryタスクを更新する場合、以下のいずれかの方法を使用してください：

### オプション1: 既存のasync_session_makerを使用（NullPool設定済み）

現在の実装のままでも動作します。`app/db/session.py`で`NullPool`を設定したため、イベントループの競合は発生しません。

```python
# 現在の実装（これでも動作します）
async def _sync():
    async with async_session_maker() as db:
        # データベース操作
        pass

result = asyncio.run(_sync())
```

### オプション2: Celery専用セッションメーカーを使用（推奨）

より明示的で、将来的な変更に強い方法です：

```python
from app.db.session import get_celery_async_session_maker

@celery_app.task(bind=True)
def sync_daily_quotes_task(self, ...):
    # ...
    
    async def _sync():
        # Celery専用のセッションメーカーを取得
        celery_session_maker = get_celery_async_session_maker()
        
        async with celery_session_maker() as db:
            # サービスの初期化
            data_source_service = DataSourceService(db)
            # ... 残りの処理
    
    # asyncio.run()を使用（これは問題ありません）
    result = asyncio.run(_sync())
```

## 重要なポイント

1. **新しいイベントループの作成は問題ない**: `asyncio.run()`や`asyncio.new_event_loop()`の使用は継続できます
2. **NullPoolが鍵**: 接続プーリングを無効化することで、イベントループ間の競合を防ぎます
3. **パフォーマンスへの影響は最小限**: Celeryタスクは通常長時間実行されるため、接続のオーバーヘッドは相対的に小さい

## 移行の優先順位

1. **エラーが発生しているタスク**: 最優先で修正
2. **頻繁に実行されるタスク**: パフォーマンスを監視しながら更新
3. **新規タスク**: 最初から`get_celery_async_session_maker()`を使用

## 注意事項

- 通常のFastAPIエンドポイントでは従来の`async_session_maker`を使用してください
- Celeryタスク内でのみ、この特別な処理が必要です
- 将来的にCeleryがasyncioをネイティブサポートした場合、この回避策は不要になる可能性があります