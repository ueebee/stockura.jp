# データソース抽象化 実装例

## 1. ディレクトリ構造の提案

```
app/
├── domain/
│   ├── entities/
│   │   ├── stock.py          # 既存
│   │   ├── price.py          # 既存
│   │   └── financial.py      # 新規: 財務データエンティティ
│   ├── value_objects/
│   │   ├── ticker_symbol.py  # 既存
│   │   ├── stock_identifier.py  # 新規: 統一銘柄識別子
│   │   └── data_source.py    # 新規: データソース定義
│   ├── repositories/
│   │   ├── stock_repository.py  # 既存: 改修
│   │   ├── stock_data_repository.py  # 新規: 統一インターフェース
│   │   └── market_data_repository.py  # 新規: 市場データ
│   └── exceptions/
│       └── data_source_exceptions.py  # 新規: 共通例外
│
├── application/
│   ├── factories/
│   │   └── data_source_factory.py  # 新規: データソースファクトリー
│   ├── services/
│   │   └── stock_data_service.py  # 新規: データ統合サービス
│   └── use_cases/
│       ├── fetch_stock_data.py    # 新規: 統合データ取得
│       └── compare_data_sources.py  # 新規: データソース比較
│
└── infrastructure/
    ├── adapters/
    │   ├── __init__.py
    │   ├── base_adapter.py        # 新規: 基底アダプター
    │   ├── jquants_adapter.py     # 新規: J-Quants アダプター
    │   └── yfinance_adapter.py    # 新規: yfinance アダプター
    ├── cache/
    │   └── stock_data_cache.py    # 新規: データキャッシュ
    └── converters/
        ├── __init__.py
        ├── stock_converter.py      # 新規: 銘柄データ変換
        └── price_converter.py      # 新規: 価格データ変換
```

## 2. 詳細実装例

### 2.1 値オブジェクト: StockIdentifier

```python
# app/domain/value_objects/stock_identifier.py
from dataclasses import dataclass
from typing import Optional, Dict
import re

@dataclass(frozen=True)
class StockIdentifier:
    """
    データソースに依存しない統一銘柄識別子
    
    Examples:
        # 日本株
        >>> jp_stock = StockIdentifier.from_jquants_code("7203")
        >>> jp_stock.to_yfinance_symbol()
        '7203.T'
        
        # 米国株
        >>> us_stock = StockIdentifier.from_yfinance_symbol("AAPL")
        >>> us_stock.code
        'AAPL'
    """
    
    code: str  # 基本コード（例: "7203", "AAPL"）
    market: Optional[str] = None  # 市場コード（例: "TSE", "NYSE"）
    country: Optional[str] = None  # 国コード（例: "JP", "US"）
    
    # 市場サフィックスのマッピング
    MARKET_SUFFIXES = {
        "TSE": ".T",
        "OSE": ".O",
        "NSE": ".N",
        "FSE": ".F",
        "SSE": ".SS",
        "SZSE": ".SZ",
        "HKEX": ".HK",
        "NYSE": "",
        "NASDAQ": "",
    }
    
    def __post_init__(self):
        """バリデーション"""
        if not self.code:
            raise ValueError("Stock code cannot be empty")
        
        # 日本株の場合は 4 桁数字チェック
        if self.country == "JP" and not re.match(r"^\d{4}$", self.code):
            raise ValueError(f"Japanese stock code must be 4 digits: {self.code}")
    
    def to_jquants_code(self) -> str:
        """J-Quants 形式に変換"""
        if self.country != "JP":
            raise ValueError(f"J-Quants only supports Japanese stocks: {self.code}")
        return self.code
    
    def to_yfinance_symbol(self) -> str:
        """yfinance 形式に変換"""
        suffix = self.MARKET_SUFFIXES.get(self.market, "")
        return f"{self.code}{suffix}"
    
    @classmethod
    def from_jquants_code(cls, code: str) -> "StockIdentifier":
        """J-Quants コードから作成"""
        return cls(code=code, market="TSE", country="JP")
    
    @classmethod
    def from_yfinance_symbol(cls, symbol: str) -> "StockIdentifier":
        """yfinance シンボルから作成"""
        # サフィックスから市場を判定
        for market, suffix in cls.MARKET_SUFFIXES.items():
            if suffix and symbol.endswith(suffix):
                return cls(
                    code=symbol[:-len(suffix)],
                    market=market,
                    country=cls._get_country_from_market(market)
                )
        
        # サフィックスなしの場合（主に米国株）
        return cls(
            code=symbol,
            market="NYSE" if symbol.isupper() else None,
            country="US" if symbol.isupper() else None
        )
    
    @staticmethod
    def _get_country_from_market(market: str) -> str:
        """市場コードから国コードを取得"""
        market_to_country = {
            "TSE": "JP", "OSE": "JP", "NSE": "JP", "FSE": "JP", "SSE": "JP",
            "SSE": "CN", "SZSE": "CN",
            "HKEX": "HK",
            "NYSE": "US", "NASDAQ": "US",
        }
        return market_to_country.get(market, "")
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        """辞書形式に変換"""
        return {
            "code": self.code,
            "market": self.market,
            "country": self.country
        }
```

