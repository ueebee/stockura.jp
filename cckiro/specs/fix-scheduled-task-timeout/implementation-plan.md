# 実装計画: スケジュールタスクのタイムアウト問題の解決

## 1. 実装タスクの概要

### フェーズ 1: 基盤実装（推定作業時間: 2 時間）
1. Redis 接続の設定と環境変数の追加
2. ScheduleEventPublisher クラスの実装
3. 単体テストの作成

### フェーズ 2: Celery Beat 拡張（推定作業時間: 3 時間）
1. DatabaseSchedulerAsyncPG への Redis サブスクライバー追加
2. イベントハンドリングと同期処理の実装
3. エラーハンドリングとログ強化

### フェーズ 3: API 統合（推定作業時間: 2 時間）
1. 依存性注入の設定
2. UseCase へのイベント発行機能追加
3. API エンドポイントの統合

### フェーズ 4: テストと検証（推定作業時間: 2 時間）
1. 単体テストの実装
2. 統合テストの実装
3. エンドツーエンドテストの実行

## 2. 詳細な実装手順

### Step 1: 環境設定の更新

#### 1.1 環境変数の追加
**ファイル**: `.env.example`, `.env`
```bash
# Celery Beat Redis Sync
CELERY_BEAT_REDIS_SYNC_ENABLED=true
CELERY_BEAT_MIN_SYNC_INTERVAL=5
CELERY_BEAT_REDIS_CHANNEL=celery_beat_schedule_updates
```

#### 1.2 設定クラスの更新
**ファイル**: `app/core/config.py`
```python
class Settings(BaseSettings):
    # 既存の設定...
    
    # Celery Beat Redis Sync
    celery_beat_redis_sync_enabled: bool = Field(default=True)
    celery_beat_min_sync_interval: int = Field(default=5)
    celery_beat_redis_channel: str = Field(default="celery_beat_schedule_updates")
```

### Step 2: ScheduleEventPublisher の実装

#### 2.1 イベントパブリッシャークラスの作成
**新規ファイル**: `app/infrastructure/events/schedule_event_publisher.py`
```python
"""Schedule event publisher for Redis Pub/Sub."""
import json
import logging
from datetime import datetime
from typing import Optional

from redis import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ScheduleEventPublisher:
    """Publish schedule events to Redis."""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize the publisher."""
        self.redis = redis_client
        self.channel = settings.celery_beat_redis_channel
        self.enabled = settings.celery_beat_redis_sync_enabled
        
    async def publish_schedule_created(self, schedule_id: str):
        """Publish schedule created event."""
        if not self.enabled or not self.redis:
            return
            
        try:
            event = {
                "event_type": "schedule_created",
                "schedule_id": schedule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.redis.publish(self.channel, json.dumps(event))
            logger.info(f"Published schedule_created event for {schedule_id}")
        except Exception as e:
            logger.error(f"Failed to publish schedule_created event: {e}")
            # Don't raise - fail silently to maintain backward compatibility
```

### Step 3: DatabaseSchedulerAsyncPG の拡張

#### 3.1 Redis サブスクライバーの追加
**更新ファイル**: `app/infrastructure/celery/schedulers/database_scheduler_asyncpg.py`

主な変更点:
- Redis サブスクライバースレッドの追加
- イベント受信時の即時同期機能
- 最小同期間隔の制御

### Step 4: 依存性注入の設定

#### 4.1 DI コンテナの設定
**新規ファイル**: `app/infrastructure/di/providers.py`
```python
"""Dependency injection providers."""
from typing import Optional

from redis import Redis

from app.core.config import get_settings
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher
from app.infrastructure.redis.connection import get_redis_client

settings = get_settings()


def get_schedule_event_publisher() -> Optional[ScheduleEventPublisher]:
    """Get schedule event publisher instance."""
    if not settings.celery_beat_redis_sync_enabled:
        return None
        
    try:
        redis_client = get_redis_client()
        return ScheduleEventPublisher(redis_client)
    except Exception as e:
        logger.error(f"Failed to create ScheduleEventPublisher: {e}")
        return None
```

### Step 5: UseCase の更新

#### 5.1 ManageListedInfoScheduleUseCase の修正
**更新ファイル**: `app/application/use_cases/manage_listed_info_schedule.py`

変更内容:
- コンストラクタに event_publisher パラメータを追加
- create_schedule, update_schedule, delete_schedule メソッドでイベント発行

### Step 6: API エンドポイントの更新

#### 6.1 依存性注入の適用
**更新ファイル**: `app/presentation/api/v1/endpoints/schedules.py`

```python
from app.infrastructure.di.providers import get_schedule_event_publisher

@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db_session: AsyncSession = Depends(get_async_session),
    event_publisher: Optional[ScheduleEventPublisher] = Depends(get_schedule_event_publisher)
):
    """Create a new schedule."""
    use_case = ManageListedInfoScheduleUseCase(
        schedule_repository=ScheduleRepository(db_session),
        event_publisher=event_publisher
    )
    # 以下既存のコード...
```

### Step 7: テストの実装

#### 7.1 単体テスト
**新規ファイル**: `tests/unit/test_schedule_event_publisher.py`
- モックを使用したイベント発行のテスト
- エラーハンドリングのテスト

#### 7.2 統合テスト
**新規ファイル**: `tests/integration/test_schedule_redis_sync.py`
- 実際の Redis 接続を使用したテスト
- スケジュール作成から同期までのフローテスト

## 3. 実装の優先順位

1. **必須実装**（最小限の動作に必要）
   - ScheduleEventPublisher
   - DatabaseSchedulerAsyncPG の Redis サブスクライバー
   - UseCase へのイベント発行追加

2. **推奨実装**（品質向上）
   - エラーハンドリングの強化
   - ログの充実
   - 単体テスト

3. **オプション実装**（さらなる改善）
   - メトリクスの追加
   - パフォーマンス最適化
   - 統合テストの充実

## 4. リスクと対策

### リスク 1: Redis 接続の失敗
- **対策**: フォールバックとして従来の 60 秒同期を維持
- **実装**: try-except でエラーをキャッチし、ログ出力のみ

### リスク 2: 高頻度の同期によるパフォーマンス低下
- **対策**: 最小同期間隔（5 秒）の設定
- **実装**: last_sync_time を記録し、間隔をチェック

### リスク 3: 既存システムとの互換性
- **対策**: 環境変数による機能の有効/無効切り替え
- **実装**: CELERY_BEAT_REDIS_SYNC_ENABLED フラグ

## 5. 検証項目

### 機能検証
- [ ] スケジュール作成後、 5 秒以内にタスクが認識される
- [ ] `test_scheduled_listed_info_api.py`がタイムアウトせずに成功
- [ ] Redis 接続エラー時も既存機能が動作

### パフォーマンス検証
- [ ] 100 個のスケジュール同時作成時の動作
- [ ] CPU/メモリ使用率の確認
- [ ] データベース負荷の確認

### 互換性検証
- [ ] 既存のスケジュールが正常に動作
- [ ] API の後方互換性
- [ ] 設定変更なしでの動作

## 6. ロールバック計画

万が一問題が発生した場合：

1. **即時対応**: 環境変数 `CELERY_BEAT_REDIS_SYNC_ENABLED=false` で機能を無効化
2. **コード復旧**: Git で feature ブランチを revert
3. **データ復旧**: スケジュールデータに変更はないため不要

## 7. 完了基準

- [ ] 全ての必須実装が完了
- [ ] 単体テストがすべてパス
- [ ] `test_scheduled_listed_info_api.py`が成功
- [ ] コードレビューの完了
- [ ] ドキュメントの更新