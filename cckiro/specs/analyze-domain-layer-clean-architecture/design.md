# Domain 層クリーンアーキテクチャ改善設計書

## 1. 設計概要

本設計書は、要件ファイルで特定された 5 つの改善点に対する具体的な設計方針と実装方法を記述します。

## 2. アーキテクチャ設計

### 2.1 レイヤー構成

```
app/
├── domain/                  # ドメイン層（純粋なビジネスロジック）
│   ├── entities/           # エンティティ
│   ├── value_objects/      # 値オブジェクト
│   ├── repositories/       # リポジトリインターフェース（統一）
│   ├── services/           # ドメインサービス（新規）
│   ├── events/             # ドメインイベント（新規）
│   └── exceptions/         # ドメイン例外
├── application/            # アプリケーション層
│   ├── use_cases/         # ユースケース
│   ├── dtos/              # データ転送オブジェクト
│   ├── factories/         # エンティティファクトリ（新規）
│   ├── serializers/       # シリアライザー（新規）
│   └── interfaces/        # 外部システムインターフェース
└── infrastructure/         # インフラストラクチャ層
    └── repositories/       # リポジトリ実装
```

## 3. 詳細設計

### 3.1 リポジトリインターフェースの統一

#### 3.1.1 命名規則
- すべてのリポジトリインターフェースは `XxxRepositoryInterface` とする
- ドメイン層の `repositories/` ディレクトリに配置

#### 3.1.2 ScheduleRepository の統合

```python
# domain/repositories/schedule_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.domain.entities.schedule import Schedule

class ScheduleRepositoryInterface(ABC):
    """統一されたスケジュールリポジトリインターフェース"""
    
    @abstractmethod
    async def create(self, schedule: Schedule) -> Schedule:
        """スケジュールを作成"""
        pass
    
    @abstractmethod
    async def save(self, schedule: Schedule) -> Schedule:
        """スケジュールを保存（create/update の判定を含む）"""
        pass
    
    @abstractmethod
    async def get_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        """ID でスケジュールを取得"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Schedule]:
        """名前でスケジュールを取得"""
        pass
    
    @abstractmethod
    async def get_all(
        self, 
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Schedule]:
        """すべてのスケジュールを取得"""
        pass
    
    @abstractmethod
    async def get_filtered(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Schedule]:
        """フィルタリングしてスケジュールを取得"""
        pass
    
    @abstractmethod
    async def update(self, schedule: Schedule) -> Schedule:
        """スケジュールを更新"""
        pass
    
    @abstractmethod
    async def delete(self, schedule_id: UUID) -> bool:
        """スケジュールを削除"""
        pass
    
    @abstractmethod
    async def enable(self, schedule_id: UUID) -> bool:
        """スケジュールを有効化"""
        pass
    
    @abstractmethod
    async def disable(self, schedule_id: UUID) -> bool:
        """スケジュールを無効化"""
        pass
```

#### 3.1.3 その他のリポジトリインターフェース

```python
# domain/repositories/auth_repository_interface.py
# 既存の AuthRepository を AuthRepositoryInterface にリネーム

# domain/repositories/listed_info_repository_interface.py  
# 既存の ListedInfoRepository を ListedInfoRepositoryInterface にリネーム

# domain/repositories/task_log_repository_interface.py
# 既存のまま（すでに正しい命名）
```

### 3.2 エンティティの外部依存の除去

#### 3.2.1 ListedInfoFactory の実装

```python
# application/factories/listed_info_factory.py
from datetime import datetime, date
from app.domain.entities.listed_info import ListedInfo
from app.domain.value_objects.stock_code import StockCode

class ListedInfoFactory:
    """J-Quants API レスポンスから ListedInfo エンティティを生成"""
    
    @staticmethod
    def from_jquants_response(data: dict) -> ListedInfo:
        """J-Quants API のレスポンスから ListedInfo を生成
        
        Args:
            data: J-Quants API のレスポンスデータ
            
        Returns:
            ListedInfo エンティティ
        """
        # 日付の解析
        date_str = data["Date"]
        if len(date_str) == 8:  # YYYYMMDD 形式
            listing_date = datetime.strptime(date_str, "%Y%m%d").date()
        else:  # YYYY-MM-DD 形式
            listing_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        return ListedInfo(
            date=listing_date,
            code=StockCode(data["Code"]),
            company_name=data["CompanyName"],
            company_name_english=data.get("CompanyNameEnglish"),
            sector_17_code=data.get("Sector17Code"),
            sector_17_code_name=data.get("Sector17CodeName"),
            sector_33_code=data.get("Sector33Code"),
            sector_33_code_name=data.get("Sector33CodeName"),
            scale_category=data.get("ScaleCategory"),
            market_code=data.get("MarketCode"),
            market_code_name=data.get("MarketCodeName"),
            margin_code=data.get("MarginCode"),
            margin_code_name=data.get("MarginCodeName"),
        )
    
    @staticmethod
    def create_multiple(data_list: List[dict]) -> List[ListedInfo]:
        """複数の J-Quants API レスポンスから ListedInfo リストを生成"""
        return [
            ListedInfoFactory.from_jquants_response(data) 
            for data in data_list
        ]
```

