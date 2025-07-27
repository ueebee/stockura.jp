from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.domain.entities.stock import Stock, StockList


class StockRepository(ABC):
    """銘柄情報リポジトリのインターフェース"""

    @abstractmethod
    async def get_listed_stocks(
        self,
        date: Optional[date] = None,
        code: Optional[str] = None,
    ) -> StockList:
        """
        上場銘柄一覧を取得

        Args:
            date: 取得日付（None の場合は最新）
            code: 銘柄コード（特定銘柄のみ取得する場合）

        Returns:
            StockList: 上場銘柄一覧

        Raises:
            DataNotFoundError: データが見つからない場合
            NetworkError: ネットワークエラーが発生した場合
        """
        pass

    @abstractmethod
    async def get_stock_by_code(self, code: str) -> Optional[Stock]:
        """
        銘柄コードから銘柄情報を取得

        Args:
            code: 銘柄コード（4 桁）

        Returns:
            Stock: 銘柄情報
            None: 銘柄が見つからない場合

        Raises:
            ValidationError: 銘柄コードが不正な場合
            NetworkError: ネットワークエラーが発生した場合
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def save_stock_list(self, stock_list: StockList) -> None:
        """
        銘柄一覧を保存（キャッシュ）

        Args:
            stock_list: 保存する銘柄一覧

        Raises:
            StorageError: 保存に失敗した場合
        """
        pass

    @abstractmethod
    async def load_cached_stock_list(self, date: Optional[date] = None) -> Optional[StockList]:
        """
        キャッシュされた銘柄一覧を読み込み

        Args:
            date: 取得日付（None の場合は最新）

        Returns:
            StockList: キャッシュされた銘柄一覧
            None: キャッシュが見つからない場合

        Raises:
            StorageError: 読み込みに失敗した場合
        """
        pass