### 2.2 統一リポジトリインターフェース

```python
# app/domain/repositories/stock_data_repository.py
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from app.domain.entities.stock import Stock
from app.domain.entities.price import Price
from app.domain.value_objects.stock_identifier import StockIdentifier

class StockDataRepository(ABC):
    """
    株式データリポジトリの統一インターフェース
    
    全てのデータソースアダプターはこのインターフェースを実装する
    """
    
    @abstractmethod
    async def get_stock_info(
        self, 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        """
        銘柄基本情報を取得
        
        Args:
            identifier: 銘柄識別子
            
        Returns:
            銘柄情報エンティティ（見つからない場合は None）
            
        Raises:
            DataSourceError: データ取得エラー
        """
        pass
    
    @abstractmethod
    async def get_stock_prices(
        self,
        identifier: StockIdentifier,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[Price]:
        """
        株価履歴を取得
        
        Args:
            identifier: 銘柄識別子
            start_date: 開始日
            end_date: 終了日
            interval: データ間隔（1d, 1w, 1m など）
            
        Returns:
            価格エンティティのリスト
            
        Raises:
            DataSourceError: データ取得エラー
            ValueError: 無効なパラメータ
        """
        pass
    
    @abstractmethod
    async def get_latest_price(
        self,
        identifier: StockIdentifier
    ) -> Optional[Price]:
        """
        最新株価を取得
        
        Args:
            identifier: 銘柄識別子
            
        Returns:
            最新価格エンティティ（見つからない場合は None）
            
        Raises:
            DataSourceError: データ取得エラー
        """
        pass
    
    @abstractmethod
    async def search_stocks(
        self,
        query: str,
        market: Optional[str] = None,
        limit: int = 100
    ) -> List[Stock]:
        """
        銘柄を検索
        
        Args:
            query: 検索クエリ（企業名、コード等）
            market: 市場フィルター
            limit: 最大取得件数
            
        Returns:
            銘柄情報のリスト
            
        Raises:
            DataSourceError: データ取得エラー
        """
        pass
    
    @abstractmethod
    async def get_supported_markets(self) -> List[str]:
        """
        サポートされている市場のリストを取得
        
        Returns:
            市場コードのリスト
        """
        pass
    
    @abstractmethod
    async def is_market_open(self, market: str) -> bool:
        """
        指定市場が現在取引中かどうかを確認
        
        Args:
            market: 市場コード
            
        Returns:
            取引中の場合 True
        """
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """データソース名を取得"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """
        データソースの機能を取得
        
        Returns:
            機能フラグの辞書
            例: {
                "realtime_price": True,
                "historical_data": True,
                "financial_data": False,
                "options_data": True
            }
        """
        pass
```

### 2.3 J-Quants アダプター実装

