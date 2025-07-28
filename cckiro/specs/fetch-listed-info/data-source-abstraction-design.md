# データソース抽象化設計書

## 1. 調査結果サマリー

### 1.1 現在のプロジェクト構造
- **アーキテクチャ**: クリーンアーキテクチャを採用
- **既存実装**: 
  - J-Quants API 用のクライアントとリポジトリ実装が存在
  - yfinance 用のインターフェース定義も存在
  - 各データソースが個別に実装されている状態

### 1.2 データソース間の比較

#### J-Quants API
- **銘柄コード形式**: 4 桁の数字（例: "7203"）
- **認証**: OAuth2 ベース（リフレッシュトークン → ID トークン）
- **データ取得単位**: 日次、バッチ取得可能
- **主要データ**:
  - 銘柄情報（企業名、業種、市場区分）
  - 株価四本値（調整済み価格含む）
  - 財務データ
- **更新頻度**: 日次（営業日終了後）
- **地域**: 日本株式市場のみ

#### yfinance
- **銘柄コード形式**: ティッカーシンボル（例: "7203.T", "AAPL"）
- **認証**: 不要（公開 API）
- **データ取得単位**: リアルタイム、履歴データ
- **主要データ**:
  - 株価データ（OHLCV）
  - 配当、株式分割情報
  - オプション情報
- **更新頻度**: リアルタイム（遅延あり）
- **地域**: グローバル市場

### 1.3 共通性と差異

#### 共通データ項目
- 銘柄基本情報（コード、企業名）
- 株価四本値（OHLC）
- 出来高（Volume）
- 日付/タイムスタンプ

#### 差異
- **銘柄コード形式**: J-Quants は 4 桁数字、 yfinance はティッカーシンボル
- **価格調整**: J-Quants は調整係数を提供、 yfinance は調整済み価格を提供
- **データの粒度**: J-Quants は日本市場に特化した詳細情報、 yfinance はグローバルだが基本情報中心
- **認証方式**: J-Quants は OAuth2 、 yfinance は認証不要

## 2. 抽象化パターンの検討

### 2.1 Repository パターン（推奨）
**メリット**:
- ドメイン層でデータアクセスを抽象化
- テストが容易（モックの作成が簡単）
- クリーンアーキテクチャとの相性が良い

**デメリット**:
- 複雑なクエリの表現が難しい場合がある

### 2.2 Adapter パターン
**メリット**:
- 既存のインターフェースに新しい実装を適合させやすい
- 外部ライブラリの変更に強い

**デメリット**:
- 追加の変換層が必要

### 2.3 Strategy パターン
**メリット**:
- 実行時にデータソースを切り替え可能
- アルゴリズムの切り替えが容易

**デメリット**:
- 設定が複雑になる可能性

## 3. 推奨設計: Repository + Adapter パターンの組み合わせ

### 3.1 設計方針
1. **Repository パターン**をベースに、ドメイン層でデータアクセスを抽象化
2. **Adapter パターン**で各データソースの差異を吸収
3. **Factory パターン**でデータソースの選択を管理

### 3.2 レイヤー構成

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                              │
│          - StockDataRepository (Interface)                   │
│          - MarketDataRepository (Interface)                 │
│          - Entities (Stock, Price, etc.)                    │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer                           │
│          - Use Cases                                         │
│          - Data Source Factory                               │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                          │
│  ┌─────────────────┐        ┌─────────────────┐           │
│  │ J-Quants Adapter│        │ yfinance Adapter│           │
│  └─────────────────┘        └─────────────────┘           │
│  ┌─────────────────┐        ┌─────────────────┐           │
│  │J-Quants Client  │        │ yfinance Client │           │
│  └─────────────────┘        └─────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 4. 具体的な実装設計

### 4.1 ドメイン層インターフェース

