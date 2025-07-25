# CompanySyncService リファクタリング設計書

## 1. アーキテクチャ設計

### 1.1 クラス構成

```
┌─────────────────────────────────────────────────────────────┐
│                      CompanySyncService                       │
│                        (調整役)                               │
└─────────────────────────────────────────────────────────────┘
                               │
                  ┌────────────┼────────────┐
                  ▼            ▼            ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │CompanyData   │ │CompanyData   │ │Company       │
        │Fetcher       │ │Mapper        │ │Repository    │
        └──────────────┘ └──────────────┘ └──────────────┘
```

### 1.2 各クラスの責務

#### CompanySyncService
- **責務**: 同期処理の全体的な制御とオーケストレーション
- **依存**: CompanyDataFetcher, CompanyDataMapper, CompanyRepository
- **主要メソッド**:
  - `sync()`: 同期処理のエントリーポイント
  - `sync_companies()`: 企業データ同期の制御

#### CompanyDataFetcher
- **責務**: J-Quants APIからのデータ取得のみ
- **依存**: JQuantsClientManager
- **主要メソッド**:
  - `fetch_all_companies()`: 全企業データ取得
  - `fetch_company_by_code()`: 特定企業データ取得

#### CompanyDataMapper
- **責務**: APIレスポンスとDBモデル間のデータ変換
- **依存**: なし（純粋関数）
- **主要メソッド**:
  - `map_to_model()`: APIデータ→DBモデル
  - `validate_data()`: データ検証

#### CompanyRepository
- **責務**: データベース操作の抽象化
- **依存**: AsyncSession, Company model
- **主要メソッド**:
  - `find_by_code()`: 企業検索
  - `save()`: 企業保存
  - `bulk_upsert()`: 一括更新

## 2. インターフェース設計

### 2.1 抽象基底クラス

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ICompanyDataFetcher(ABC):
    @abstractmethod
    async def fetch_all_companies(self) -> List[Dict[str, Any]]:
        pass

class ICompanyDataMapper(ABC):
    @abstractmethod
    def map_to_model(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class ICompanyRepository(ABC):
    @abstractmethod
    async def find_by_code(self, code: str) -> Optional[Company]:
        pass
    
    @abstractmethod
    async def bulk_upsert(self, companies: List[Dict[str, Any]]) -> Dict[str, int]:
        pass
```

## 3. データフロー設計

### 3.1 同期処理のフロー

```
1. CompanySyncService.sync_companies()
   ├─ 2. CompanyDataFetcher.fetch_all_companies()
   │     └─ J-Quants API呼び出し
   ├─ 3. CompanyDataMapper.map_to_model() [各データに対して]
   │     └─ データ検証・変換
   └─ 4. CompanyRepository.bulk_upsert()
         └─ DB一括更新
```

### 3.2 エラーハンドリング

各レイヤーで適切な例外を定義：
- `DataFetchError`: データ取得エラー
- `DataValidationError`: データ検証エラー
- `RepositoryError`: DB操作エラー

## 4. 実装の詳細設計

### 4.1 CompanySyncService（リファクタリング後）

```python
class CompanySyncService(BaseSyncService[CompanySyncHistory]):
    def __init__(
        self,
        fetcher: ICompanyDataFetcher,
        mapper: ICompanyDataMapper,
        repository: ICompanyRepository,
        db: AsyncSession
    ):
        super().__init__(db)
        self.fetcher = fetcher
        self.mapper = mapper
        self.repository = repository
    
    async def sync_companies(self, data_source_id: int, ...) -> CompanySyncHistory:
        # 30行以内の簡潔な制御フロー
        sync_history = await self.create_sync_history(...)
        
        try:
            # データ取得
            companies_data = await self.fetcher.fetch_all_companies()
            
            # データ変換
            mapped_data = [self.mapper.map_to_model(d) for d in companies_data]
            
            # DB保存
            stats = await self.repository.bulk_upsert(mapped_data)
            
            # 履歴更新
            return await self.update_sync_history_success(sync_history, **stats)
        except Exception as e:
            await self.update_sync_history_failure(sync_history, e)
            raise
```

### 4.2 パフォーマンス最適化

- **バッチ処理**: `bulk_upsert`で一括処理
- **トランザクション**: 適切なトランザクション境界
- **メモリ効率**: ストリーミング処理の検討（大量データ時）

## 5. テスト戦略

### 5.1 単体テスト

各クラスを独立してテスト可能に：
- `CompanyDataFetcher`: APIクライアントをモック
- `CompanyDataMapper`: 純粋関数なので簡単にテスト
- `CompanyRepository`: DBセッションをモック

### 5.2 統合テスト

実際のDBを使用した統合テスト：
- トランザクションロールバック
- テストデータの準備・クリーンアップ

## 6. 移行計画

### 6.1 段階的移行

1. **Phase 1**: 新クラスの作成（既存コードはそのまま）
2. **Phase 2**: CompanySyncServiceから新クラスを呼び出し
3. **Phase 3**: 古いコードの削除

### 6.2 互換性の維持

- 既存のAPIインターフェースは変更なし
- 内部実装のみの変更