```python
# app/infrastructure/adapters/jquants_adapter.py
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import asyncio
from app.domain.entities.stock import Stock, StockCode, MarketCode
from app.domain.entities.price import Price
from app.domain.repositories.stock_data_repository import StockDataRepository
from app.domain.value_objects.stock_identifier import StockIdentifier
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.exceptions.data_source_exceptions import (
    DataSourceError, AuthenticationError, RateLimitError, DataNotFoundError
)
from app.infrastructure.jquants.base_client import JQuantsBaseClient
from app.infrastructure.converters.stock_converter import JQuantsStockConverter
from app.infrastructure.converters.price_converter import JQuantsPriceConverter

class JQuantsAdapter(StockDataRepository):
    """J-Quants API 用アダプター"""
    
    def __init__(
        self, 
        client: JQuantsBaseClient,
        stock_converter: JQuantsStockConverter,
        price_converter: JQuantsPriceConverter
    ):
        self._client = client
        self._stock_converter = stock_converter
        self._price_converter = price_converter
        self._market_cache: Optional[Dict[str, bool]] = None
    
    async def get_stock_info(
        self, 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        """銘柄情報を取得"""
        try:
            code = identifier.to_jquants_code()
            
            # API リクエスト
            response = await self._client.get(
                "/listed/info",
                params={"code": code}
            )
            
            if not response or "info" not in response:
                return None
            
            info_list = response["info"]
            if not info_list:
                return None
            
            # 最新のデータを使用
            latest_info = info_list[0]
            return self._stock_converter.convert(latest_info)
            
        except ValueError as e:
            # J-Quants がサポートしていない銘柄
            return None
        except Exception as e:
            raise DataSourceError(f"Failed to get stock info: {e}")
    
    async def get_stock_prices(
        self,
        identifier: StockIdentifier,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[Price]:
        """株価履歴を取得"""
        if interval != "1d":
            # J-Quants は日次データのみサポート
            raise ValueError(f"J-Quants only supports daily interval, got: {interval}")
        
        try:
            code = identifier.to_jquants_code()
            
            # API リクエスト（ページネーション対応）
            all_quotes = []
            pagination_key = None
            
            while True:
                params = {
                    "code": code,
                    "from": start_date.strftime("%Y%m%d"),
                    "to": end_date.strftime("%Y%m%d")
                }
                if pagination_key:
                    params["pagination_key"] = pagination_key
                
                response = await self._client.get(
                    "/prices/daily_quotes",
                    params=params
                )
                
                quotes = response.get("daily_quotes", [])
                all_quotes.extend(quotes)
                
                # ページネーション確認
                pagination_key = response.get("pagination_key")
                if not pagination_key:
                    break
            
            # エンティティに変換
            prices = []
            for quote in all_quotes:
                price = self._price_converter.convert(quote, identifier)
                if price:
                    prices.append(price)
            
            return sorted(prices, key=lambda p: p.date)
            
        except Exception as e:
            raise DataSourceError(f"Failed to get stock prices: {e}")
    
    async def get_latest_price(
        self,
        identifier: StockIdentifier
    ) -> Optional[Price]:
        """最新株価を取得"""
        try:
            # 今日または最新営業日のデータを取得
            today = date.today()
            prices = await self.get_stock_prices(
                identifier,
                today,
                today,
                "1d"
            )
            
            if prices:
                return prices[-1]
            
            # 過去 5 営業日まで遡って検索
            from datetime import timedelta
            for i in range(1, 6):
                check_date = today - timedelta(days=i)
                prices = await self.get_stock_prices(
                    identifier,
                    check_date,
                    check_date,
                    "1d"
                )
                if prices:
                    return prices[-1]
            
            return None
            
        except Exception as e:
            raise DataSourceError(f"Failed to get latest price: {e}")
    
    async def search_stocks(
        self,
        query: str,
        market: Optional[str] = None,
        limit: int = 100
    ) -> List[Stock]:
        """銘柄を検索"""
        try:
            # 全銘柄を取得（J-Quants は検索 API がないため）
            response = await self._client.get("/listed/info")
            
            if not response or "info" not in response:
                return []
            
            all_stocks = []
            for info in response["info"]:
                stock = self._stock_converter.convert(info)
                if stock:
                    all_stocks.append(stock)
            
            # フィルタリング
            results = []
            query_lower = query.lower()
            
            for stock in all_stocks:
                # 市場フィルター
                if market and stock.market_code.value != market:
                    continue
                
                # テキスト検索
                if (query_lower in stock.code.value.lower() or
                    query_lower in stock.company_name.lower() or
                    (stock.company_name_english and 
                     query_lower in stock.company_name_english.lower())):
                    results.append(stock)
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            raise DataSourceError(f"Failed to search stocks: {e}")
    
    async def get_supported_markets(self) -> List[str]:
        """サポートされている市場のリスト"""
        return ["TSE", "OSE", "NSE", "FSE", "SSE"]
    
    async def is_market_open(self, market: str) -> bool:
        """市場が開いているか確認"""
        if market not in await self.get_supported_markets():
            return False
        
        # キャッシュから取得または更新
        if self._market_cache is None:
            await self._update_market_status()
        
        return self._market_cache.get(market, False)
    
    async def _update_market_status(self):
        """市場状態を更新"""
        try:
            # J-Quants のトレーディングカレンダーから判定
            today = date.today()
            response = await self._client.get(
                "/markets/trading_calendar",
                params={"date": today.strftime("%Y%m%d")}
            )
            
            self._market_cache = {}
            for market in await self.get_supported_markets():
                # 簡易的な実装（実際はカレンダーデータから判定）
                self._market_cache[market] = response.get("is_trading_day", False)
                
        except Exception:
            self._market_cache = {}
    
    @property
    def source_name(self) -> str:
        return "J-Quants"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "realtime_price": False,  # 日次更新のみ
            "historical_data": True,
            "financial_data": True,
            "options_data": False,
            "dividend_data": True,
            "market_indices": True,
            "intraday_data": False,
        }
```