```python
# app/domain/repositories/stock_data_repository.py
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional
from app.domain.entities.stock import Stock
from app.domain.entities.price import Price
from app.domain.value_objects.stock_identifier import StockIdentifier

class StockDataRepository(ABC):
    """株式データリポジトリの抽象インターフェース"""
    
    @abstractmethod
    async def get_stock_info(
        self, 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        """銘柄情報を取得"""
        pass
    
    @abstractmethod
    async def get_stock_prices(
        self,
        identifier: StockIdentifier,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[Price]:
        """株価履歴を取得"""
        pass
    
    @abstractmethod
    async def get_latest_price(
        self,
        identifier: StockIdentifier
    ) -> Optional[Price]:
        """最新株価を取得"""
        pass
    
    @abstractmethod
    async def search_stocks(
        self,
        query: str,
        market: Optional[str] = None
    ) -> List[Stock]:
        """銘柄を検索"""
        pass
```

### 4.2 値オブジェクト: 銘柄識別子

```python
# app/domain/value_objects/stock_identifier.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class StockIdentifier:
    """データソースに依存しない銘柄識別子"""
    
    code: str  # 基本コード（例: "7203"）
    market: Optional[str] = None  # 市場コード（例: "TSE", "NYSE"）
    country: Optional[str] = None  # 国コード（例: "JP", "US"）
    
    def to_jquants_code(self) -> str:
        """J-Quants 形式に変換"""
        # 4 桁の数字コードをそのまま返す
        return self.code
    
    def to_yfinance_symbol(self) -> str:
        """yfinance 形式に変換"""
        if self.country == "JP":
            return f"{self.code}.T"
        return self.code
    
    @classmethod
    def from_jquants_code(cls, code: str) -> "StockIdentifier":
        """J-Quants コードから作成"""
        return cls(code=code, market="TSE", country="JP")
    
    @classmethod
    def from_yfinance_symbol(cls, symbol: str) -> "StockIdentifier":
        """yfinance シンボルから作成"""
        if symbol.endswith(".T"):
            return cls(
                code=symbol[:-2],
                market="TSE",
                country="JP"
            )
        # その他の市場の処理...
        return cls(code=symbol)
```

### 4.3 インフラストラクチャ層: アダプター実装

```python
# app/infrastructure/adapters/jquants_adapter.py
from datetime import date
from typing import List, Optional
from app.domain.entities.stock import Stock
from app.domain.entities.price import Price
from app.domain.repositories.stock_data_repository import StockDataRepository
from app.domain.value_objects.stock_identifier import StockIdentifier
from app.infrastructure.jquants.client import JQuantsClient

class JQuantsAdapter(StockDataRepository):
    """J-Quants API 用アダプター"""
    
    def __init__(self, client: JQuantsClient):
        self._client = client
    
    async def get_stock_info(
        self, 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        code = identifier.to_jquants_code()
        
        # J-Quants API から銘柄情報を取得
        response = await self._client.get_listed_info(code=code)
        if not response or not response.get("info"):
            return None
        
        # レスポンスをドメインエンティティに変換
        info = response["info"][0]
        return self._convert_to_stock_entity(info)
    
    async def get_stock_prices(
        self,
        identifier: StockIdentifier,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[Price]:
        code = identifier.to_jquants_code()
        
        # J-Quants API から価格データを取得
        response = await self._client.get_daily_quotes(
            code=code,
            from_date=start_date.strftime("%Y%m%d"),
            to_date=end_date.strftime("%Y%m%d")
        )
        
        # レスポンスをドメインエンティティに変換
        prices = []
        for quote in response.get("daily_quotes", []):
            prices.append(self._convert_to_price_entity(quote, identifier))
        
        return prices
    
    def _convert_to_stock_entity(self, data: dict) -> Stock:
        """J-Quants のレスポンスを Stock エンティティに変換"""
        from app.domain.entities.stock import StockCode
        
        return Stock(
            code=StockCode(data["Code"]),
            company_name=data["CompanyName"],
            company_name_english=data.get("CompanyNameEnglish"),
            sector_17_code=self._parse_sector_code(data.get("Sector17Code")),
            sector_17_name=data.get("Sector17CodeName"),
            # ... その他のフィールド
        )
    
    def _convert_to_price_entity(
        self, 
        data: dict, 
        identifier: StockIdentifier
    ) -> Price:
        """J-Quants のレスポンスを Price エンティティに変換"""
        from datetime import datetime
        from app.domain.value_objects.ticker_symbol import TickerSymbol
        
        return Price(
            ticker_symbol=TickerSymbol(identifier.code),
            date=datetime.strptime(data["Date"], "%Y%m%d").date(),
            open=float(data["AdjustmentOpen"]),
            high=float(data["AdjustmentHigh"]),
            low=float(data["AdjustmentLow"]),
            close=float(data["AdjustmentClose"]),
            volume=int(data["AdjustmentVolume"]),
            adjusted_close=float(data["AdjustmentClose"])
        )
```

