# Presentation 層のクリーンアーキテクチャ改善 - 設計書（第 1 回：依存性注入の改善）

## 1. 設計概要

本設計書は、 Presentation 層における依存性注入の改善に焦点を当てた設計を記述します。
クリーンアーキテクチャの原則に従い、 Presentation 層がインフラストラクチャ層の具体的な実装に依存しないよう改善します。

## 2. 現状の問題点

### 2.1 schedules.py の問題点
```python
# 現状：インフラストラクチャ層の具体的な実装を直接インポート
from app.infrastructure.repositories.database.schedule_repository import ScheduleRepositoryImpl
from app.infrastructure.repositories.database.task_log_repository import TaskLogRepository
from app.infrastructure.celery.tasks.listed_info_task import fetch_listed_info_task

# エンドポイント内で直接インスタンス化
repository = ScheduleRepositoryImpl(session)
```

### 2.2 auth.py の問題点
```python
# 現状：具体的な実装を直接インポート
from app.infrastructure.repositories.redis.auth_repository_impl import RedisAuthRepository

# get_auth_repository 内で具体的な実装を返している
return RedisAuthRepository(redis_client)
```

## 3. 設計方針

### 3.1 依存性の逆転
- Presentation 層は Domain 層のインターフェースのみに依存する
- 具体的な実装への依存は、依存性注入コンテナ（providers）で解決する

### 3.2 ディレクトリ構造
```
app/presentation/
├── dependencies/
│   ├── __init__.py
│   ├── auth.py          # 認証関連の依存性
│   ├── repositories.py  # リポジトリの依存性
│   ├── use_cases.py     # ユースケースの依存性
│   └── services.py      # その他サービスの依存性
```

## 4. 詳細設計

### 4.1 リポジトリの依存性注入

#### 4.1.1 presentation/dependencies/repositories.py
```python
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.schedule_repository_interface import ScheduleRepositoryInterface
from app.domain.repositories.task_log_repository_interface import TaskLogRepositoryInterface
from app.domain.repositories.auth_repository_interface import AuthRepositoryInterface
from app.infrastructure.database.connection import get_session
from app.infrastructure.redis.redis_client import get_redis_client

# 実装クラスは動的にインポート（設定に基づいて切り替え可能）
def get_schedule_repository(
    session: AsyncSession = Depends(get_session)
) -> ScheduleRepositoryInterface:
    """スケジュールリポジトリの依存性注入"""
    from app.infrastructure.repositories.database.schedule_repository import ScheduleRepositoryImpl
    return ScheduleRepositoryImpl(session)

def get_task_log_repository(
    session: AsyncSession = Depends(get_session)
) -> TaskLogRepositoryInterface:
    """タスクログリポジトリの依存性注入"""
    from app.infrastructure.repositories.database.task_log_repository import TaskLogRepository
    return TaskLogRepository(session)

async def get_auth_repository() -> AuthRepositoryInterface:
    """認証リポジトリの依存性注入"""
    from app.infrastructure.repositories.redis.auth_repository_impl import RedisAuthRepository
    redis_client = await get_redis_client()
    return RedisAuthRepository(redis_client)
```

### 4.2 ユースケースの依存性注入

#### 4.2.1 presentation/dependencies/use_cases.py
```python
from fastapi import Depends
from typing import Optional

from app.application.use_cases.manage_schedule import ManageScheduleUseCase
from app.application.use_cases.auth_use_case import AuthUseCase
from app.domain.repositories.schedule_repository_interface import ScheduleRepositoryInterface
from app.domain.repositories.auth_repository_interface import AuthRepositoryInterface
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher
from .repositories import get_schedule_repository, get_auth_repository
from .services import get_schedule_event_publisher

def get_manage_schedule_use_case(
    repository: ScheduleRepositoryInterface = Depends(get_schedule_repository),
    event_publisher: Optional[ScheduleEventPublisher] = Depends(get_schedule_event_publisher),
) -> ManageScheduleUseCase:
    """スケジュール管理ユースケースの依存性注入"""
    return ManageScheduleUseCase(repository, event_publisher=event_publisher)

def get_auth_use_case(
    auth_repository: AuthRepositoryInterface = Depends(get_auth_repository),
) -> AuthUseCase:
    """認証ユースケースの依存性注入"""
    return AuthUseCase(auth_repository)
```

### 4.3 サービスの依存性注入

#### 4.3.1 presentation/dependencies/services.py
```python
from typing import Optional
import logging

from app.core.config import get_settings
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher
from app.infrastructure.redis.redis_client import get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()

async def get_schedule_event_publisher() -> Optional[ScheduleEventPublisher]:
    """スケジュールイベントパブリッシャーの依存性注入"""
    if not settings.celery_beat_redis_sync_enabled:
        logger.debug("Redis sync is disabled, returning None for ScheduleEventPublisher")
        return None
        
    try:
        redis_client = await get_redis_client()
        return ScheduleEventPublisher(redis_client)
    except Exception as e:
        logger.error(f"Failed to create ScheduleEventPublisher: {e}")
        return None
```

### 4.4 エンドポイントの修正

#### 4.4.1 schedules.py の修正
```python
# Before: インフラストラクチャ層の具体的な実装をインポート
# from app.infrastructure.repositories.database.schedule_repository import ScheduleRepositoryImpl
# from app.infrastructure.repositories.database.task_log_repository import TaskLogRepository

# After: 依存性注入プロバイダーのみをインポート
from app.presentation.dependencies.use_cases import get_manage_schedule_use_case
from app.presentation.dependencies.repositories import get_task_log_repository

# エンドポイントでは依存性注入を使用
@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
) -> ScheduleResponse:
    # 実装は変更なし
```

#### 4.4.2 auth.py の修正
```python
# Before: 具体的な実装をインポート
# from app.infrastructure.repositories.redis.auth_repository_impl import RedisAuthRepository

# After: 依存性注入プロバイダーのみをインポート
from app.presentation.dependencies.use_cases import get_auth_use_case

# 既存の get_auth_repository 関数は削除し、 dependencies モジュールのものを使用
```

## 5. 移行計画

### 5.1 フェーズ 1: 依存性注入の基盤整備
1. `presentation/dependencies`ディレクトリの作成
2. 各依存性注入プロバイダーの実装

### 5.2 フェーズ 2: エンドポイントの移行
1. schedules.py の移行
2. auth.py の移行
3. listed_info_schedules.py の移行（存在する場合）

### 5.3 フェーズ 3: 既存プロバイダーの移行
1. `infrastructure/di/providers.py`の内容を`presentation/dependencies`に移行
2. 古いプロバイダーファイルの削除

## 6. テスト戦略

### 6.1 単体テスト
- 各依存性注入プロバイダーのテストを作成
- モックを使用した依存性の差し替えテスト

### 6.2 統合テスト
- 既存の API テストが全て通ることを確認
- 依存性注入が正しく機能することを確認

## 7. リスクと対策

### 7.1 リスク
- 循環インポートの可能性
- 既存の機能への影響

### 7.2 対策
- 動的インポートを使用して循環インポートを回避
- 段階的な移行により、各ステップで動作確認を実施

---

この設計に問題がないか確認してください。問題がある場合は、修正すべき点を教えてください。