### 2.4 yfinance アダプター実装

```python
# app/infrastructure/adapters/yfinance_adapter.py
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import yfinance as yf
import pandas as pd
from app.domain.entities.stock import Stock, StockCode
from app.domain.entities.price import Price
from app.domain.repositories.stock_data_repository import StockDataRepository
from app.domain.value_objects.stock_identifier import StockIdentifier
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.exceptions.data_source_exceptions import DataSourceError
from app.infrastructure.converters.stock_converter import YFinanceStockConverter
from app.infrastructure.converters.price_converter import YFinancePriceConverter

class YFinanceAdapter(StockDataRepository):
    """yfinance 用アダプター"""
    
    def __init__(
        self,
        stock_converter: YFinanceStockConverter,
        price_converter: YFinancePriceConverter
    ):
        self._stock_converter = stock_converter
        self._price_converter = price_converter
    
    async def get_stock_info(
        self, 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        """銘柄情報を取得"""
        try:
            symbol = identifier.to_yfinance_symbol()
            ticker = yf.Ticker(symbol)
            
            # 銘柄情報を取得
            info = ticker.info
            if not info or "symbol" not in info:
                return None
            
            return self._stock_converter.convert(info, identifier)
            
        except Exception as e:
            raise DataSourceError(f"Failed to get stock info: {e}")
    
    async def get_stock_prices(
        self,
        identifier: StockIdentifier,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[Price]:
        """株価履歴を取得"""
        try:
            symbol = identifier.to_yfinance_symbol()
            ticker = yf.Ticker(symbol)
            
            # yfinance の interval フォーマットを確認
            valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", 
                             "1h", "1d", "5d", "1wk", "1mo", "3mo"]
            if interval not in valid_intervals:
                raise ValueError(f"Invalid interval: {interval}")
            
            # データ取得
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval=interval,
                auto_adjust=True,  # 調整済み価格を使用
                prepost=False,
                actions=True
            )
            
            if df.empty:
                return []
            
            # DataFrame をエンティティに変換
            prices = []
            for index, row in df.iterrows():
                price = self._price_converter.convert(index, row, identifier)
                if price:
                    prices.append(price)
            
            return prices
            
        except Exception as e:
            raise DataSourceError(f"Failed to get stock prices: {e}")
    
    async def get_latest_price(
        self,
        identifier: StockIdentifier
    ) -> Optional[Price]:
        """最新株価を取得"""
        try:
            symbol = identifier.to_yfinance_symbol()
            ticker = yf.Ticker(symbol)
            
            # リアルタイムデータを取得
            info = ticker.info
            if not info:
                return None
            
            # 現在価格情報から Price エンティティを作成
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            if not current_price:
                # 履歴から最新データを取得
                df = ticker.history(period="1d")
                if df.empty:
                    return None
                
                last_row = df.iloc[-1]
                return self._price_converter.convert(df.index[-1], last_row, identifier)
            
            # リアルタイムデータからエンティティを作成
            return Price(
                ticker_symbol=TickerSymbol(identifier.code),
                date=date.today(),
                timestamp=datetime.now(),
                open=float(info.get("open", current_price)),
                high=float(info.get("dayHigh", current_price)),
                low=float(info.get("dayLow", current_price)),
                close=float(current_price),
                volume=int(info.get("volume", 0)),
                adjusted_close=float(current_price)
            )
            
        except Exception as e:
            raise DataSourceError(f"Failed to get latest price: {e}")
    
    async def search_stocks(
        self,
        query: str,
        market: Optional[str] = None,
        limit: int = 100
    ) -> List[Stock]:
        """銘柄を検索"""
        try:
            # yfinance には直接的な検索 API がないため、
            # Yahoo Finance の検索機能を模倣
            # 実装の簡略化のため、事前定義されたシンボルリストから検索
            
            results = []
            
            # クエリがティッカーシンボルの場合
            if query.upper() == query and len(query) <= 5:
                try:
                    ticker = yf.Ticker(query)
                    info = ticker.info
                    if info and "symbol" in info:
                        identifier = StockIdentifier.from_yfinance_symbol(query)
                        stock = self._stock_converter.convert(info, identifier)
                        if stock:
                            results.append(stock)
                except:
                    pass
            
            # TODO: より高度な検索機能の実装
            # - Yahoo Finance API の screener 機能を使用
            # - 外部の銘柄リストデータベースとの連携
            
            return results[:limit]
            
        except Exception as e:
            raise DataSourceError(f"Failed to search stocks: {e}")
    
    async def get_supported_markets(self) -> List[str]:
        """サポートされている市場のリスト"""
        # yfinance は世界中の市場をサポート
        return [
            "NYSE", "NASDAQ", "TSE", "LSE", "HKEX", 
            "SSE", "SZSE", "NSE", "BSE", "ASX",
            "TSX", "XETRA", "EURONEXT"
        ]
    
    async def is_market_open(self, market: str) -> bool:
        """市場が開いているか確認"""
        try:
            # 簡易的な実装（実際は各市場の営業時間を考慮）
            from datetime import timezone
            import pytz
            
            market_timezones = {
                "NYSE": "US/Eastern",
                "NASDAQ": "US/Eastern",
                "TSE": "Asia/Tokyo",
                "LSE": "Europe/London",
                "HKEX": "Asia/Hong_Kong",
            }
            
            tz_name = market_timezones.get(market)
            if not tz_name:
                return False
            
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            
            # 平日の取引時間内かチェック（簡易版）
            if now.weekday() >= 5:  # 土日
                return False
            
            # 各市場の取引時間（簡易版）
            market_hours = {
                "NYSE": (9, 30, 16, 0),  # 9:30-16:00
                "NASDAQ": (9, 30, 16, 0),
                "TSE": (9, 0, 15, 0),  # 9:00-15:00
                "LSE": (8, 0, 16, 30),  # 8:00-16:30
                "HKEX": (9, 30, 16, 0),  # 9:30-16:00
            }
            
            if market in market_hours:
                open_h, open_m, close_h, close_m = market_hours[market]
                current_time = now.hour * 60 + now.minute
                open_time = open_h * 60 + open_m
                close_time = close_h * 60 + close_m
                
                return open_time <= current_time <= close_time
            
            return False
            
        except Exception:
            return False
    
    @property
    def source_name(self) -> str:
        return "yfinance"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "realtime_price": True,
            "historical_data": True,
            "financial_data": True,
            "options_data": True,
            "dividend_data": True,
            "market_indices": True,
            "intraday_data": True,
        }
```

