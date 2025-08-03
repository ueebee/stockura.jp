# タスクスケジューリング改善設計ファイル

## 概要

本設計では、 Celery Beat のスケジューリング機能を拡張し、同一タスクを異なるパラメータで複数スケジュール登録できるようにします。また、タスクの分類管理、パラメータバリデーション、重複実行防止などの機能を追加します。

## アーキテクチャ設計

### 1. データベーススキーマ変更

#### 1.1 既存のテーブル修正

**celery_beat_schedules テーブル**
```sql
-- name フィールドの UNIQUE 制約を削除
ALTER TABLE celery_beat_schedules DROP CONSTRAINT celery_beat_schedules_name_key;

-- name フィールドにインデックスを追加（検索性能のため）
CREATE INDEX idx_celery_beat_schedules_name ON celery_beat_schedules(name);

-- 新しいカラムの追加
ALTER TABLE celery_beat_schedules 
ADD COLUMN category VARCHAR(50),
ADD COLUMN tags JSONB DEFAULT '[]'::jsonb,
ADD COLUMN execution_policy VARCHAR(20) DEFAULT 'allow' CHECK (execution_policy IN ('allow', 'skip', 'queue')),
ADD COLUMN auto_generated_name BOOLEAN DEFAULT FALSE;
```

#### 1.2 新しいテーブル

**task_definitions テーブル（新規）**
```sql
CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(50),
    description TEXT,
    parameter_schema JSONB,  -- JSON Schema 形式でパラメータを定義
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. ドメインモデル設計

#### 2.1 TaskDefinition エンティティ（新規）

```python
@dataclass
class TaskDefinition:
    """タスク定義エンティティ"""
    id: UUID
    task_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

#### 2.2 Schedule エンティティ（修正）

```python
@dataclass
class Schedule:
    """Schedule entity for Celery Beat tasks."""
    id: UUID
    name: str
    task_name: str
    cron_expression: str
    enabled: bool = True
    args: List[Any] = None
    kwargs: Dict[str, Any] = None
    description: Optional[str] = None
    category: Optional[str] = None  # 追加
    tags: List[str] = None  # 追加
    execution_policy: str = "allow"  # 追加: allow, skip, queue
    auto_generated_name: bool = False  # 追加
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### 3. ユースケース設計

#### 3.1 CreateScheduleUseCase（修正）

```python
class CreateScheduleUseCase:
    def __init__(
        self,
        schedule_repo: ScheduleRepositoryInterface,
        task_definition_repo: TaskDefinitionRepositoryInterface,
        name_generator: ScheduleNameGenerator,
    ):
        self._schedule_repo = schedule_repo
        self._task_definition_repo = task_definition_repo
        self._name_generator = name_generator

    async def execute(self, dto: CreateScheduleDTO) -> ScheduleDTO:
        # 1. タスク定義の取得
        task_def = await self._task_definition_repo.get_by_task_name(dto.task_name)
        
        # 2. パラメータバリデーション
        if task_def and task_def.parameter_schema:
            self._validate_parameters(dto.task_params, task_def.parameter_schema)
        
        # 3. スケジュール名の生成（必要な場合）
        if not dto.name:
            dto.name = self._name_generator.generate(
                task_name=dto.task_name,
                params=dto.task_params,
                cron_expression=dto.cron_expression
            )
            auto_generated_name = True
        else:
            auto_generated_name = False
        
        # 4. カテゴリーの設定（指定がない場合はタスク定義から）
        if not dto.category and task_def:
            dto.category = task_def.category
        
        # 5. Schedule エンティティの作成
        schedule = Schedule(
            id=uuid4(),
            name=dto.name,
            task_name=dto.task_name,
            cron_expression=dto.cron_expression,
            enabled=dto.enabled,
            kwargs=dto.task_params or {},
            description=dto.description,
            category=dto.category,
            tags=dto.tags or [],
            execution_policy=dto.execution_policy or "allow",
            auto_generated_name=auto_generated_name,
        )
        
        # 6. 保存
        created = await self._schedule_repo.create(schedule)
        return ScheduleDTO.from_entity(created)
