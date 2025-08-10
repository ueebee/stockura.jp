# 設計ファイル: listed_info タスクの cron 形式スケジューリング機能

## 1. アーキテクチャ概要

### 1.1 全体構成
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CLI/API       │────▶│  Schedule       │────▶│ Celery Beat     │
│  Interface      │     │  Manager        │     │ Scheduler       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Database      │     │ Celery Worker   │
                        │ (PostgreSQL)    │     │ (listed_info)   │
                        └─────────────────┘     └─────────────────┘
```

### 1.2 主要コンポーネント
1. **Schedule Manager**: スケジュール管理のビジネスロジック
2. **API Endpoints**: RESTful API for スケジュール管理
3. **CLI Commands**: コマンドラインインターフェース
4. **Database Models**: 既存の `celery_beat_schedules` テーブルを活用
5. **Celery Integration**: 既存の `fetch_listed_info_task` を活用

## 2. データモデル

### 2.1 既存テーブルの活用
```sql
-- 既存の celery_beat_schedules テーブル
-- id: UUID
-- name: String(255) - スケジュール名
-- task_name: String(255) - "fetch_listed_info_task"
-- cron_expression: String(100) - cron 形式の実行スケジュール
-- enabled: Boolean - 有効/無効フラグ
-- args: JSONB - 位置引数
-- kwargs: JSONB - キーワード引数（period_type 等）
-- description: Text - 説明
-- category: String(50) - カテゴリ（"listed_info"）
-- tags: JSONB - タグ
-- execution_policy: String(20) - 実行ポリシー
-- auto_generated_name: Boolean - 自動生成名フラグ
-- created_at: DateTime
-- updated_at: DateTime
```

### 2.2 kwargs の構造
```python
{
    "period_type": "yesterday" | "7days" | "30days" | "custom",
    "from_date": "2024-01-01",  # custom の場合
    "to_date": "2024-01-31",    # custom の場合
    "codes": ["7203", "7267"],  # オプション：特定銘柄のみ
    "market": "0111"            # オプション：特定市場のみ
}
```

## 3. API 設計

### 3.1 エンドポイント仕様

#### POST /api/v1/schedules/listed-info
```python
# Request Body
{
    "name": "daily_listed_info_fetch",
    "cron_expression": "0 9 * * *",
    "period_type": "yesterday",
    "description": "毎日 9 時に前日分のデータを取得",
    "enabled": true,
    "codes": [],  # 空の場合は全銘柄
    "market": null  # null の場合は全市場
}

