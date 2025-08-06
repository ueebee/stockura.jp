"""決算発表予定エンティティ"""

from dataclasses import dataclass
from datetime import date

from app.domain.value_objects.stock_code import StockCode


@dataclass(frozen=True)
class Announcement:
    """決算発表予定エンティティ"""

    date: date
    code: StockCode
    company_name: str
    fiscal_year: str
    sector_name: str
    fiscal_quarter: str
    section: str

    def __post_init__(self) -> None:
        """Post initialization validation."""
        if not self.company_name:
            raise ValueError("会社名は必須です")
        if not isinstance(self.date, date):
            raise ValueError("日付は date 型である必要があります")
        if not self.fiscal_year:
            raise ValueError("決算期は必須です")
        if not self.sector_name:
            raise ValueError("業種名は必須です")
        if not self.fiscal_quarter:
            raise ValueError("四半期区分は必須です")
        if not self.section:
            raise ValueError("市場区分は必須です")

    @classmethod
    def from_dict(cls, data: dict) -> "Announcement":
        """辞書から Announcement エンティティを作成

        Args:
            data: J-Quants API のレスポンスデータ

        Returns:
            Announcement instance
        """
        from datetime import datetime

        # 日付の解析
        date_str = data["Date"]
        if len(date_str) == 8:  # YYYYMMDD 形式
            announcement_date = datetime.strptime(date_str, "%Y%m%d").date()
        else:  # YYYY-MM-DD 形式
            announcement_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        return cls(
            date=announcement_date,
            code=StockCode(data["Code"]),
            company_name=data["CompanyName"],
            fiscal_year=data["FiscalYear"],
            sector_name=data["SectorName"],
            fiscal_quarter=data["FiscalQuarter"],
            section=data["Section"],
        )

    def is_same_announcement(self, other: "Announcement") -> bool:
        """同じ発表予定かどうかを判定

        Args:
            other: 比較対象の Announcement

        Returns:
            同じ発表予定の場合 True
        """
        return (
            self.date == other.date
            and self.code == other.code
            and self.fiscal_quarter == other.fiscal_quarter
        )