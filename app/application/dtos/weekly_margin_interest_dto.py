"""週次信用取引残高関連の DTO"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.domain.entities import WeeklyMarginInterest


@dataclass
class WeeklyMarginInterestDTO:
    """週次信用取引残高データ転送オブジェクト"""

    code: str
    date: date
    short_margin_trade_volume: Optional[float]
    long_margin_trade_volume: Optional[float]
    short_negotiable_margin_trade_volume: Optional[float]
    long_negotiable_margin_trade_volume: Optional[float]
    short_standardized_margin_trade_volume: Optional[float]
    long_standardized_margin_trade_volume: Optional[float]
    issue_type: Optional[str]

    @classmethod
    def from_entity(cls, entity: WeeklyMarginInterest) -> "WeeklyMarginInterestDTO":
        """エンティティから DTO を生成"""
        return cls(
            code=entity.code,
            date=entity.date,
            short_margin_trade_volume=entity.short_margin_trade_volume,
            long_margin_trade_volume=entity.long_margin_trade_volume,
            short_negotiable_margin_trade_volume=entity.short_negotiable_margin_trade_volume,
            long_negotiable_margin_trade_volume=entity.long_negotiable_margin_trade_volume,
            short_standardized_margin_trade_volume=entity.short_standardized_margin_trade_volume,
            long_standardized_margin_trade_volume=entity.long_standardized_margin_trade_volume,
            issue_type=entity.issue_type,
        )

    def to_entity(self) -> WeeklyMarginInterest:
        """DTO からエンティティを生成"""
        return WeeklyMarginInterest(
            code=self.code,
            date=self.date,
            short_margin_trade_volume=self.short_margin_trade_volume,
            long_margin_trade_volume=self.long_margin_trade_volume,
            short_negotiable_margin_trade_volume=self.short_negotiable_margin_trade_volume,
            long_negotiable_margin_trade_volume=self.long_negotiable_margin_trade_volume,
            short_standardized_margin_trade_volume=self.short_standardized_margin_trade_volume,
            long_standardized_margin_trade_volume=self.long_standardized_margin_trade_volume,
            issue_type=self.issue_type,
        )


@dataclass
class WeeklyMarginInterestListDTO:
    """週次信用取引残高リストデータ転送オブジェクト"""

    items: List[WeeklyMarginInterestDTO]
    total_count: int

    @classmethod
    def from_entities(
        cls, entities: List[WeeklyMarginInterest]
    ) -> "WeeklyMarginInterestListDTO":
        """エンティティリストから DTO を生成"""
        return cls(
            items=[WeeklyMarginInterestDTO.from_entity(entity) for entity in entities],
            total_count=len(entities),
        )


@dataclass
class FetchWeeklyMarginInterestResult:
    """週次信用取引残高取得結果"""

    success: bool
    fetched_count: int
    saved_count: int
    code: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    error_message: Optional[str] = None


@dataclass
class WeeklyMarginInterestSearchParams:
    """週次信用取引残高検索パラメータ"""

    code: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    issue_type: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
