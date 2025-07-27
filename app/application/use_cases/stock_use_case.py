from datetime import date
from typing import Optional

from app.domain.entities.stock import MarketCode, SectorCode17, SectorCode33, Stock, StockList
from app.domain.exceptions.jquants_exceptions import DataNotFoundError, ValidationError
from app.domain.repositories.stock_repository import StockRepository


class StockUseCase:
    """銘柄情報に関するユースケース"""

    def __init__(self, stock_repository: StockRepository) -> None:
        self._stock_repository = stock_repository

    async def get_all_stocks(self, use_cache: bool = True) -> StockList:
        """
        全上場銘柄一覧を取得

        Args:
            use_cache: キャッシュを使用するか

        Returns:
            StockList: 上場銘柄一覧

        Raises:
            DataNotFoundError: データが見つからない場合
            NetworkError: ネットワークエラーが発生した場合
        """
        # キャッシュを使用する場合
        if use_cache:
            cached_list = await self._stock_repository.load_cached_stock_list()
            if cached_list:
                return cached_list

        # API から取得
        stock_list = await self._stock_repository.get_listed_stocks()
        
        # キャッシュに保存
        await self._stock_repository.save_stock_list(stock_list)
        
        return stock_list

    async def get_stock_by_code(self, code: str) -> Stock:
        """
        銘柄コードから銘柄情報を取得

        Args:
            code: 銘柄コード（4 桁）

        Returns:
            Stock: 銘柄情報

        Raises:
            ValidationError: 銘柄コードが不正な場合
            DataNotFoundError: 銘柄が見つからない場合
            NetworkError: ネットワークエラーが発生した場合
        """
        # 銘柄コードのバリデーション
        if not code.isdigit() or len(code) != 4:
            raise ValidationError("銘柄コードは 4 桁の数字である必要があります")

        # リポジトリから取得
        stock = await self._stock_repository.get_stock_by_code(code)
        if not stock:
            raise DataNotFoundError(f"銘柄コード {code} の銘柄が見つかりません")

        return stock

    async def search_stocks(
        self,
        keyword: str,
        market_code: Optional[str] = None,
        sector_17_code: Optional[str] = None,
        sector_33_code: Optional[str] = None,
    ) -> StockList:
        """
        銘柄を検索

        Args:
            keyword: 検索キーワード（会社名の部分一致）
            market_code: 市場区分コード
            sector_17_code: 17 業種コード
            sector_33_code: 33 業種コード

        Returns:
            StockList: 検索結果の銘柄一覧

        Raises:
            ValidationError: 検索条件が不正な場合
            NetworkError: ネットワークエラーが発生した場合
        """
        if not keyword:
            raise ValidationError("検索キーワードは必須です")

        # 検索実行
        return await self._stock_repository.search_stocks(
            keyword=keyword,
            market_code=market_code,
            sector_17_code=sector_17_code,
            sector_33_code=sector_33_code,
        )

    async def get_stocks_by_market(self, market_code: str) -> StockList:
        """
        市場区分で銘柄を取得

        Args:
            market_code: 市場区分コード

        Returns:
            StockList: 指定市場の銘柄一覧

        Raises:
            ValidationError: 市場区分コードが不正な場合
            DataNotFoundError: データが見つからない場合
            NetworkError: ネットワークエラーが発生した場合
        """
        # 市場区分コードのバリデーション
        try:
            market = MarketCode(market_code)
        except ValueError:
            raise ValidationError(f"無効な市場区分コード: {market_code}")

        # 全銘柄を取得してフィルタリング
        all_stocks = await self.get_all_stocks()
        filtered_stocks = all_stocks.filter_by_market(market)
        
        if not filtered_stocks:
            raise DataNotFoundError(f"市場区分 {market.name} の銘柄が見つかりません")

        return StockList(stocks=filtered_stocks, updated_date=all_stocks.updated_date)

    async def get_stocks_by_sector_17(self, sector_code: str) -> StockList:
        """
        17 業種で銘柄を取得

        Args:
            sector_code: 17 業種コード

        Returns:
            StockList: 指定業種の銘柄一覧

        Raises:
            ValidationError: 業種コードが不正な場合
            DataNotFoundError: データが見つからない場合
            NetworkError: ネットワークエラーが発生した場合
        """
        # 業種コードのバリデーション
        try:
            sector = SectorCode17(sector_code)
        except ValueError:
            raise ValidationError(f"無効な 17 業種コード: {sector_code}")

        # 全銘柄を取得してフィルタリング
        all_stocks = await self.get_all_stocks()
        filtered_stocks = all_stocks.filter_by_sector_17(sector)
        
        if not filtered_stocks:
            raise DataNotFoundError(f"17 業種 {sector.name} の銘柄が見つかりません")

        return StockList(stocks=filtered_stocks, updated_date=all_stocks.updated_date)

    async def get_stocks_by_sector_33(self, sector_code: str) -> StockList:
        """
        33 業種で銘柄を取得

        Args:
            sector_code: 33 業種コード

        Returns:
            StockList: 指定業種の銘柄一覧

        Raises:
            ValidationError: 業種コードが不正な場合
            DataNotFoundError: データが見つからない場合
            NetworkError: ネットワークエラーが発生した場合
        """
        # 業種コードのバリデーション
        try:
            sector = SectorCode33(sector_code)
        except ValueError:
            raise ValidationError(f"無効な 33 業種コード: {sector_code}")

        # 全銘柄を取得してフィルタリング
        all_stocks = await self.get_all_stocks()
        filtered_stocks = all_stocks.filter_by_sector_33(sector)
        
        if not filtered_stocks:
            raise DataNotFoundError(f"33 業種 {sector.name} の銘柄が見つかりません")

        return StockList(stocks=filtered_stocks, updated_date=all_stocks.updated_date)

    async def refresh_stock_cache(self) -> StockList:
        """
        銘柄情報のキャッシュを更新

        Returns:
            StockList: 更新された銘柄一覧

        Raises:
            NetworkError: ネットワークエラーが発生した場合
        """
        # 強制的に API から取得
        return await self.get_all_stocks(use_cache=False)