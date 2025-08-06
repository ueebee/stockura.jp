"""週次信用取引残高リポジトリインターフェース"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.domain.entities import WeeklyMarginInterest


class WeeklyMarginInterestRepository(ABC):
    """週次信用取引残高リポジトリのインターフェース"""

    @abstractmethod
    async def save(self, weekly_margin_interest: WeeklyMarginInterest) -> None:
        """週次信用取引残高を保存する

        Args:
            weekly_margin_interest: 保存する週次信用取引残高エンティティ
        """
        pass

    @abstractmethod
    async def save_bulk(
        self, weekly_margin_interests: List[WeeklyMarginInterest]
    ) -> None:
        """複数の週次信用取引残高を一括保存する

        Args:
            weekly_margin_interests: 保存する週次信用取引残高エンティティのリスト
        """
        pass

    @abstractmethod
    async def find_by_code_and_date(
        self, code: str, date: date
    ) -> Optional[WeeklyMarginInterest]:
        """銘柄コードと日付で週次信用取引残高を検索する

        Args:
            code: 銘柄コード
            date: 週末日付

        Returns:
            見つかった場合は WeeklyMarginInterest 、見つからない場合は None
        """
        pass

    @abstractmethod
    async def find_by_code_and_date_range(
        self, code: str, start_date: date, end_date: date
    ) -> List[WeeklyMarginInterest]:
        """銘柄コードと日付範囲で週次信用取引残高を検索する

        Args:
            code: 銘柄コード
            start_date: 開始日
            end_date: 終了日

        Returns:
            検索結果のリスト
        """
        pass

    @abstractmethod
    async def find_by_date(self, date: date) -> List[WeeklyMarginInterest]:
        """日付で週次信用取引残高を検索する

        Args:
            date: 週末日付

        Returns:
            検索結果のリスト
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[WeeklyMarginInterest]:
        """日付範囲で週次信用取引残高を検索する

        Args:
            start_date: 開始日
            end_date: 終了日

        Returns:
            検索結果のリスト
        """
        pass

    @abstractmethod
    async def find_by_issue_type(
        self,
        issue_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WeeklyMarginInterest]:
        """銘柄種別で週次信用取引残高を検索する

        Args:
            issue_type: 銘柄種別（1: 貸借銘柄, 2: 貸借融資銘柄, 3: その他）
            start_date: 開始日（省略可）
            end_date: 終了日（省略可）

        Returns:
            検索結果のリスト
        """
        pass

    @abstractmethod
    async def delete_by_date_range(self, start_date: date, end_date: date) -> int:
        """日付範囲で週次信用取引残高を削除する

        Args:
            start_date: 開始日
            end_date: 終了日

        Returns:
            削除された件数
        """
        pass
