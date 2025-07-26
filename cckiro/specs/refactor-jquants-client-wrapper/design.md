# JQuantsクライアントラッパーのリファクタリング設計

## 1. アーキテクチャ設計

### 1.1 現在のアーキテクチャ
```
[CompanySyncService] → [JQuantsClientManager] → [JQuantsListedInfoClient] → [IAPIClient実装]
[DailyQuotesSyncService] → [JQuantsClientManager] → [JQuantsDailyQuotesClient] → [IAPIClient実装]
```

### 1.2 リファクタリング後のアーキテクチャ
```
[CompanySyncService] → [JQuantsClientManager] → [IAPIClient実装]
[DailyQuotesSyncService] → [JQuantsClientManager] → [IAPIClient実装]
```

## 2. 詳細設計

### 2.1 JQuantsClientManagerの変更

#### 現在の実装
```python
class JQuantsClientManager:
    def __init__(self, data_source_service: DataSourceService):
        self._api_clients: Dict[int, IAPIClient] = {}
        self._listed_clients: Dict[int, JQuantsListedInfoClient] = {}
        self._daily_quotes_clients: Dict[int, JQuantsDailyQuotesClient] = {}
    
    async def get_client(self, data_source_id: int) -> JQuantsListedInfoClient:
        # ラッパークライアントを返す
    
    async def get_daily_quotes_client(self, data_source_id: int) -> JQuantsDailyQuotesClient:
        # ラッパークライアントを返す
```

#### リファクタリング後
```python
class JQuantsClientManager:
    def __init__(self, data_source_service: DataSourceService):
        self._api_clients: Dict[int, IAPIClient] = {}
    
    async def get_client(self, data_source_id: int) -> IAPIClient:
        # APIクライアントを直接返す
        if data_source_id not in self._api_clients:
            self._api_clients[data_source_id] = await JQuantsClientFactory.create(
                data_source_service=self.data_source_service,
                data_source_id=data_source_id
            )
        return self._api_clients[data_source_id]
```

### 2.2 日付変換ユーティリティの追加

日付変換ロジックを集約するためのユーティリティクラスを作成：

```python
# app/utils/date_converter.py
class DateConverter:
    @staticmethod
    def to_date(date_input: Optional[Union[str, datetime, date]]) -> Optional[date]:
        """様々な形式の日付入力をdateオブジェクトに変換"""
        if date_input is None:
            return None
        
        if isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, str):
            # YYYYMMDD形式とYYYY-MM-DD形式の両方に対応
            if len(date_input) == 8 and date_input.isdigit():
                return date(int(date_input[:4]), int(date_input[4:6]), int(date_input[6:8]))
            else:
                return date.fromisoformat(date_input)
        
        raise ValueError(f"Unsupported date format: {type(date_input)}")
```

### 2.3 サービスクラスの修正

#### CompanyDataFetcherの修正
```python
class CompanyDataFetcher(ICompanyDataFetcher):
    async def fetch_all_companies(self, target_date: Optional[date] = None) -> List[Dict[str, Any]]:
        # get_client()でIAPIClientを直接取得
        client = await self.jquants_client_manager.get_client(self.data_source_id)
        return await client.get_listed_companies(target_date=target_date)
```

#### DailyQuotesDataFetcherの修正
```python
class DailyQuotesDataFetcher(IDailyQuotesDataFetcher):
    async def fetch_quotes_by_date(self, target_date: date, specific_codes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        # get_client()でIAPIClientを直接取得
        client = await self.jquants_client_manager.get_client(self.data_source_id)
        return await client.get_daily_quotes(target_date=target_date, specific_codes=specific_codes)
```

### 2.4 削除されるクラス

以下のクラスとその関連コードを削除：
- `JQuantsListedInfoClient`
- `JQuantsDailyQuotesClient`

## 3. インターフェース設計

### 3.1 IAPIClientインターフェース（変更なし）
```python
class IAPIClient(ABC):
    @abstractmethod
    async def get_listed_companies(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_daily_quotes(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        specific_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        pass
```

## 4. エラーハンドリング

既存のエラーハンドリング機構を維持：
- `AuthenticationError`
- `NetworkError`
- `DataValidationError`
- `RateLimitError`

## 5. 移行戦略

### 5.1 段階的な移行
1. **Phase 1**: DateConverterユーティリティの作成とテスト
2. **Phase 2**: JQuantsClientManagerのリファクタリング
3. **Phase 3**: サービスクラスの修正
4. **Phase 4**: ラッパークラスの削除
5. **Phase 5**: テストの更新と検証

### 5.2 後方互換性の確保
- 既存のメソッドシグネチャを維持
- 戻り値の形式を変更しない

## 6. テスト戦略

### 6.1 単体テスト
- DateConverterのテスト
- JQuantsClientManagerのテスト
- 各サービスクラスのテスト

### 6.2 統合テスト
- CompanySyncServiceの統合テスト
- DailyQuotesSyncServiceの統合テスト

### 6.3 リグレッションテスト
- 既存のすべてのテストが成功することを確認

## 7. 期待される効果

1. **コード量の削減**
   - 約300行のコード削減（ラッパークラスの削除）
   
2. **複雑性の低減**
   - クラス数: 3クラス削減
   - 依存関係の簡素化
   
3. **保守性の向上**
   - 新しいAPIメソッド追加時の変更箇所が半減
   - テストの記述が簡単に