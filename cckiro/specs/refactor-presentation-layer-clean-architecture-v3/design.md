# Presentation 層クリーンアーキテクチャ改善設計（第 3 回）

## 1. 設計概要

Presentation 層の責務を明確化し、データ変換ロジックを専用のコンポーネントに分離する設計を行います。

## 2. アーキテクチャ構成

### 2.1 レイヤー構造

```
app/
├── presentation/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/     # API エンドポイント
│   │       ├── schemas/       # Pydantic スキーマ
│   │       └── mappers/       # 新規: スキーマ ⇔ DTO 変換
│   ├── dependencies/          # 依存性注入
│   └── middleware/            # ミドルウェア
├── application/               # アプリケーション層（変更なし）
│   ├── dtos/
│   └── use_cases/
└── domain/                    # ドメイン層（変更なし）
```

### 2.2 新規コンポーネント: Mapper

データ変換の責務を持つ Mapper クラスを導入します。

#### 基本設計

```python
# app/presentation/api/v1/mappers/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

TSchema = TypeVar('TSchema')
TDto = TypeVar('TDto')

class BaseMapper(ABC, Generic[TSchema, TDto]):
    """Base mapper for converting between API schemas and DTOs."""
    
    @abstractmethod
    def schema_to_dto(self, schema: TSchema) -> TDto:
        """Convert API schema to DTO."""
        pass
    
    @abstractmethod
    def dto_to_schema(self, dto: TDto) -> TSchema:
        """Convert DTO to API schema."""
        pass
```

#### 自動マッピング機能

```python
# app/presentation/api/v1/mappers/auto_mapper.py
class AutoMapper:
    """Automatic field mapping utility."""
    
    @staticmethod
    def map_fields(source: Any, target_class: Type[T]) -> Dict[str, Any]:
        """Map fields from source to target class automatically."""
        # 同じ名前のフィールドを自動的にマッピング
        # 型チェックも実施
```

### 2.3 具体的な Mapper の実装例

```python
# app/presentation/api/v1/mappers/schedule_mapper.py
class ScheduleMapper(BaseMapper[ScheduleCreate, ScheduleCreateDto]):
    """Mapper for schedule-related conversions."""
    
    def schema_to_dto(self, schema: ScheduleCreate) -> ScheduleCreateDto:
        # 自動マッピングを利用
        fields = AutoMapper.map_fields(schema, ScheduleCreateDto)
        
        # カスタムマッピング（必要な場合のみ）
        if schema.task_params:
            fields['task_params'] = self._map_task_params(schema.task_params)
        
        return ScheduleCreateDto(**fields)
```

### 2.4 エンドポイントの簡潔化

```python
# app/presentation/api/v1/endpoints/schedules.py
@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    use_case: ManageScheduleUseCase = Depends(get_manage_schedule_use_case),
    mapper: ScheduleMapper = Depends(get_schedule_mapper),
) -> ScheduleResponse:
    """Create a new schedule."""
    # マッピングは Mapper に委譲
    dto = mapper.schema_to_dto(schedule_data)
    result = await use_case.create_schedule(dto)
    return mapper.dto_to_schema(result)
```

## 3. 実装方針

### 3.1 段階的な実装

1. **Phase 1**: 基本的な Mapper 基盤の実装
   - BaseMapper の実装
   - AutoMapper の実装
   - 単体テストの作成

2. **Phase 2**: Schedule 関連の Mapper 実装
   - ScheduleMapper の実装
   - 既存エンドポイントの移行
   - 統合テストの実施

3. **Phase 3**: その他のエンドポイントの移行
   - Auth 関連の Mapper
   - ListedInfo 関連の Mapper

### 3.2 テスト戦略

- 各 Mapper の単体テスト
- 自動マッピング機能のテスト
- エンドポイントの統合テスト（既存のテストが通ることを確認）

## 4. 期待される効果

1. **保守性の向上**
   - フィールド追加時の変更箇所が最小限に
   - データ変換ロジックの一元管理

2. **テスタビリティの向上**
   - Mapper の単体テストが容易に
   - エンドポイントのテストがシンプルに

3. **責務の明確化**
   - Presentation 層: HTTP リクエスト/レスポンス処理
   - Mapper: データ変換
   - Application 層: ビジネスロジック

## 5. 注意点

- 既存の API インターフェースは変更しない
- Application 層の DTO は変更しない
- 過度な抽象化を避け、実用的な実装を心がける