### 2.5 データコンバーター

```python
# app/infrastructure/converters/stock_converter.py
from typing import Optional, Dict, Any
from app.domain.entities.stock import Stock, StockCode, MarketCode
from app.domain.value_objects.stock_identifier import StockIdentifier

class JQuantsStockConverter:
    """J-Quants のレスポンスをドメインエンティティに変換"""
    
    def convert(self, data: Dict[str, Any]) -> Optional[Stock]:
        """API レスポンスを Stock エンティティに変換"""
        try:
            # マーケットコードの変換
            market_code = self._parse_market_code(data.get("MarketCode"))
            
            # セクターコードの変換
            sector_17_code = self._parse_sector_17_code(data.get("Sector17Code"))
            sector_33_code = self._parse_sector_33_code(data.get("Sector33Code"))
            
            return Stock(
                code=StockCode(data["Code"]),
                company_name=data["CompanyName"],
                company_name_english=data.get("CompanyNameEnglish"),
                sector_17_code=sector_17_code,
                sector_17_name=data.get("Sector17CodeName"),
                sector_33_code=sector_33_code,
                sector_33_name=data.get("Sector33CodeName"),
                scale_category=data.get("ScaleCategory"),
                market_code=market_code,
                market_name=data.get("MarketCodeName"),
            )
        except (KeyError, ValueError) as e:
            # 必須フィールドが欠けている場合は None を返す
            return None
    
    def _parse_market_code(self, code: Optional[str]) -> Optional[MarketCode]:
        """市場コードを Enum に変換"""
        if not code:
            return None
        try:
            return MarketCode(code)
        except ValueError:
            return None
    
    def _parse_sector_17_code(self, code: Optional[str]) -> Optional[Any]:
        """17 業種コードを Enum に変換"""
        # 実装省略
        return None
    
    def _parse_sector_33_code(self, code: Optional[str]) -> Optional[Any]:
        """33 業種コードを Enum に変換"""
        # 実装省略
        return None


class YFinanceStockConverter:
    """yfinance のレスポンスをドメインエンティティに変換"""
    
    def convert(
        self, 
        info: Dict[str, Any], 
        identifier: StockIdentifier
    ) -> Optional[Stock]:
        """yfinance 情報を Stock エンティティに変換"""
        try:
            # 市場コードの推定
            market_code = self._estimate_market_code(
                info.get("exchange"), 
                identifier.market
            )
            
            # 業種の変換（yfinance は業種名のみ提供）
            sector_name = info.get("sector", "")
            
            return Stock(
                code=StockCode(identifier.code),
                company_name=info.get("longName", info.get("shortName", "")),
                company_name_english=info.get("longName"),
                sector_17_code=None,  # yfinance では取得不可
                sector_17_name=sector_name,
                sector_33_code=None,  # yfinance では取得不可
                sector_33_name=info.get("industry"),
                scale_category=self._estimate_scale_category(info),
                market_code=market_code,
                market_name=info.get("exchange"),
            )
        except (KeyError, ValueError) as e:
            return None
    
    def _estimate_market_code(
        self, 
        exchange: Optional[str], 
        identifier_market: Optional[str]
    ) -> Optional[MarketCode]:
        """取引所情報から市場コードを推定"""
        if identifier_market == "TSE":
            # 東証の市場区分を推定（実際はより詳細な判定が必要）
            return MarketCode.PRIME
        return None
    
    def _estimate_scale_category(self, info: Dict[str, Any]) -> Optional[str]:
        """企業規模カテゴリを推定"""
        market_cap = info.get("marketCap", 0)
        if market_cap > 1_000_000_000_000:  # 1 兆円以上
            return "TOPIX Core30"
        elif market_cap > 100_000_000_000:  # 1000 億円以上
            return "TOPIX Large70"
        elif market_cap > 10_000_000_000:  # 100 億円以上
            return "TOPIX Mid400"
        else:
            return "TOPIX Small"
```

