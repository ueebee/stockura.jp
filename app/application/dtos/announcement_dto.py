"""決算発表予定 DTO"""

from dataclasses import dataclass
from datetime import date
from typing import List

from app.domain.entities.announcement import Announcement


@dataclass
class AnnouncementDTO:
    """決算発表予定 DTO"""

    date: date
    code: str
    company_name: str
    fiscal_year: str
    sector_name: str
    fiscal_quarter: str
    section: str

    @classmethod
    def from_entity(cls, entity: Announcement) -> "AnnouncementDTO":
        """エンティティから DTO を作成

        Args:
            entity: Announcement エンティティ

        Returns:
            AnnouncementDTO instance
        """
        return cls(
            date=entity.date,
            code=entity.code.value,
            company_name=entity.company_name,
            fiscal_year=entity.fiscal_year,
            sector_name=entity.sector_name,
            fiscal_quarter=entity.fiscal_quarter,
            section=entity.section,
        )

    @classmethod
    def from_entities(cls, entities: List[Announcement]) -> List["AnnouncementDTO"]:
        """エンティティリストから DTO リストを作成

        Args:
            entities: Announcement エンティティのリスト

        Returns:
            AnnouncementDTO のリスト
        """
        return [cls.from_entity(entity) for entity in entities]

    def to_dict(self) -> dict:
        """DTO を辞書に変換

        Returns:
            辞書形式のデータ
        """
        return {
            "date": self.date.isoformat(),
            "code": self.code,
            "company_name": self.company_name,
            "fiscal_year": self.fiscal_year,
            "sector_name": self.sector_name,
            "fiscal_quarter": self.fiscal_quarter,
            "section": self.section,
        }


@dataclass
class AnnouncementListDTO:
    """決算発表予定リスト DTO"""

    announcements: List[AnnouncementDTO]
    total_count: int

    def to_dict(self) -> dict:
        """DTO を辞書に変換

        Returns:
            辞書形式のデータ
        """
        return {
            "announcements": [announcement.to_dict() for announcement in self.announcements],
            "total_count": self.total_count,
        }