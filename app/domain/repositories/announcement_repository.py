"""決算発表予定リポジトリインターフェース"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.domain.entities.announcement import Announcement


class AnnouncementRepository(ABC):
    """決算発表予定リポジトリのインターフェース"""

    @abstractmethod
    async def save(self, announcement: Announcement) -> None:
        """決算発表予定を保存

        Args:
            announcement: 保存する決算発表予定エンティティ
        """
        pass

    @abstractmethod
    async def save_bulk(self, announcements: List[Announcement]) -> None:
        """決算発表予定を一括保存

        Args:
            announcements: 保存する決算発表予定エンティティのリスト
        """
        pass

    @abstractmethod
    async def find_by_date(self, announcement_date: date) -> List[Announcement]:
        """発表日で決算発表予定を検索

        Args:
            announcement_date: 発表日

        Returns:
            決算発表予定エンティティのリスト
        """
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> List[Announcement]:
        """銘柄コードで決算発表予定を検索

        Args:
            code: 銘柄コード

        Returns:
            決算発表予定エンティティのリスト
        """
        pass

    @abstractmethod
    async def find_by_date_and_code(
        self, announcement_date: date, code: str
    ) -> Optional[Announcement]:
        """発表日と銘柄コードで決算発表予定を検索

        Args:
            announcement_date: 発表日
            code: 銘柄コード

        Returns:
            決算発表予定エンティティ（存在しない場合は None）
        """
        pass

    @abstractmethod
    async def find_latest(self) -> List[Announcement]:
        """最新の決算発表予定を取得

        Returns:
            最新の決算発表予定エンティティのリスト
        """
        pass

    @abstractmethod
    async def delete_by_date(self, announcement_date: date) -> int:
        """発表日で決算発表予定を削除

        Args:
            announcement_date: 発表日

        Returns:
            削除件数
        """
        pass