### 2.6 データソースファクトリー

```python
# app/application/factories/data_source_factory.py
from enum import Enum
from typing import Dict, Optional
from app.domain.repositories.stock_data_repository import StockDataRepository
from app.infrastructure.adapters.jquants_adapter import JQuantsAdapter
from app.infrastructure.adapters.yfinance_adapter import YFinanceAdapter
from app.infrastructure.converters.stock_converter import (
    JQuantsStockConverter, YFinanceStockConverter
)
from app.infrastructure.converters.price_converter import (
    JQuantsPriceConverter, YFinancePriceConverter
)
from app.core.config import settings

class DataSource(Enum):
    """利用可能なデータソース"""
    JQUANTS = "jquants"
    YFINANCE = "yfinance"
    AUTO = "auto"  # 自動選択

class DataSourceFactory:
    """
    データソースファクトリー
    
    設定とコンテキストに基づいて適切なデータソースを選択・提供する
    """
    
    def __init__(self):
        self._adapters: Dict[DataSource, StockDataRepository] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """アダプターを初期化"""
        # J-Quants アダプター
        if settings.JQUANTS_ENABLED:
            from app.infrastructure.jquants.base_client import JQuantsBaseClient
            from app.application.use_cases.auth_use_case import AuthUseCase
            from app.domain.entities.auth import JQuantsCredentials
            
            # 認証情報とクライアントの設定
            credentials = JQuantsCredentials(
                email=settings.JQUANTS_EMAIL,
                password=settings.JQUANTS_PASSWORD
            )
            auth_use_case = AuthUseCase(...)  # 依存性注入
            client = JQuantsBaseClient(credentials)
            
            # コンバーターの作成
            stock_converter = JQuantsStockConverter()
            price_converter = JQuantsPriceConverter()
            
            # アダプターの作成
            self._adapters[DataSource.JQUANTS] = JQuantsAdapter(
                client=client,
                stock_converter=stock_converter,
                price_converter=price_converter
            )
        
        # yfinance アダプター
        if settings.YFINANCE_ENABLED:
            stock_converter = YFinanceStockConverter()
            price_converter = YFinancePriceConverter()
            
            self._adapters[DataSource.YFINANCE] = YFinanceAdapter(
                stock_converter=stock_converter,
                price_converter=price_converter
            )
    
    def get_repository(
        self, 
        source: DataSource = DataSource.AUTO,
        identifier: Optional[StockIdentifier] = None
    ) -> StockDataRepository:
        """
        指定されたデータソースのリポジトリを取得
        
        Args:
            source: データソース指定
            identifier: 銘柄識別子（AUTO 選択時に使用）
            
        Returns:
            適切なデータソースリポジトリ
            
        Raises:
            ValueError: 無効なデータソースまたは利用不可
        """
        if source == DataSource.AUTO:
            return self._select_best_repository(identifier)
        
        if source not in self._adapters:
            available = list(self._adapters.keys())
            raise ValueError(
                f"Data source {source.value} is not available. "
                f"Available sources: {available}"
            )
        
        return self._adapters[source]
    
    def _select_best_repository(
        self, 
        identifier: Optional[StockIdentifier] = None
    ) -> StockDataRepository:
        """最適なリポジトリを自動選択"""
        # 銘柄識別子に基づく選択
        if identifier:
            if identifier.country == "JP":
                # 日本株は J-Quants を優先
                if DataSource.JQUANTS in self._adapters:
                    return self._adapters[DataSource.JQUANTS]
            else:
                # 海外株は yfinance を使用
                if DataSource.YFINANCE in self._adapters:
                    return self._adapters[DataSource.YFINANCE]
        
        # デフォルトの優先順位
        priority = [DataSource.JQUANTS, DataSource.YFINANCE]
        for source in priority:
            if source in self._adapters:
                return self._adapters[source]
        
        raise ValueError("No data source available")
    
    def get_all_repositories(self) -> Dict[DataSource, StockDataRepository]:
        """全ての利用可能なリポジトリを取得"""
        return self._adapters.copy()
    
    def is_available(self, source: DataSource) -> bool:
        """指定したデータソースが利用可能か確認"""
        return source in self._adapters
```

