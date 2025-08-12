"""Listed info repository interface."""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.domain.entities.listed_info import JQuantsListedInfo
from app.domain.value_objects.stock_code import StockCode


class ListedInfoRepositoryInterface(ABC):
    """上場銘柄情報リポジトリのインターフェース"""

    @abstractmethod
    async def save_all(self, listed_infos: List[JQuantsListedInfo]) -> None:
        """複数の上場銘柄情報を保存

        Args:
            listed_infos: 保存する上場銘柄情報のリスト

        Raises:
            StorageError: 保存に失敗した場合
        """
        pass

    @abstractmethod
    async def find_by_code_and_date(
        self, code: StockCode, target_date: date
    ) -> Optional[JQuantsListedInfo]:
        """銘柄コードと日付で検索

        Args:
            code: 銘柄コード
            target_date: 基準日

        Returns:
            JQuantsListedInfo: 上場銘柄情報
            None: データが見つからない場合

        Raises:
            StorageError: 検索に失敗した場合
        """
        pass

    @abstractmethod
    async def find_all_by_date(self, target_date: date) -> List[JQuantsListedInfo]:
        """日付で全銘柄を検索

        Args:
            target_date: 基準日

        Returns:
            List[JQuantsListedInfo]: 指定日付の全上場銘柄情報

        Raises:
            StorageError: 検索に失敗した場合
        """
        pass

    @abstractmethod
    async def find_latest_by_code(self, code: StockCode) -> Optional[JQuantsListedInfo]:
        """銘柄コードで最新の情報を検索

        Args:
            code: 銘柄コード

        Returns:
            JQuantsListedInfo: 最新の上場銘柄情報
            None: データが見つからない場合

        Raises:
            StorageError: 検索に失敗した場合
        """
        pass

    @abstractmethod
    async def delete_by_date(self, target_date: date) -> int:
        """指定日付のデータを削除

        Args:
            target_date: 削除対象の日付

        Returns:
            int: 削除された件数

        Raises:
            StorageError: 削除に失敗した場合
        """
        pass