"""Listed info database model."""
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Index, PrimaryKeyConstraint, String, func

from app.infrastructure.database.connection import Base


class JQuantsListedInfoModel(Base):
    """J-Quants listed info SQLAlchemy model for J-Quants listed company information."""

    __tablename__ = "jquants_listed_info"
    __table_args__ = (
        PrimaryKeyConstraint("date", "code"),
        Index("idx_jquants_listed_info_code", "code"),
        Index("idx_jquants_listed_info_date", "date"),
    )

    date = Column(Date, nullable=False)
    code = Column(String(10), nullable=False)  # 銘柄コード（最大 10 文字）
    company_name = Column(String(255), nullable=False)
    company_name_english = Column(String(255), nullable=True)
    sector_17_code = Column(String(10), nullable=True)
    sector_17_code_name = Column(String(255), nullable=True)
    sector_33_code = Column(String(10), nullable=True)
    sector_33_code_name = Column(String(255), nullable=True)
    scale_category = Column(String(50), nullable=True)
    market_code = Column(String(10), nullable=True)
    market_code_name = Column(String(50), nullable=True)
    margin_code = Column(String(10), nullable=True)
    margin_code_name = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<JQuantsListedInfoModel(date='{self.date}', code='{self.code}', company_name='{self.company_name}')>"