### 2.7 統合ユースケース

```python
# app/application/use_cases/fetch_stock_data.py
from datetime import date
from typing import Optional, List, Dict, Any
from app.application.factories.data_source_factory import (
    DataSourceFactory, DataSource
)
from app.domain.value_objects.stock_identifier import StockIdentifier
from app.domain.entities.stock import Stock
from app.domain.entities.price import Price
from app.domain.exceptions.data_source_exceptions import DataSourceError
from app.core.logger import get_logger

logger = get_logger(__name__)

class FetchStockDataUseCase:
    """
    統合株式データ取得ユースケース
    
    複数のデータソースから最適なデータを取得し、
    フォールバック機能も提供する
    """
    
    def __init__(
        self, 
        factory: DataSourceFactory,
        cache_service: Optional[Any] = None
    ):
        self._factory = factory
        self._cache = cache_service
    
    async def execute(
        self,
        code: str,
        market: Optional[str] = None,
        country: Optional[str] = None,
        source: str = "auto",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        with_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        株式データを取得
        
        Args:
            code: 銘柄コード
            market: 市場コード
            country: 国コード
            source: データソース（"auto", "jquants", "yfinance"）
            start_date: 価格データ開始日
            end_date: 価格データ終了日
            with_fallback: フォールバック有効化
            
        Returns:
            株式情報と価格データの辞書
        """
        # 銘柄識別子を作成
        identifier = StockIdentifier(
            code=code,
            market=market,
            country=country
        )
        
        # キャッシュチェック
        cache_key = f"stock_data:{identifier.code}:{market}:{country}"
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for {cache_key}")
                return cached
        
        # データソース選択
        source_enum = DataSource(source.lower())
        
        # データ取得試行
        result = None
        errors = []
        
        if with_fallback and source_enum == DataSource.AUTO:
            # 全てのデータソースを試行
            for ds, repo in self._factory.get_all_repositories().items():
                try:
                    result = await self._fetch_from_repository(
                        repo, identifier, start_date, end_date
                    )
                    if result:
                        logger.info(f"Successfully fetched data from {ds.value}")
                        break
                except DataSourceError as e:
                    errors.append((ds.value, str(e)))
                    logger.warning(f"Failed to fetch from {ds.value}: {e}")
        else:
            # 指定されたデータソースのみ使用
            try:
                repo = self._factory.get_repository(source_enum, identifier)
                result = await self._fetch_from_repository(
                    repo, identifier, start_date, end_date
                )
            except DataSourceError as e:
                errors.append((source, str(e)))
                raise
        
        if not result:
            error_msgs = [f"{src}: {msg}" for src, msg in errors]
            raise DataSourceError(
                f"Failed to fetch data from all sources. Errors: {error_msgs}"
            )
        
        # キャッシュに保存
        if self._cache:
            await self._cache.set(cache_key, result, expire=3600)  # 1 時間
        
        return result
    
    async def _fetch_from_repository(
        self,
        repository: StockDataRepository,
        identifier: StockIdentifier,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """リポジトリからデータを取得"""
        # 銘柄情報を取得
        stock = await repository.get_stock_info(identifier)
        if not stock:
            return None
        
        # 価格データを取得
        prices = []
        latest_price = None
        
        if start_date and end_date:
            prices = await repository.get_stock_prices(
                identifier, start_date, end_date
            )
        else:
            latest_price = await repository.get_latest_price(identifier)
        
        # 追加情報
        capabilities = repository.capabilities
        
        return {
            "stock": stock,
            "prices": prices,
            "latest_price": latest_price,
            "source": repository.source_name,
            "capabilities": capabilities,
            "fetched_at": datetime.now()
        }
```

### 2.8 比較ユースケース