```python
# app/infrastructure/adapters/yfinance_adapter.py
from datetime import date
from typing import List, Optional
import yfinance as yf
from app.domain.entities.stock import Stock
from app.domain.entities.price import Price
from app.domain.repositories.stock_data_repository import StockDataRepository
from app.domain.value_objects.stock_identifier import StockIdentifier

class YFinanceAdapter(StockDataRepository):
    """yfinance 用アダプター"""
    
    async def get_stock_info(
        self, 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        symbol = identifier.to_yfinance_symbol()
        
        # yfinance から銘柄情報を取得
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if not info:
            return None
        
        # レスポンスをドメインエンティティに変換
        return self._convert_to_stock_entity(info, identifier)
    
    async def get_stock_prices(
        self,
        identifier: StockIdentifier,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[Price]:
        symbol = identifier.to_yfinance_symbol()
        
        # yfinance から価格データを取得
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval=interval
        )
        
        # DataFrame をドメインエンティティに変換
        prices = []
        for index, row in df.iterrows():
            prices.append(self._convert_to_price_entity(index, row, identifier))
        
        return prices
    
    def _convert_to_stock_entity(
        self, 
        info: dict, 
        identifier: StockIdentifier
    ) -> Stock:
        """yfinance のレスポンスを Stock エンティティに変換"""
        from app.domain.entities.stock import StockCode
        
        # yfinance のデータを J-Quants のフォーマットにマッピング
        return Stock(
            code=StockCode(identifier.code),
            company_name=info.get("longName", ""),
            company_name_english=info.get("longName"),
            # yfinance には業種コードがないため、業種名から推測または None
            sector_17_code=None,
            sector_17_name=info.get("sector"),
            # ... その他のフィールド
        )
```

### 4.4 ファクトリーパターンによるデータソース選択

```python
# app/application/factories/data_source_factory.py
from enum import Enum
from typing import Dict
from app.domain.repositories.stock_data_repository import StockDataRepository
from app.infrastructure.adapters.jquants_adapter import JQuantsAdapter
from app.infrastructure.adapters.yfinance_adapter import YFinanceAdapter

class DataSource(Enum):
    JQUANTS = "jquants"
    YFINANCE = "yfinance"

class DataSourceFactory:
    """データソースファクトリー"""
    
    def __init__(self):
        self._adapters: Dict[DataSource, StockDataRepository] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """アダプターを初期化"""
        # J-Quants アダプター
        from app.infrastructure.jquants.client import JQuantsClient
        jquants_client = JQuantsClient()  # 設定から読み込み
        self._adapters[DataSource.JQUANTS] = JQuantsAdapter(jquants_client)
        
        # yfinance アダプター
        self._adapters[DataSource.YFINANCE] = YFinanceAdapter()
    
    def get_repository(
        self, 
        source: DataSource = DataSource.JQUANTS
    ) -> StockDataRepository:
        """指定されたデータソースのリポジトリを取得"""
        if source not in self._adapters:
            raise ValueError(f"Unknown data source: {source}")
        
        return self._adapters[source]
    
    def get_best_repository_for_market(
        self, 
        market: str
    ) -> StockDataRepository:
        """市場に最適なリポジトリを選択"""
        if market in ["TSE", "OSE", "NSE", "FSE", "SSE"]:  # 日本市場
            return self._adapters[DataSource.JQUANTS]
        else:  # その他の市場
            return self._adapters[DataSource.YFINANCE]
```

### 4.5 ユースケースでの使用例