```

#### 3.2 TaskExecutionController（新規）

重複実行防止のための制御クラス：

```python
class TaskExecutionController:
    def __init__(self, cache_client: Redis):
        self._cache = cache_client
    
    async def can_execute(
        self, 
        task_name: str, 
        params: Dict[str, Any], 
        policy: str
    ) -> bool:
        """タスクが実行可能かチェック"""
        if policy == "allow":
            return True
        
        lock_key = self._generate_lock_key(task_name, params)
        
        if policy == "skip":
            # 実行中なら False を返す
            return not await self._is_locked(lock_key)
        
        elif policy == "queue":
            # キューイング実装（簡易版）
            # 実際の実装では、 Redis の List を使ってキューを実装
            return await self._wait_for_lock(lock_key)
    
    async def acquire_lock(
        self, 
        task_name: str, 
        params: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """実行ロックを取得"""
        lock_key = self._generate_lock_key(task_name, params)
        return await self._cache.set(lock_key, "1", ex=ttl, nx=True)
    
    async def release_lock(self, task_name: str, params: Dict[str, Any]):
        """実行ロックを解放"""
        lock_key = self._generate_lock_key(task_name, params)
        await self._cache.delete(lock_key)
    
    def _generate_lock_key(self, task_name: str, params: Dict[str, Any]) -> str:
        """タスク名とパラメータからロックキーを生成"""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"task_lock:{task_name}:{params_hash}"
```

### 4. API スキーマ設計

#### 4.1 リクエストスキーマ（修正）

```python
class ScheduleCreate(BaseModel):
    """Create schedule request schema."""
    name: Optional[str] = Field(None, description="Schedule name (auto-generated if not provided)")
    task_name: str = Field(..., description="Task name to execute")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")
    task_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    description: Optional[str] = Field(None, description="Schedule description")
    category: Optional[str] = Field(None, description="Task category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for filtering")
    execution_policy: Optional[str] = Field(
        default="allow",
        regex="^(allow|skip|queue)$",
        description="Execution policy when task is already running"
    )
```

#### 4.2 レスポンススキーマ（修正）

```python
class ScheduleResponse(BaseModel):
    """Schedule response schema."""
    id: str
    name: str
    task_name: str
    cron_expression: str
    enabled: bool
    task_params: Dict[str, Any]
    description: Optional[str]
    category: Optional[str]
    tags: List[str]
    execution_policy: str
    auto_generated_name: bool
    created_at: datetime
    updated_at: datetime
```

### 5. タスク実装の修正

```python
@celery_app.task(bind=True, base=FetchListedInfoTask)
def fetch_listed_info_task_asyncpg(
    self,
    schedule_id: Optional[str] = None,
    schedule_name: Optional[str] = None,  # 追加
    execution_policy: Optional[str] = "allow",  # 追加
    # ... 既存のパラメータ
):
    """タスク実装の修正"""
    # 実行制御
    if execution_policy != "allow":
        controller = TaskExecutionController(redis_client)
        params = {
            "period_type": period_type,
            "from_date": from_date,
            "to_date": to_date,
            "codes": codes,
            "market": market,
        }
        
        if not await controller.can_execute(self.name, params, execution_policy):
            logger.info(f"Task skipped due to execution policy: {execution_policy}")
            return {"status": "skipped", "reason": "already_running"}
        
        # ロックを取得
        await controller.acquire_lock(self.name, params)
    
    try:
        # 既存の処理
        result = await _fetch_listed_info_async(
            task_id=task_id,
            log_id=log_id,
            schedule_id=schedule_id,
            schedule_name=schedule_name,  # 追加
            # ... 既存のパラメータ
        )
        return result
    finally:
        if execution_policy != "allow":
            await controller.release_lock(self.name, params)
```

### 6. スケジュール名自動生成

```python
class ScheduleNameGenerator:
    """スケジュール名の自動生成"""
    
    def generate(
        self, 
        task_name: str, 
        params: Dict[str, Any], 
        cron_expression: str
    ) -> str:
        # タスク名の短縮形を取得
        task_short = self._shorten_task_name(task_name)
        
        # パラメータから重要な情報を抽出
        param_info = self._extract_param_info(task_name, params)
        
        # cron 式から頻度を解析
        frequency = self._parse_frequency(cron_expression)
        
        # 名前を組み立て
        parts = [task_short]
        if param_info:
            parts.append(param_info)
        if frequency:
            parts.append(frequency)
        
        return "_".join(parts)
    
    def _shorten_task_name(self, task_name: str) -> str:
        """タスク名を短縮"""
        # 例: fetch_listed_info_task_asyncpg -> fetch_listed_info
        if task_name.endswith("_task_asyncpg"):
            return task_name[:-13]
        elif task_name.endswith("_task"):
            return task_name[:-5]
        return task_name
    
    def _extract_param_info(self, task_name: str, params: Dict[str, Any]) -> str:
        """パラメータから重要な情報を抽出"""
        if "fetch_listed_info" in task_name:
            period_type = params.get("period_type", "")
            if period_type:
                return period_type
        # 他のタスクタイプに応じた処理
        return ""
    
    def _parse_frequency(self, cron_expression: str) -> str:
        """cron 式から頻度を解析"""
        if cron_expression == "* * * * *":
            return "every_minute"
        elif cron_expression == "0 * * * *":
            return "hourly"
        elif cron_expression == "0 0 * * *":
            return "daily"
        elif cron_expression == "0 0 * * 0":
            return "weekly"
        elif cron_expression == "0 0 1 * *":
            return "monthly"
        else:
            return "custom"
```

## 実装の優先順位

1. **Phase 1: コア機能（必須）**
   - データベーススキーマの変更
   - Schedule エンティティの修正
   - CreateScheduleUseCase の修正
   - API エンドポイントの修正

2. **Phase 2: 拡張機能（推奨）**
   - TaskDefinition の実装
   - パラメータバリデーション
   - スケジュール名自動生成

3. **Phase 3: 高度な機能（オプション）**
   - 実行ポリシー（重複実行防止）
   - タスクカテゴリー・タグ機能
   - 管理画面の改善

## セキュリティ考慮事項

1. **パラメータインジェクション対策**
   - タスクパラメータは JSON Schema でバリデーション
   - SQL インジェクション対策済み（SQLAlchemy 使用）

2. **権限管理**
   - スケジュール作成・編集・削除には適切な権限チェック
   - タスク定義の編集は管理者のみ

## パフォーマンス考慮事項

1. **インデックス設計**
   - name, task_name, enabled, category にインデックス
   - tags は JSONB の GIN インデックス

2. **キャッシュ戦略**
   - タスク定義は Redis にキャッシュ
   - スケジュール一覧は適切にページネーション

## 移行計画

1. **データベースマイグレーション**
   - Alembic を使用した段階的マイグレーション
   - ダウンタイムなしでの移行

2. **コード移行**
   - 新機能は feature flag で制御
   - 段階的なロールアウト