```python
# app/application/use_cases/compare_data_sources.py
from typing import Dict, List, Any
from app.application.factories.data_source_factory import DataSourceFactory
from app.domain.value_objects.stock_identifier import StockIdentifier
from app.core.logger import get_logger

logger = get_logger(__name__)

class CompareDataSourcesUseCase:
    """
    複数のデータソースを比較するユースケース
    
    データの完全性、更新頻度、カバレッジなどを比較
    """
    
    def __init__(self, factory: DataSourceFactory):
        self._factory = factory
    
    async def execute(
        self,
        code: str,
        market: Optional[str] = None,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        指定銘柄のデータを全てのソースから取得して比較
        
        Returns:
            比較結果の辞書
        """
        identifier = StockIdentifier(
            code=code,
            market=market,
            country=country
        )
        
        results = {}
        
        # 各データソースから情報を取得
        for source, repository in self._factory.get_all_repositories().items():
            try:
                stock_info = await repository.get_stock_info(identifier)
                latest_price = await repository.get_latest_price(identifier)
                
                results[source.value] = {
                    "available": True,
                    "stock_info": stock_info,
                    "latest_price": latest_price,
                    "capabilities": repository.capabilities,
                    "error": None
                }
                
            except Exception as e:
                results[source.value] = {
                    "available": False,
                    "stock_info": None,
                    "latest_price": None,
                    "capabilities": repository.capabilities,
                    "error": str(e)
                }
        
        # 比較分析
        comparison = self._analyze_differences(results)
        
        return {
            "identifier": identifier.to_dict(),
            "sources": results,
            "comparison": comparison
        }
    
    def _analyze_differences(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """データソース間の差異を分析"""
        available_sources = [
            src for src, data in results.items() 
            if data["available"]
        ]
        
        if len(available_sources) < 2:
            return {
                "comparable": False,
                "reason": "Less than 2 sources available"
            }
        
        # 価格の比較
        prices = {}
        for src, data in results.items():
            if data["latest_price"]:
                prices[src] = data["latest_price"].close
        
        price_diff = None
        if len(prices) >= 2:
            price_values = list(prices.values())
            price_diff = {
                "max": max(price_values),
                "min": min(price_values),
                "diff": max(price_values) - min(price_values),
                "diff_percent": ((max(price_values) - min(price_values)) / 
                               min(price_values) * 100)
            }
        
        return {
            "comparable": True,
            "available_sources": available_sources,
            "price_comparison": price_diff,
            "data_completeness": self._check_data_completeness(results)
        }
    
    def _check_data_completeness(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """データの完全性をチェック"""
        completeness = {}
        
        for src, data in results.items():
            if not data["available"]:
                completeness[src] = 0.0
                continue
            
            score = 0.0
            if data["stock_info"]:
                score += 0.5
            if data["latest_price"]:
                score += 0.5
            
            completeness[src] = score
        
        return completeness
```

## 3. 設定ファイル

```python
# app/core/config.py への追加
from pydantic import BaseSettings

class Settings(BaseSettings):
    # 既存の設定...
    
    # データソース設定
    JQUANTS_ENABLED: bool = True
    JQUANTS_EMAIL: str = ""
    JQUANTS_PASSWORD: str = ""
    JQUANTS_API_BASE_URL: str = "https://api.jquants.com/v1"
    JQUANTS_TIMEOUT: int = 30
    JQUANTS_MAX_RETRIES: int = 3
    
    YFINANCE_ENABLED: bool = True
    YFINANCE_TIMEOUT: int = 30
    YFINANCE_MAX_WORKERS: int = 5
    
    # デフォルトデータソース
    DEFAULT_DATA_SOURCE: str = "auto"
    
    # キャッシュ設定
    STOCK_DATA_CACHE_TTL: int = 3600  # 1 時間
    PRICE_DATA_CACHE_TTL: int = 300   # 5 分
    
    class Config:
        env_file = ".env"
```

## 4. まとめ

この実装例では、以下の点を実現しています：

1. **統一インターフェース**: `StockDataRepository` により、異なるデータソースを同じインターフェースで扱える
2. **柔軟な銘柄識別**: `StockIdentifier` により、各データソースの銘柄コード形式の違いを吸収
3. **アダプターパターン**: 各データソースの特性を維持しながら統一的にアクセス
4. **ファクトリーパターン**: データソースの選択と初期化を一元管理
5. **フォールバック機能**: 一つのデータソースが失敗しても他で補完
6. **比較機能**: 複数のデータソースからのデータを比較・検証

この設計により、新しいデータソースの追加も容易で、既存のビジネスロジックに影響を与えることなく拡張できます。