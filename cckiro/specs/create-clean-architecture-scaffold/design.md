# 設計書：クリーンアーキテクチャベースのアプリケーション雛形

## 1. アーキテクチャ概要

### 1.1 レイヤー構成
```
┌─────────────────────────────────────────────────────┐
│              Presentation Layer (API)                │
│  ┌─────────────────────────────────────────────┐    │
│  │  FastAPI Routes / Controllers               │    │
│  │  Request/Response Models                    │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│             Application Layer                        │
│  ┌─────────────────────────────────────────────┐    │
│  │  Use Cases / Application Services           │    │
│  │  DTOs / Port Interfaces                     │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│                Domain Layer                          │
│  ┌─────────────────────────────────────────────┐    │
│  │  Entities / Value Objects                   │    │
│  │  Domain Services / Business Rules           │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────┐
│           Infrastructure Layer                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Repository Implementations                 │    │
│  │  External API Clients                       │    │
│  │  Database / Cache Adapters                  │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 1.2 依存関係の方向
- 外側の層は内側の層に依存する
- 内側の層は外側の層を知らない
- インターフェースを使用した依存性の逆転

## 2. ディレクトリ構造

```
stockura/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI アプリケーションのエントリーポイント
│   │
│   ├── domain/                    # ドメイン層
│   │   ├── __init__.py
│   │   ├── entities/              # エンティティ
│   │   │   ├── __init__.py
│   │   │   ├── stock.py          # 株式エンティティ
│   │   │   └── price.py          # 価格エンティティ
│   │   ├── value_objects/         # 値オブジェクト
│   │   │   ├── __init__.py
│   │   │   ├── ticker_symbol.py  # ティッカーシンボル
│   │   │   └── time_period.py    # 期間
│   │   ├── exceptions/            # ドメイン例外
│   │   │   ├── __init__.py
│   │   │   └── stock_exceptions.py
│   │   └── services/              # ドメインサービス
│   │       ├── __init__.py
│   │       └── price_calculator.py
│   │
│   ├── application/               # アプリケーション層
│   │   ├── __init__.py
│   │   ├── use_cases/             # ユースケース
│   │   │   ├── __init__.py
│   │   │   ├── fetch_stock_price.py
│   │   │   └── analyze_stock.py
│   │   ├── interfaces/            # ポートインターフェース
│   │   │   ├── __init__.py
│   │   │   ├── repositories/     # リポジトリインターフェース
│   │   │   │   ├── __init__.py
│   │   │   │   └── stock_repository.py
│   │   │   └── external/         # 外部サービスインターフェース
│   │   │       ├── __init__.py
│   │   │       ├── jquants_client.py
│   │   │       └── yfinance_client.py
│   │   └── dtos/                  # データ転送オブジェクト
│   │       ├── __init__.py
│   │       └── stock_dto.py
│   │
│   ├── infrastructure/            # インフラストラクチャ層
│   │   ├── __init__.py
│   │   ├── database/              # データベース関連
│   │   │   ├── __init__.py
│   │   │   ├── connection.py     # DB 接続管理
│   │   │   ├── models/           # ORM モデル
│   │   │   │   ├── __init__.py
│   │   │   │   └── stock_model.py
│   │   │   └── repositories/     # リポジトリ実装
│   │   │       ├── __init__.py
│   │   │       └── stock_repository_impl.py
│   │   ├── cache/                 # キャッシュ関連
│   │   │   ├── __init__.py
│   │   │   └── redis_client.py
│   │   ├── external_api/          # 外部 API 実装
│   │   │   ├── __init__.py
│   │   │   ├── jquants/
│   │   │   │   ├── __init__.py
│   │   │   │   └── client.py
│   │   │   └── yfinance/
│   │   │       ├── __init__.py
│   │   │       └── client.py
│   │   └── job_queue/             # ジョブキュー
│   │       ├── __init__.py
│   │       ├── celery_app.py
│   │       └── tasks/
│   │           ├── __init__.py
│   │           └── stock_tasks.py
│   │
│   ├── presentation/              # プレゼンテーション層
│   │   ├── __init__.py
│   │   ├── api/                   # API エンドポイント
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py
│   │   │   │   └── endpoints/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── stocks.py
│   │   │   │       └── health.py
│   │   │   └── dependencies.py   # 依存性注入
│   │   ├── schemas/               # リクエスト/レスポンススキーマ
│   │   │   ├── __init__.py
│   │   │   ├── stock_schema.py
│   │   │   └── common_schema.py
│   │   └── middleware/            # ミドルウェア
│   │       ├── __init__.py
│   │       ├── error_handler.py
│   │       └── logging.py
│   │
│   └── core/                      # 共通設定・ユーティリティ
│       ├── __init__.py
│       ├── config.py              # 設定管理
│       ├── constants.py           # 定数定義
│       ├── logger.py              # ロギング設定
│       └── container.py           # DI コンテナ
│
├── tests/                         # テストコード
│   ├── __init__.py
│   ├── unit/                      # ユニットテスト
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/               # 統合テスト
│   │   └── api/
│   └── conftest.py               # pytest 設定
│
├── scripts/                       # ユーティリティスクリプト
│   ├── __init__.py
│   └── init_db.py                # DB 初期化スクリプト
│
├── docker/                        # Docker 関連ファイル
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── .env.example                   # 環境変数サンプル
├── .gitignore
├── requirements.txt               # 依存パッケージ
├── requirements-dev.txt          # 開発用依存パッケージ
├── pyproject.toml                # プロジェクト設定
└── README.md
```

## 3. 各層の詳細設計

### 3.1 ドメイン層

#### エンティティ例：Stock
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Stock:
    ticker_symbol: str
    company_name: str
    market: str
    sector: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

#### 値オブジェクト例：TickerSymbol
```python
class TickerSymbol:
    def __init__(self, value: str):
        if not self._validate(value):
            raise ValueError(f"Invalid ticker symbol: {value}")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    def _validate(self, value: str) -> bool:
        # バリデーションロジック
        return bool(value and value.isalnum())
