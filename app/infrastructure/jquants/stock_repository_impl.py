import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from app.application.use_cases.auth_use_case import AuthUseCase
from app.domain.entities.auth import JQuantsCredentials
from app.domain.entities.stock import Stock, StockList
from app.domain.exceptions.jquants_exceptions import (
    DataNotFoundError,
    NetworkError,
    StorageError,
    ValidationError,
)
from app.domain.repositories.stock_repository import StockRepository
from app.infrastructure.jquants.base_client import JQuantsBaseClient


class JQuantsStockRepository(StockRepository):
    """J-Quants API 銘柄情報リポジトリの実装"""

    LISTED_INFO_ENDPOINT = "/listed/info"

    def __init__(
        self,
        auth_use_case: AuthUseCase,
        credentials: JQuantsCredentials,
        cache_dir: Optional[Path] = None,
    ) -> None:
        """
        Args:
            auth_use_case: 認証ユースケース
            credentials: 認証情報
            cache_dir: キャッシュディレクトリ（None の場合はデフォルト）
        """
        self._auth_use_case = auth_use_case
        self._credentials = credentials
        self._cache_dir = cache_dir or Path.home() / ".stockura" / "cache" / "stocks"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def get_listed_stocks(
        self,
        date: Optional[date] = None,
        code: Optional[str] = None,
    ) -> StockList:
        """上場銘柄一覧を取得"""
        # 認証情報の更新
        credentials = await self._auth_use_case.ensure_valid_token(self._credentials)
        
        # パラメータの構築
        params = {}
        if date:
            params["date"] = date.strftime("%Y-%m-%d")
        if code:
            params["code"] = code

        try:
            async with JQuantsBaseClient(credentials) as client:
                # ページネーション対応で全データを取得
                data_list = await client.get_paginated(
                    self.LISTED_INFO_ENDPOINT,
                    params=params,
                )

            # エンティティに変換
            stocks = []
            for data in data_list:
                try:
                    stock = Stock.from_dict(data)
                    stocks.append(stock)
                except (KeyError, ValueError) as e:
                    # 変換エラーはスキップ（ログに記録すべき）
                    continue

            if not stocks:
                raise DataNotFoundError("銘柄データが見つかりません")

            # 更新日を設定（最新のデータ日付を使用）
            updated_date = date or datetime.now().date()
            
            return StockList(stocks=stocks, updated_date=updated_date)

        except NetworkError:
            raise
        except Exception as e:
            raise NetworkError(f"銘柄一覧の取得中にエラーが発生しました: {str(e)}")

    async def get_stock_by_code(self, code: str) -> Optional[Stock]:
        """銘柄コードから銘柄情報を取得"""
        # バリデーション
        if not code.isdigit() or len(code) != 4:
            raise ValidationError("銘柄コードは 4 桁の数字である必要があります")

        # 特定銘柄のみ取得
        try:
            stock_list = await self.get_listed_stocks(code=code)
            return stock_list.get_by_code(code)
        except DataNotFoundError:
            return None

    async def search_stocks(
        self,
        keyword: str,
        market_code: Optional[str] = None,
        sector_17_code: Optional[str] = None,
        sector_33_code: Optional[str] = None,
    ) -> StockList:
        """銘柄を検索"""
        # 全銘柄を取得
        all_stocks = await self.get_listed_stocks()
        
        # キーワードで検索
        filtered_stocks = all_stocks.search_by_name(keyword)
        
        # 市場区分でフィルタリング
        if market_code:
            filtered_stocks = [
                stock for stock in filtered_stocks
                if stock.market_code and stock.market_code.value == market_code
            ]
        
        # 17 業種でフィルタリング
        if sector_17_code:
            filtered_stocks = [
                stock for stock in filtered_stocks
                if stock.sector_17_code and stock.sector_17_code.value == sector_17_code
            ]
        
        # 33 業種でフィルタリング
        if sector_33_code:
            filtered_stocks = [
                stock for stock in filtered_stocks
                if stock.sector_33_code and stock.sector_33_code.value == sector_33_code
            ]
        
        return StockList(stocks=filtered_stocks, updated_date=all_stocks.updated_date)

    async def save_stock_list(self, stock_list: StockList) -> None:
        """銘柄一覧を保存（キャッシュ）"""
        try:
            # キャッシュファイルパス
            cache_file = self._cache_dir / "stock_list.json"
            
            # データを辞書形式に変換
            data = {
                "updated_date": stock_list.updated_date.isoformat() if stock_list.updated_date else None,
                "stocks": [
                    {
                        "Code": stock.code.value,
                        "CompanyName": stock.company_name,
                        "CompanyNameEnglish": stock.company_name_english,
                        "Sector17Code": stock.sector_17_code.value if stock.sector_17_code else None,
                        "Sector17CodeName": stock.sector_17_name,
                        "Sector33Code": stock.sector_33_code.value if stock.sector_33_code else None,
                        "Sector33CodeName": stock.sector_33_name,
                        "ScaleCategory": stock.scale_category,
                        "MarketCode": stock.market_code.value if stock.market_code else None,
                        "MarketCodeName": stock.market_name,
                    }
                    for stock in stock_list.stocks
                ],
            }
            
            # ファイルに保存
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise StorageError(f"銘柄一覧の保存に失敗しました: {str(e)}")

    async def load_cached_stock_list(self, date: Optional[date] = None) -> Optional[StockList]:
        """キャッシュされた銘柄一覧を読み込み"""
        try:
            # キャッシュファイルパス
            cache_file = self._cache_dir / "stock_list.json"
            
            if not cache_file.exists():
                return None
            
            # ファイルから読み込み
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 更新日の確認
            cached_date = None
            if data.get("updated_date"):
                cached_date = datetime.fromisoformat(data["updated_date"]).date()
            
            # 日付指定がある場合は一致するか確認
            if date and cached_date != date:
                return None
            
            # エンティティに変換
            stocks = []
            for stock_data in data.get("stocks", []):
                try:
                    stock = Stock.from_dict(stock_data)
                    stocks.append(stock)
                except (KeyError, ValueError):
                    # 変換エラーはスキップ
                    continue
            
            if not stocks:
                return None
            
            return StockList(stocks=stocks, updated_date=cached_date)
            
        except FileNotFoundError:
            return None
        except Exception as e:
            raise StorageError(f"銘柄一覧の読み込みに失敗しました: {str(e)}")