```python
# app/application/use_cases/get_stock_data_use_case.py
from datetime import date
from typing import Optional
from app.application.factories.data_source_factory import (
    DataSourceFactory, 
    DataSource
)
from app.domain.value_objects.stock_identifier import StockIdentifier

class GetStockDataUseCase:
    """株式データ取得ユースケース"""
    
    def __init__(self, factory: DataSourceFactory):
        self._factory = factory
    
    async def execute(
        self,
        code: str,
        market: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        # 銘柄識別子を作成
        identifier = StockIdentifier(code=code, market=market)
        
        # データソースを選択
        if source:
            repository = self._factory.get_repository(DataSource(source))
        elif market:
            repository = self._factory.get_best_repository_for_market(market)
        else:
            repository = self._factory.get_repository()  # デフォルト
        
        # 銘柄情報を取得
        stock = await repository.get_stock_info(identifier)
        if not stock:
            raise ValueError(f"Stock not found: {code}")
        
        # 価格データを取得
        if start_date and end_date:
            prices = await repository.get_stock_prices(
                identifier, 
                start_date, 
                end_date
            )
        else:
            price = await repository.get_latest_price(identifier)
            prices = [price] if price else []
        
        return {
            "stock": stock,
            "prices": prices
        }
```

## 5. エラーハンドリング戦略

### 5.1 共通例外クラス

```python
# app/domain/exceptions/data_source_exceptions.py
class DataSourceError(Exception):
    """データソース関連の基底例外"""
    pass

class AuthenticationError(DataSourceError):
    """認証エラー"""
    pass

class RateLimitError(DataSourceError):
    """レート制限エラー"""
    pass

class DataNotFoundError(DataSourceError):
    """データが見つからない"""
    pass

class NetworkError(DataSourceError):
    """ネットワークエラー"""
    pass
```

### 5.2 アダプター内でのエラー変換

```python
# 各アダプター内で実装
async def get_stock_info(self, identifier: StockIdentifier) -> Optional[Stock]:
    try:
        # データソース固有の処理
        pass
    except JQuantsAuthError as e:
        raise AuthenticationError(f"J-Quants authentication failed: {e}")
    except JQuantsRateLimitError as e:
        raise RateLimitError(f"J-Quants rate limit exceeded: {e}")
    except Exception as e:
        raise DataSourceError(f"Unexpected error: {e}")
```

## 6. テスト戦略

### 6.1 単体テスト
- 各アダプターのモックを作成
- ドメインエンティティへの変換ロジックをテスト
- エラーハンドリングのテスト

### 6.2 統合テスト
- 実際の API との通信テスト（VCR を使用）
- データソース切り替えのテスト
- フォールバック機能のテスト

### 6.3 モックリポジトリ

```python
# tests/mocks/mock_stock_data_repository.py
class MockStockDataRepository(StockDataRepository):
    """テスト用モックリポジトリ"""
    
    def __init__(self, test_data: dict):
        self._test_data = test_data
    
    async def get_stock_info(
        self, 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        return self._test_data.get("stocks", {}).get(identifier.code)
```

## 7. 実装ロードマップ

### Phase 1: 基盤整備
1. StockIdentifier 値オブジェクトの実装
2. StockDataRepository インターフェースの定義
3. 共通例外クラスの定義

### Phase 2: アダプター実装
1. JQuantsAdapter の実装
2. YFinanceAdapter の実装
3. データ変換ロジックの実装

### Phase 3: ファクトリーとユースケース
1. DataSourceFactory の実装
2. 既存ユースケースの移行
3. 新規ユースケースの作成

### Phase 4: テストと最適化
1. 単体テストの作成
2. 統合テストの作成
3. パフォーマンス最適化

## 8. 考慮事項

### 8.1 パフォーマンス
- キャッシュ戦略の実装
- バッチ取得の最適化
- 非同期処理の活用

### 8.2 拡張性
- 新しいデータソースの追加が容易
- データ項目の追加に柔軟に対応
- プラグイン形式での拡張も検討

### 8.3 運用
- ログ出力の統一
- メトリクスの収集
- エラー通知の仕組み

## 9. まとめ

この設計により、以下の利点が得られます：

1. **データソースの透過的な切り替え**: ビジネスロジックを変更せずにデータソースを切り替え可能
2. **テストの容易性**: モックリポジトリによる単体テストが簡単
3. **拡張性**: 新しいデータソースの追加が容易
4. **保守性**: 各データソースの実装が分離されており、個別に更新可能
5. **一貫性**: 共通のインターフェースによりデータアクセスが統一される

この設計は、クリーンアーキテクチャの原則に従いながら、実用的で拡張可能なソリューションを提供します。