#### 3.2.2 ListedInfo エンティティの修正

```python
# domain/entities/listed_info.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional
from app.domain.value_objects.stock_code import StockCode

@dataclass(frozen=True)
class ListedInfo:
    """上場銘柄情報エンティティ（外部依存を除去）"""
    
    date: date
    code: StockCode
    company_name: str
    company_name_english: Optional[str]
    sector_17_code: Optional[str]
    sector_17_code_name: Optional[str]
    sector_33_code: Optional[str]
    sector_33_code_name: Optional[str]
    scale_category: Optional[str]
    market_code: Optional[str]
    market_code_name: Optional[str]
    margin_code: Optional[str]
    margin_code_name: Optional[str]

    def __post_init__(self) -> None:
        """Post initialization validation."""
        if not self.company_name:
            raise ValueError("会社名は必須です")
        if not isinstance(self.date, date):
            raise ValueError("日付は date 型である必要があります")
    
    # from_dict メソッドを削除
    
    def is_same_listing(self, other: ListedInfo) -> bool:
        """同じ上場情報かどうかを判定"""
        return self.date == other.date and self.code == other.code
    
    # ビジネスロジックを追加（リッチドメインモデル化）
    def is_prime_market(self) -> bool:
        """プライム市場銘柄かどうか"""
        return self.market_code == "0111"
    
    def is_standard_market(self) -> bool:
        """スタンダード市場銘柄かどうか"""
        return self.market_code == "0112"
    
    def is_growth_market(self) -> bool:
        """グロース市場銘柄かどうか"""
        return self.market_code == "0113"
    
    def belongs_to_sector_17(self, sector_code: str) -> bool:
        """指定された 17 業種に属するか"""
        return self.sector_17_code == sector_code
    
    def belongs_to_sector_33(self, sector_code: str) -> bool:
        """指定された 33 業種に属するか"""
        return self.sector_33_code == sector_code
```

### 3.3 シリアライゼーションの責務分離

#### 3.3.1 ScheduleSerializer の実装

```python
# application/serializers/schedule_serializer.py
from typing import Dict, Any
from app.domain.entities.schedule import Schedule

class ScheduleSerializer:
    """Schedule エンティティのシリアライザー"""
    
    @staticmethod
    def to_dict(schedule: Schedule) -> Dict[str, Any]:
        """Schedule エンティティを Dict に変換"""
        return {
            "id": str(schedule.id),
            "name": schedule.name,
            "task_name": schedule.task_name,
            "cron_expression": schedule.cron_expression,
            "enabled": schedule.enabled,
            "args": schedule.args,
            "kwargs": schedule.kwargs,
            "description": schedule.description,
            "category": schedule.category,
            "tags": schedule.tags,
            "execution_policy": schedule.execution_policy,
            "auto_generated_name": schedule.auto_generated_name,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Schedule:
        """Dict から Schedule エンティティを生成"""
        from datetime import datetime
        from uuid import UUID
        
        return Schedule(
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            name=data["name"],
            task_name=data["task_name"],
            cron_expression=data["cron_expression"],
            enabled=data.get("enabled", True),
            args=data.get("args", []),
            kwargs=data.get("kwargs", {}),
            description=data.get("description"),
            category=data.get("category"),
            tags=data.get("tags", []),
            execution_policy=data.get("execution_policy", "allow"),
            auto_generated_name=data.get("auto_generated_name", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
```

#### 3.3.2 Schedule エンティティの修正

