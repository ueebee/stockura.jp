"""決算発表予定データベースモデル"""

from datetime import date as date_type

from sqlalchemy import Column, Date, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AnnouncementModel(Base):
    """決算発表予定のデータベースモデル"""

    __tablename__ = "announcements"

    # 複合主キー: 発表日 + 銘柄コード + 四半期区分
    date = Column(Date, primary_key=True, nullable=False, comment="発表日")
    code = Column(String(4), primary_key=True, nullable=False, comment="銘柄コード")
    fiscal_quarter = Column(String(50), primary_key=True, nullable=False, comment="四半期区分")
    
    # その他のカラム
    company_name = Column(String(255), nullable=False, comment="会社名")
    fiscal_year = Column(String(10), nullable=False, comment="決算期")
    sector_name = Column(String(100), nullable=False, comment="業種名")
    section = Column(String(50), nullable=False, comment="市場区分")

    # ユニーク制約
    __table_args__ = (
        UniqueConstraint("date", "code", "fiscal_quarter", name="uq_announcement"),
    )

    def to_entity(self) -> "Announcement":
        """データベースモデルからエンティティに変換

        Returns:
            Announcement entity
        """
        from app.domain.entities.announcement import Announcement
        from app.domain.value_objects.stock_code import StockCode

        return Announcement(
            date=self.date,
            code=StockCode(self.code),
            company_name=self.company_name,
            fiscal_year=self.fiscal_year,
            sector_name=self.sector_name,
            fiscal_quarter=self.fiscal_quarter,
            section=self.section,
        )

    @classmethod
    def from_entity(cls, entity: "Announcement") -> "AnnouncementModel":
        """エンティティからデータベースモデルに変換

        Args:
            entity: Announcement entity

        Returns:
            AnnouncementModel instance
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