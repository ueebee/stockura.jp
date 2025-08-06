"""週次信用取引残高エンティティ"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class WeeklyMarginInterest:
    """週次信用取引残高を表すエンティティ

    J-Quants API から取得する週次の信用取引残高データを表現する。
    """

    # 基本情報
    code: str  # 銘柄コード
    date: date  # 週末日付

    # 信用取引残高
    short_margin_trade_volume: Optional[float] = None  # 信用売り残高
    long_margin_trade_volume: Optional[float] = None  # 信用買い残高

    # 一般信用
    short_negotiable_margin_trade_volume: Optional[float] = None  # 一般信用売り残高
    long_negotiable_margin_trade_volume: Optional[float] = None  # 一般信用買い残高

    # 制度信用
    short_standardized_margin_trade_volume: Optional[float] = None  # 制度信用売り残高
    long_standardized_margin_trade_volume: Optional[float] = None  # 制度信用買い残高

    # 銘柄種別
    issue_type: Optional[str] = None  # 1: 貸借銘柄, 2: 貸借融資銘柄, 3: その他

    def __post_init__(self):
        """エンティティの妥当性を検証"""
        if not self.code:
            raise ValueError("銘柄コードは必須です")

        if not self.date:
            raise ValueError("日付は必須です")

        if self.issue_type and self.issue_type not in ["1", "2", "3"]:
            raise ValueError("銘柄種別は 1, 2, 3 のいずれかである必要があります")
