# SQLAlchemy AsyncioイベントループエラーのCeleryとの解決方法

## 問題の概要

Celeryタスク内でSQLAlchemyの非同期セッション（`AsyncSession`）を使用すると、以下のエラーが発生することがあります：

```
Task got Future <Future pending> attached to a different loop
```

## 原因

このエラーは、SQLAlchemyの`async_engine`が作成されたイベントループと、Celeryタスクが実行されるイベントループが異なるために発生します。

具体的には：
1. `async_session_maker`はモジュールレベルで作成され、特定のイベントループにバインドされる
2. Celeryタスクは`asyncio.run()`や`asyncio.new_event_loop()`で新しいイベントループを作成する
3. 異なるイベントループ間でFutureオブジェクトを使用しようとするとエラーが発生する

## 解決方法

### 1. NullPoolを使用する（実装済み）

`app/db/session.py`で、非同期エンジンに`NullPool`を設定しました：

```python
from sqlalchemy.pool import NullPool

async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DATABASE_ECHO,
    future=True,
    poolclass=NullPool,  # Celeryタスクでのイベントループ競合を防ぐ
    pool_pre_ping=True,
)
```

`NullPool`は接続プーリングを無効化し、各リクエストで新しい接続を作成します。これにより、異なるイベントループ間での競合を防ぎます。

### 2. Celery専用のセッションメーカーを使用する（推奨）

より柔軟なアプローチとして、`get_celery_async_session_maker()`関数を追加しました：

```python
def get_celery_async_session_maker():
    """
    Celeryタスク専用の非同期セッションメーカーを取得します。
    """
    celery_async_engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=settings.DATABASE_ECHO,
        future=True,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    
    return async_sessionmaker(
        celery_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
```

## 使用例

### Celeryタスクでの使用

```python
@celery_app.task(bind=True)
def sync_data_task(self):
    async def _sync():
        # Celery専用のセッションメーカーを取得
        celery_session_maker = get_celery_async_session_maker()
        
        async with celery_session_maker() as db:
            # データベース操作を実行
            result = await db.execute(select(Model))
            return result.all()
    
    # 新しいイベントループで実行
    return asyncio.run(_sync())
```

## パフォーマンスへの影響

`NullPool`を使用することで、接続プーリングの利点が失われますが：
- Celeryタスクは通常、長時間実行されるため、接続のオーバーヘッドは相対的に小さい
- イベントループエラーを回避できる確実性の方が重要
- 必要に応じて、将来的により洗練されたソリューションに移行可能

## 参考資料

- [SQLAlchemy AsyncIO Integration](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html)
- [Python asyncio Event Loops](https://docs.python.org/3/library/asyncio-eventloop.html)