```

### 3.2 アプリケーション層

#### ユースケース例：FetchStockPrice
```python
from abc import ABC, abstractmethod
from typing import Optional
from datetime import date

class FetchStockPriceUseCase:
    def __init__(
        self,
        stock_repository: StockRepositoryInterface,
        price_service: PriceServiceInterface
    ):
        self._stock_repository = stock_repository
        self._price_service = price_service
    
    async def execute(
        self,
        ticker_symbol: str,
        target_date: Optional[date] = None
    ) -> StockPriceDTO:
        # ユースケースのロジック
        pass
```

### 3.3 インフラストラクチャ層

#### リポジトリ実装例
```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

class StockRepositoryImpl(StockRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def find_by_ticker(self, ticker: str) -> Optional[Stock]:
        # データベースからの取得ロジック
        pass
    
    async def save(self, stock: Stock) -> Stock:
        # データベースへの保存ロジック
        pass
```

### 3.4 プレゼンテーション層

#### API エンドポイント例
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("/{ticker}/price")
async def get_stock_price(
    ticker: str,
    use_case: FetchStockPriceUseCase = Depends(get_fetch_stock_price_use_case)
):
    try:
        result = await use_case.execute(ticker)
        return result
    except StockNotFoundError:
        raise HTTPException(status_code=404, detail="Stock not found")
```

## 4. 依存性注入（DI）設計

### DI コンテナ
```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # 設定
    config = providers.Configuration()
    
    # データベース
    db_session = providers.Singleton(
        create_async_session,
        db_url=config.database.url
    )
    
    # リポジトリ
    stock_repository = providers.Factory(
        StockRepositoryImpl,
        session=db_session
    )
    
    # 外部 API クライアント
    jquants_client = providers.Singleton(
        JQuantsClient,
        api_key=config.jquants.api_key
    )
    
    # ユースケース
    fetch_stock_price_use_case = providers.Factory(
        FetchStockPriceUseCase,
        stock_repository=stock_repository,
        price_service=jquants_client
    )
```

## 5. 設定管理

### 環境変数と設定クラス
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # アプリケーション設定
    app_name: str = "Stockura"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # データベース設定
    database_url: str
    database_pool_size: int = 10
    
    # Redis 設定
    redis_url: str
    redis_ttl: int = 3600
    
    # 外部 API 設定
    jquants_api_key: str
    jquants_base_url: str = "https://api.jquants.com/v1"
    
    # Celery 設定
    celery_broker_url: str
    celery_result_backend: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

## 6. エラーハンドリング設計

### カスタム例外階層
```
BaseError
├── DomainError
│   ├── StockNotFoundError
│   └── InvalidTickerSymbolError
├── ApplicationError
│   ├── UseCaseError
│   └── ValidationError
└── InfrastructureError
    ├── DatabaseError
    └── ExternalAPIError
```

## 7. ロギング設計

- 構造化ログ（JSON 形式）
- ログレベル：DEBUG, INFO, WARNING, ERROR, CRITICAL
- コンテキスト情報の付与（リクエスト ID 、ユーザー ID 等）

## 8. テスト戦略

### テストの種類
1. **ユニットテスト**: 各層の個別コンポーネント
2. **統合テスト**: 層間の連携
3. **E2E テスト**: API エンドポイントの動作確認

### モックとテストダブル
- リポジトリインターフェースのモック
- 外部 API クライアントのスタブ
- インメモリデータベースの使用