# Response
{
    "id": "uuid",
    "name": "daily_listed_info_fetch",
    "cron_expression": "0 9 * * *",
    "period_type": "yesterday",
    "description": "毎日 9 時に前日分のデータを取得",
    "enabled": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

#### GET /api/v1/schedules/listed-info
```python
# Response
{
    "schedules": [
        {
            "id": "uuid",
            "name": "daily_listed_info_fetch",
            "cron_expression": "0 9 * * *",
            "period_type": "yesterday",
            "description": "毎日 9 時に前日分のデータを取得",
            "enabled": true,
            "last_run_at": "2024-01-01T09:00:00Z",
            "next_run_at": "2024-01-02T09:00:00Z"
        }
    ],
    "total": 1
}
```

#### PUT /api/v1/schedules/listed-info/{schedule_id}
#### DELETE /api/v1/schedules/listed-info/{schedule_id}
#### GET /api/v1/schedules/listed-info/{schedule_id}/history

## 4. 実装詳細

### 4.1 Use Case 層
```python
# app/application/use_cases/manage_listed_info_schedule.py
class ManageListedInfoScheduleUseCase:
    def __init__(self, schedule_repository: ScheduleRepository):
        self._schedule_repository = schedule_repository
    
    async def create_schedule(
        self,
        name: str,
        cron_expression: str,
        period_type: str,
        **kwargs
    ) -> Schedule:
        # cron 式の検証
        validate_cron_expression(cron_expression)
        
        # スケジュール作成
        schedule = Schedule(
            name=name,
            task_name="fetch_listed_info_task",
            cron_expression=cron_expression,
            kwargs={
                "period_type": period_type,
                **kwargs
            },
            category="listed_info",
            enabled=True
        )
        
        return await self._schedule_repository.save(schedule)
```

### 4.2 Repository 層
```python
# app/infrastructure/repositories/database/schedule_repository_impl.py
class ScheduleRepositoryImpl(ScheduleRepository):
    async def save(self, schedule: Schedule) -> Schedule:
        # 既存の CeleryBeatSchedule モデルを使用
        model = CeleryBeatSchedule(
            name=schedule.name,
            task_name=schedule.task_name,
            cron_expression=schedule.cron_expression,
            kwargs=schedule.kwargs,
            category=schedule.category,
            enabled=schedule.enabled
        )
        # DB 保存処理
        
    async def find_by_category(self, category: str) -> List[Schedule]:
        # カテゴリでフィルタリング
```

### 4.3 API 層
```python
# app/presentation/api/v1/endpoints/listed_info_schedules.py
router = APIRouter(prefix="/schedules/listed-info", tags=["listed_info_schedules"])

@router.post("/", response_model=ScheduleResponse)
async def create_listed_info_schedule(
    request: CreateListedInfoScheduleRequest,
    use_case: ManageListedInfoScheduleUseCase = Depends(get_use_case)
):
    schedule = await use_case.create_schedule(
        name=request.name,
        cron_expression=request.cron_expression,
        period_type=request.period_type,
        description=request.description,
        codes=request.codes,
        market=request.market
    )
    return ScheduleResponse.from_entity(schedule)
```

### 4.4 CLI 層
```python
# scripts/manage_listed_info_schedule.py
import click

@click.group()
def cli():
    """listed_info スケジュール管理コマンド"""
    pass

@cli.command()
@click.option('--name', required=True, help='スケジュール名')
@click.option('--cron', required=True, help='cron 形式の実行スケジュール')
@click.option('--period-type', required=True, 
              type=click.Choice(['yesterday', '7days', '30days', 'custom']))
def create(name: str, cron: str, period_type: str):
    """スケジュールを作成"""
    # 実装
```

## 5. cron 式の検証とヘルパー

### 5.1 cron 式バリデーター
```python
# app/domain/validators/cron_validator.py
from croniter import croniter

def validate_cron_expression(expression: str) -> bool:
    """cron 式の妥当性を検証"""
    try:
        croniter(expression)
        return True
    except:
        raise ValueError(f"Invalid cron expression: {expression}")

def get_next_run_time(cron_expression: str) -> datetime:
    """次回実行時刻を計算"""
    cron = croniter(cron_expression, datetime.now())
    return cron.get_next(datetime)
```

### 5.2 プリセットヘルパー
```python
# app/domain/helpers/schedule_presets.py
SCHEDULE_PRESETS = {
    "daily_morning": "0 9 * * *",      # 毎日朝 9 時
    "daily_evening": "0 18 * * *",     # 毎日夕方 6 時
    "weekly_monday": "0 9 * * 1",      # 毎週月曜 9 時
    "monthly_first": "0 9 1 * *",      # 毎月 1 日 9 時
    "business_days": "0 9 * * 1-5",    # 平日 9 時
}
```

## 6. エラーハンドリング

### 6.1 カスタム例外
```python
# app/domain/exceptions/schedule_exceptions.py
class ScheduleException(Exception):
    """スケジュール関連の基底例外"""
    pass

class InvalidCronExpressionException(ScheduleException):
    """無効な cron 式"""
    pass

class ScheduleConflictException(ScheduleException):
    """スケジュール名の重複"""
    pass
```

## 7. テスト戦略

### 7.1 単体テスト
- cron 式バリデーションのテスト
- Use Case のテスト
- Repository のテスト

### 7.2 統合テスト
- API エンドポイントのテスト
- CLI コマンドのテスト
- Celery Beat との統合テスト

### 7.3 E2E テスト
- スケジュール登録から実行までの一連の流れ
- 実行履歴の確認

## 8. セキュリティ考慮事項

### 8.1 認証・認可
- API エンドポイントには認証を必須とする
- スケジュール管理権限の確認

### 8.2 入力検証
- cron 式の厳密な検証
- period_type の値の検証
- SQL インジェクション対策

## 9. 運用考慮事項

### 9.1 ログ出力
- スケジュール登録/更新/削除時のログ
- 実行開始/終了のログ
- エラー発生時の詳細ログ

### 9.2 モニタリング
- スケジュール実行の成功/失敗率
- 実行時間の監視
- 次回実行予定の表示

### 9.3 バックアップ・リカバリ
- スケジュール設定のエクスポート/インポート機能
- 障害時の自動リトライ