```python
# domain/entities/schedule.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

@dataclass
class Schedule:
    """Schedule entity for Celery Beat tasks（to_dict メソッドを削除）"""
    
    id: UUID
    name: str
    task_name: str
    cron_expression: str
    enabled: bool = True
    args: List[Any] = None
    kwargs: Dict[str, Any] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = None
    execution_policy: str = "allow"
    auto_generated_name: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Post initialization."""
        if self.args is None:
            self.args = []
        if self.kwargs is None:
            self.kwargs = {}
        if self.tags is None:
            self.tags = []
    
    # to_dict メソッドを削除
    
    # ビジネスロジックを追加
    def can_execute(self) -> bool:
        """実行可能かどうかを判定"""
        return self.enabled and self.execution_policy == "allow"
    
    def has_category(self, category: str) -> bool:
        """指定されたカテゴリに属するか"""
        return self.category == category
    
    def has_tag(self, tag: str) -> bool:
        """指定されたタグを持つか"""
        return tag in self.tags
    
    def is_auto_generated(self) -> bool:
        """自動生成されたスケジュールかどうか"""
        return self.auto_generated_name
```

### 3.4 ドメインサービスの実装

#### 3.4.1 ScheduleService

```python
# domain/services/schedule_service.py
from typing import List
from app.domain.entities.schedule import Schedule
from app.domain.validators.cron_validator import CronValidator

class ScheduleService:
    """スケジュールに関する複雑なビジネスロジックを扱うドメインサービス"""
    
    def __init__(self, cron_validator: CronValidator):
        self._cron_validator = cron_validator
    
    def validate_cron_expression(self, cron_expression: str) -> bool:
        """Cron 式の妥当性を検証"""
        return self._cron_validator.validate(cron_expression)
    
    def find_conflicting_schedules(
        self, 
        new_schedule: Schedule, 
        existing_schedules: List[Schedule]
    ) -> List[Schedule]:
        """同じタスクで同じ時間に実行される競合するスケジュールを検索"""
        conflicts = []
        for schedule in existing_schedules:
            if (schedule.task_name == new_schedule.task_name and
                schedule.cron_expression == new_schedule.cron_expression and
                schedule.enabled and
                schedule.id != new_schedule.id):
                conflicts.append(schedule)
        return conflicts
    
    def generate_unique_name(
        self, 
        base_name: str, 
        existing_schedules: List[Schedule]
    ) -> str:
        """既存のスケジュールと重複しないユニークな名前を生成"""
        existing_names = {s.name for s in existing_schedules}
        if base_name not in existing_names:
            return base_name
        
        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1
        return f"{base_name}_{counter}"
```

#### 3.4.2 ListedInfoService

```python
# domain/services/listed_info_service.py
from typing import List, Dict
from app.domain.entities.listed_info import ListedInfo

class ListedInfoService:
    """上場銘柄情報に関する複雑なビジネスロジックを扱うドメインサービス"""
    
    def group_by_sector_17(
        self, 
        listed_infos: List[ListedInfo]
    ) -> Dict[str, List[ListedInfo]]:
        """17 業種別にグループ化"""
        groups = {}
        for info in listed_infos:
            sector = info.sector_17_code or "unknown"
            if sector not in groups:
                groups[sector] = []
            groups[sector].append(info)
        return groups
    
    def group_by_market(
        self, 
        listed_infos: List[ListedInfo]
    ) -> Dict[str, List[ListedInfo]]:
        """市場別にグループ化"""
        groups = {}
        for info in listed_infos:
            market = info.market_code or "unknown"
            if market not in groups:
                groups[market] = []
            groups[market].append(info)
        return groups
    
    def filter_by_scale_category(
        self, 
        listed_infos: List[ListedInfo], 
        scale_category: str
    ) -> List[ListedInfo]:
        """規模区分でフィルタリング"""
        return [
            info for info in listed_infos 
            if info.scale_category == scale_category
        ]
    
    def find_changed_listings(
        self, 
        current: List[ListedInfo], 
        previous: List[ListedInfo]
    ) -> Dict[str, List[ListedInfo]]:
        """前回と今回の差分を検出"""
        current_dict = {info.code.value: info for info in current}
        previous_dict = {info.code.value: info for info in previous}
        
        new_listings = []
        delisted = []
        changed = []
        
        # 新規上場
        for code, info in current_dict.items():
            if code not in previous_dict:
                new_listings.append(info)
        
        # 上場廃止
        for code, info in previous_dict.items():
            if code not in current_dict:
                delisted.append(info)
        
        # 変更（市場変更など）
        for code, current_info in current_dict.items():
            if code in previous_dict:
                previous_info = previous_dict[code]
                if (current_info.market_code != previous_info.market_code or
                    current_info.sector_17_code != previous_info.sector_17_code or
                    current_info.sector_33_code != previous_info.sector_33_code):
                    changed.append(current_info)
        
        return {
            "new": new_listings,
            "delisted": delisted,
            "changed": changed
        }
```

