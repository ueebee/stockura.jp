"""週次信用取引残高 SQLAlchemy モデル"""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Index,
    PrimaryKeyConstraint,
    String,
    func,
)

from app.infrastructure.database.connection import Base


class WeeklyMarginInterestModel(Base):
    """週次信用取引残高 SQLAlchemy モデル"""

    __tablename__ = "weekly_margin_interest"
    __table_args__ = (
        PrimaryKeyConstraint("code", "date"),
        Index("idx_weekly_margin_interest_code", "code"),
        Index("idx_weekly_margin_interest_date", "date"),
        Index("idx_weekly_margin_interest_issue_type", "issue_type"),
        Index("idx_weekly_margin_interest_date_issue_type", "date", "issue_type"),
    )

    # 基本情報
    code = Column(String(10), nullable=False)  # 銘柄コード
    date = Column(Date, nullable=False)  # 週末日付

    # 信用取引残高
    short_margin_trade_volume = Column(Float, nullable=True)  # 信用売り残高
    long_margin_trade_volume = Column(Float, nullable=True)  # 信用買い残高

    # 一般信用
    short_negotiable_margin_trade_volume = Column(
        Float, nullable=True
    )  # 一般信用売り残高
    long_negotiable_margin_trade_volume = Column(
        Float, nullable=True
    )  # 一般信用買い残高

    # 制度信用
    short_standardized_margin_trade_volume = Column(
        Float, nullable=True
    )  # 制度信用売り残高
    long_standardized_margin_trade_volume = Column(
        Float, nullable=True
    )  # 制度信用買い残高

    # 銘柄種別
    issue_type = Column(
        String(1), nullable=True
    )  # 1: 貸借銘柄, 2: 貸借融資銘柄, 3: その他

    # タイムスタンプ
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """文字列表現"""
        return f"<WeeklyMarginInterestModel(code='{self.code}', date='{self.date}', issue_type='{self.issue_type}')>"
