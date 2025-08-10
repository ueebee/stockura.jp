# Domain 層改善提案

## 要約
クリーンアーキテクチャの観点から現在の domain 層を分析した結果、以下の 5 つの主要な改善点を特定しました。

## 改善提案（優先度順）

### 1. 【高優先度】リポジトリインターフェースの統一
**問題点**: `ScheduleRepository`と`ScheduleRepositoryInterface`の 2 つが存在し、メソッドシグネチャも異なる

**改善案**:
- すべてのリポジトリインターフェースを`XxxRepositoryInterface`に統一
- `ScheduleRepository`を削除し、`ScheduleRepositoryInterface`に統合
- インフラストラクチャ層の実装がインターフェースに準拠していることを確認

**影響範囲**: 中（リポジトリインターフェースと実装クラス）

### 2. 【高優先度】エンティティの外部依存の除去
**問題点**: `ListedInfo.from_dict()`が J-Quants API のデータ構造に依存

**改善案**:
```python
# application/factories/listed_info_factory.py (新規作成)
class ListedInfoFactory:
    @staticmethod
    def from_jquants_response(data: dict) -> ListedInfo:
        # API レスポンスからエンティティへの変換ロジック
        pass
```

**影響範囲**: 中（エンティティとユースケース）

### 3. 【中優先度】リッチドメインモデルへの移行
**問題点**: エンティティがデータホルダーとしてのみ機能

**改善案**:
- `Schedule`エンティティに`can_execute()`, `should_retry()` などのビジネスロジックを追加
- `ListedInfo`エンティティに`is_tradable()`, `belongs_to_sector()` などのメソッドを追加
- 複雑なビジネスロジックは`ScheduleService`, `ListedInfoService`などのドメインサービスに実装

**影響範囲**: 大（エンティティ、ユースケース、テスト）

### 4. 【中優先度】シリアライゼーションの責務分離
**問題点**: `Schedule.to_dict()`がドメイン層に存在

**改善案**:
```python
# application/serializers/schedule_serializer.py (新規作成)
class ScheduleSerializer:
    @staticmethod
    def to_dict(schedule: Schedule) -> dict:
        # シリアライゼーションロジック
        pass
```

**影響範囲**: 小（エンティティとプレゼンテーション層）

### 5. 【低優先度】ドメインイベントの実装
**問題点**: イベント駆動の仕組みがない

**改善案**:
```python
# domain/events/base.py (新規作成)
@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime
    aggregate_id: UUID

# domain/events/schedule_events.py (新規作成)
@dataclass(frozen=True)
class ScheduleCreatedEvent(DomainEvent):
    schedule_name: str
    task_name: str
```

**影響範囲**: 大（新規実装のため既存コードへの影響は少ない）

## 実装ロードマップ

### フェーズ 1（1-2 週間）
1. リポジトリインターフェースの統一
2. エンティティの外部依存の除去

### フェーズ 2（2-3 週間）
3. シリアライゼーションの責務分離
4. 基本的なドメインサービスの実装

### フェーズ 3（3-4 週間）
5. リッチドメインモデルへの段階的移行
6. ドメインイベントの基盤実装

## リスクと対策
- **後方互換性**: 各フェーズで既存の API インターフェースを維持
- **テスト**: 各変更に対して十分なテストカバレッジを確保
- **段階的移行**: ビッグバンリリースを避け、機能ごとに移行

## 期待される効果
- テスタビリティの向上（外部依存の除去により）
- ビジネスロジックの見通しの改善
- 将来的な変更への対応力向上
- チーム内でのドメイン知識の共有促進