# 実装計画ファイル: Celery Beat を用いた listed_info 定期取得機能

## 1. 実装順序と依存関係

### Phase 1: 基盤整備（1-2 日目）
1. Celery の基本設定
2. データベーススキーマの作成（マイグレーション）
3. 基本的なモデルとリポジトリの実装

### Phase 2: コア機能実装（3-4 日目）
4. listed_info 取得タスクの実装
5. ユースケース層の実装
6. カスタムスケジューラーの実装

### Phase 3: API 実装（5 日目）
7. スケジュール管理 API の実装
8. エラーハンドリングとログ機能

### Phase 4: テストと仕上げ（6 日目）
9. ユニットテストの作成
10. 統合テストの実装
11. ドキュメント作成

## 2. 詳細実装計画

### 2.1 Celery の基本設定

**ファイル作成:**
- `app/infrastructure/celery/__init__.py`
- `app/infrastructure/celery/app.py`
- `app/infrastructure/celery/config.py`

**実装内容:**
```python
# app/infrastructure/celery/app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery('stockura')
celery_app.config_from_object('app.infrastructure.celery.config')
```

### 2.2 データベーススキーマの作成

**ファイル作成:**
- `alembic/versions/xxx_add_celery_beat_tables.py`
- `app/infrastructure/database/models/schedule.py`
- `app/infrastructure/database/models/task_log.py`

**実装手順:**
1. SQLAlchemy モデルの定義
2. Alembic マイグレーションファイルの生成
3. マイグレーションの実行

### 2.3 リポジトリ実装

**ファイル作成:**
- `app/infrastructure/repositories/schedule_repository.py`
- `app/infrastructure/repositories/task_log_repository.py`
- `app/domain/repositories/schedule_repository_interface.py`
- `app/domain/repositories/task_log_repository_interface.py`

**実装内容:**
- CRUD 操作の実装
- 非同期対応（async/await）
- トランザクション管理

### 2.4 listed_info 取得タスクの実装

**ファイル作成:**
- `app/infrastructure/celery/tasks/__init__.py`
- `app/infrastructure/celery/tasks/listed_info_task.py`

**実装内容:**
```python
@celery_app.task(bind=True, max_retries=3)
def fetch_listed_info_task(self, schedule_id: str, **kwargs):
    # タスクロジックの実装
    pass
```

### 2.5 ユースケース層の実装

**ファイル作成:**
- `app/application/use_cases/fetch_listed_info_use_case.py`
- `app/domain/entities/schedule.py`
- `app/domain/entities/task_log.py`

**実装内容:**
- ビジネスロジックの実装
- 日付範囲の計算ロジック
- データ取得と保存の調整

### 2.6 カスタムスケジューラーの実装

**ファイル作成:**
- `app/infrastructure/celery/schedulers/__init__.py`
- `app/infrastructure/celery/schedulers/database_scheduler.py`

**実装内容:**
- celery-beat のカスタムスケジューラー
- DB からのスケジュール読み込み
- 動的なスケジュール更新

### 2.7 スケジュール管理 API の実装

**ファイル作成:**
- `app/api/v1/endpoints/schedules.py`
- `app/api/v1/schemas/schedule.py`
- `app/application/dto/schedule_dto.py`

**エンドポイント:**
- `GET /api/v1/schedules`
- `POST /api/v1/schedules`
- `GET /api/v1/schedules/{id}`
- `PUT /api/v1/schedules/{id}`
- `DELETE /api/v1/schedules/{id}`
- `POST /api/v1/schedules/{id}/enable`
- `POST /api/v1/schedules/{id}/disable`

### 2.8 エラーハンドリングとログ

**ファイル作成:**
- `app/infrastructure/celery/handlers.py`
- `app/infrastructure/logging/task_logger.py`

**実装内容:**
- タスク失敗時のハンドリング
- 構造化ログの実装
- メトリクスの収集

### 2.9 テスト実装

**ファイル作成:**
- `tests/unit/infrastructure/celery/test_listed_info_task.py`
- `tests/unit/application/use_cases/test_fetch_listed_info_use_case.py`
- `tests/integration/api/v1/test_schedules.py`
- `tests/integration/celery/test_database_scheduler.py`

**テスト内容:**
- タスクの単体テスト
- API 統合テスト
- スケジューラーの動作確認

### 2.10 設定とドキュメント

**ファイル作成:**
- `docs/CELERY_BEAT_SETUP.md`
- `.env.example` (更新)
- `docker-compose.yml` (Celery/Redis 追加)

## 3. 実装時の注意事項

### 3.1 非同期処理の扱い
- Celery タスク内で asyncio を使用する場合は、`asyncio.run()`を使用
- リポジトリは非同期版と同期版の両方を提供

### 3.2 エラーハンドリング
- API 呼び出しエラーは必ずリトライ
- DB エラーは即座に失敗として記録
- 部分的な成功も適切に処理

### 3.3 パフォーマンス
- 大量データはバッチ処理
- メモリ使用量に注意
- 適切なインデックスの設定

## 4. 環境設定

### 4.1 必要なパッケージ
```
celery==5.3.x
celery[redis]==5.3.x
flower==2.0.x
croniter==2.0.x
```

### 4.2 環境変数
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TIMEZONE=Asia/Tokyo
```

## 5. 動作確認手順

1. Redis の起動
2. Celery Worker の起動
3. Celery Beat の起動
4. API でスケジュール登録
5. タスク実行の確認
6. Flower での監視

## 6. リスクと対策

### リスク 1: スケジューラーの同期問題
- 対策: 分散ロックの実装

### リスク 2: タスクの重複実行
- 対策: タスク ID による重複チェック

### リスク 3: メモリ不足
- 対策: ストリーミング処理の実装