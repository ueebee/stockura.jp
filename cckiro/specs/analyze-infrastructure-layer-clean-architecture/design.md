# Infrastructure 層クリーンアーキテクチャ改善設計

## 1. 設計概要

本設計書は、 Stockura プロジェクトの infrastructure 層をクリーンアーキテクチャの原則に従って改善するための詳細設計を定義します。

## 2. 設計方針

### 2.1 基本原則
- **依存性逆転の原則（DIP）**: infrastructure 層は常に domain 層に依存し、逆は許可しない
- **単一責任の原則（SRP）**: 各クラスは単一の責任のみを持つ
- **インターフェース分離の原則（ISP）**: 必要最小限のインターフェースを定義

### 2.2 設計目標
1. 層間の依存関係を明確化
2. 責務の重複を排除
3. 型安全性の向上
4. 拡張性の確保

## 3. アーキテクチャ設計

### 3.1 ディレクトリ構造の再編成

```
app/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   │   ├── stock_code.py
│   │   ├── market_code.py
│   │   ├── sector_code.py      # 新規
│   │   └── listing_date.py     # 新規
│   ├── repositories/            # インターフェース定義
│   ├── services/
│   └── factories/               # ドメインファクトリー（移動）
│       └── listed_info_factory.py
│
├── application/
│   ├── use_cases/
│   ├── dtos/
│   └── interfaces/
│       └── external/            # 外部サービスインターフェース
│
└── infrastructure/
    ├── database/
    │   ├── models/              # ORM モデル
    │   ├── mappers/             # エンティティ⇔モデル変換（新規）
    │   │   ├── __init__.py
    │   │   ├── base_mapper.py
    │   │   └── listed_info_mapper.py
    │   └── connection.py
    │
    ├── repositories/
    │   ├── database/
    │   ├── external/
    │   └── redis/
    │
    ├── external_services/       # 外部 API クライアント統合（名称変更）
    │   ├── jquants/
    │   │   ├── client.py
    │   │   ├── types/          # 型定義（新規）
    │   │   │   └── responses.py
    │   │   └── mappers/        # API レスポンス⇔DTO 変換（新規）
    │   │       └── listed_info_mapper.py
    │   └── yahoo/               # 将来の拡張用
    │
    ├── cache/                   # キャッシュ抽象化（実装）
    │   ├── interfaces.py
    │   └── redis_cache.py
    │
    ├── events/
    ├── celery/
    └── config/                  # インフラ設定（新規）
        └── settings.py
```

### 3.2 主要コンポーネントの設計

#### 3.2.1 Mapper パターンの導入

```python
# app/infrastructure/database/mappers/base_mapper.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TEntity = TypeVar('TEntity')
TModel = TypeVar('TModel')

class BaseMapper(ABC, Generic[TEntity, TModel]):
    """基底マッパークラス"""
    
    @abstractmethod
    def to_entity(self, model: TModel) -> TEntity:
        """モデルからエンティティへの変換"""
        pass
    
    @abstractmethod
    def to_model(self, entity: TEntity) -> TModel:
        """エンティティからモデルへの変換"""
        pass
```

#### 3.2.2 型安全な API レスポンス定義

```python
# app/infrastructure/external_services/jquants/types/responses.py
from typing import TypedDict, Optional

class JQuantsListedInfoResponse(TypedDict):
    """J-Quants 上場銘柄情報レスポンス"""
    Date: str
    Code: str
    CompanyName: str
    CompanyNameEnglish: Optional[str]
    Sector17Code: str
    Sector17CodeName: str
    Sector33Code: str
    Sector33CodeName: str
    ScaleCategory: str
    MarketCode: str
    MarketCodeName: str
    MarginCode: Optional[str]
    MarginCodeName: Optional[str]
```

#### 3.2.3 リポジトリ実装の改善

```python
# app/infrastructure/repositories/database/listed_info_repository_impl.py
class ListedInfoRepositoryImpl(ListedInfoRepositoryInterface):
    """上場銘柄情報リポジトリ実装"""
    
    def __init__(
        self, 
        session: AsyncSession,
        mapper: ListedInfoMapper
    ) -> None:
        self._session = session
        self._mapper = mapper
    
    async def save_all(self, entities: List[ListedInfo]) -> None:
        """複数の上場銘柄情報を保存"""
        models = [self._mapper.to_model(entity) for entity in entities]
        # バルクインサート処理
```

### 3.3 依存関係の整理

#### 3.3.1 レイヤー間の依存関係

```
Presentation → Application → Domain ← Infrastructure
                                ↑
                                │
                            （実装）
```

#### 3.3.2 依存性注入の改善

```python
# app/infrastructure/di/providers.py
from typing import Protocol

class DatabaseSession(Protocol):
    """データベースセッション抽象化"""
    async def execute(self, statement): ...
    async def commit(self): ...
    async def rollback(self): ...

class CacheService(Protocol):
    """キャッシュサービス抽象化"""
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: Optional[int] = None): ...
```

### 3.4 エラーハンドリングの設計

#### 3.4.1 インフラ層例外階層

```python
# app/infrastructure/exceptions.py
class InfrastructureError(Exception):
    """インフラ層基底例外"""
    pass

class DatabaseError(InfrastructureError):
    """データベース関連エラー"""
    pass

class ExternalAPIError(InfrastructureError):
    """外部 API 関連エラー"""
    pass

class CacheError(InfrastructureError):
    """キャッシュ関連エラー"""
    pass
```

#### 3.4.2 例外の変換

```python
# インフラ層でキャッチした例外をドメイン層の例外に変換
try:
    response = await self._http_client.get(url)
except aiohttp.ClientError as e:
    raise ExternalAPIError(f"API request failed: {e}") from e
```

## 4. 実装優先順位

### Phase 1: 基盤整備（高優先度）
1. Mapper クラスの実装
2. 型定義の追加
3. ディレクトリ構造の再編成

### Phase 2: リポジトリ改善（高優先度）
1. リポジトリ実装への Mapper 適用
2. 外部 API クライアントの型安全化

### Phase 3: 設定管理（中優先度）
1. インフラ設定の分離
2. 環境変数管理の改善

### Phase 4: キャッシュ実装（低優先度）
1. キャッシュインターフェースの定義
2. Redis キャッシュ実装

## 5. 移行戦略

### 5.1 段階的移行
1. 新規コンポーネントから新設計を適用
2. 既存コンポーネントは段階的にリファクタリング
3. テストカバレッジを維持しながら移行

### 5.2 互換性の維持
- 既存のインターフェースは維持
- 内部実装のみを段階的に改善
- 破壊的変更は避ける

## 6. テスト戦略

### 6.1 単体テスト
- Mapper クラスの変換テスト
- リポジトリのモックテスト
- 例外変換のテスト

### 6.2 統合テスト
- データベース接続テスト
- 外部 API 通信テスト
- キャッシュ動作テスト

## 7. 期待される効果

1. **保守性の向上**: 責務が明確に分離され、変更の影響範囲が限定的
2. **拡張性の向上**: 新しい外部サービスやデータソースの追加が容易
3. **型安全性**: コンパイル時の型チェックによるバグの早期発見
4. **テスタビリティ**: インターフェースベースの設計によりモックが容易