### 3.5 ドメインイベントの基盤実装

#### 3.5.1 基底クラス

```python
# domain/events/base.py
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class DomainEvent(ABC):
    """ドメインイベントの基底クラス"""
    occurred_at: datetime
    aggregate_id: UUID
    aggregate_type: str
    event_version: int = 1
    
    def event_name(self) -> str:
        """イベント名を返す"""
        return self.__class__.__name__
```

#### 3.5.2 スケジュール関連イベント

```python
# domain/events/schedule_events.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from app.domain.events.base import DomainEvent

@dataclass(frozen=True)
class ScheduleCreatedEvent(DomainEvent):
    """スケジュール作成イベント"""
    schedule_name: str
    task_name: str
    cron_expression: str
    category: Optional[str] = None

@dataclass(frozen=True)
class ScheduleUpdatedEvent(DomainEvent):
    """スケジュール更新イベント"""
    schedule_name: str
    changes: Dict[str, Any]

@dataclass(frozen=True)
class ScheduleEnabledEvent(DomainEvent):
    """スケジュール有効化イベント"""
    schedule_name: str

@dataclass(frozen=True)
class ScheduleDisabledEvent(DomainEvent):
    """スケジュール無効化イベント"""
    schedule_name: str

@dataclass(frozen=True)
class ScheduleDeletedEvent(DomainEvent):
    """スケジュール削除イベント"""
    schedule_name: str
```

#### 3.5.3 上場銘柄情報関連イベント

```python
# domain/events/listed_info_events.py
from dataclasses import dataclass
from datetime import date
from typing import List
from app.domain.events.base import DomainEvent

@dataclass(frozen=True)
class ListedInfosFetchedEvent(DomainEvent):
    """上場銘柄情報取得イベント"""
    target_date: date
    fetched_count: int
    source: str  # "jquants" など

@dataclass(frozen=True)
class ListedInfosStoredEvent(DomainEvent):
    """上場銘柄情報保存イベント"""
    target_date: date
    stored_count: int

@dataclass(frozen=True)
class NewListingsDetectedEvent(DomainEvent):
    """新規上場検出イベント"""
    target_date: date
    new_listings: List[str]  # 銘柄コードのリスト

@dataclass(frozen=True)
class DelistingsDetectedEvent(DomainEvent):
    """上場廃止検出イベント"""
    target_date: date
    delistings: List[str]  # 銘柄コードのリスト

@dataclass(frozen=True)
class MarketChangeDetectedEvent(DomainEvent):
    """市場変更検出イベント"""
    target_date: date
    code: str
    from_market: str
    to_market: str
```

## 4. 移行戦略

### 4.1 段階的移行アプローチ

1. **フェーズ 1**: インターフェースの整理（既存コードへの影響最小）
   - リポジトリインターフェースの統一
   - 新しいファクトリーとシリアライザーの追加

2. **フェーズ 2**: エンティティの改善（中程度の影響）
   - エンティティから外部依存メソッドを削除
   - ビジネスロジックの追加
   - ドメインサービスの実装

3. **フェーズ 3**: イベント駆動への移行（新機能として追加）
   - ドメインイベントの基盤実装
   - 既存機能への段階的適用

### 4.2 互換性の維持

- 削除されるメソッド（`from_dict`, `to_dict`）は、ファクトリーとシリアライザーで同等の機能を提供
- 既存の API エンドポイントは変更せず、内部実装のみを更新
- テストケースを充実させ、リグレッションを防止

## 5. テスト戦略

### 5.1 ユニットテスト
- 各エンティティのビジネスロジック
- ドメインサービスの複雑なロジック
- ファクトリーとシリアライザーの変換処理

### 5.2 統合テスト
- リポジトリインターフェースと実装の整合性
- ユースケースの動作確認
- イベント発行と処理の流れ

### 5.3 リグレッションテスト
- 既存機能が影響を受けていないことの確認
- パフォーマンステスト

## 6. 実装の優先順位

1. **必須**: リポジトリインターフェースの統一
2. **必須**: エンティティの外部依存除去
3. **推奨**: シリアライゼーションの責務分離
4. **推奨**: 基本的なドメインサービスの実装
5. **オプション**: ドメインイベントの実装

この優先順位に従って、段階的に実装を進めることで、リスクを最小化しながら確実に改善を進められます。