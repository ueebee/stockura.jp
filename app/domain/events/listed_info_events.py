"""Listed info domain events."""
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

from app.domain.events.base import DomainEvent
from app.domain.value_objects.stock_code import StockCode


@dataclass(frozen=True)
class ListedInfoFetched(DomainEvent):
    """上場銘柄情報取得イベント"""
    
    fetch_date: date
    count: int
    source: str = "J-Quants"
    
    @property
    def event_type(self) -> str:
        return "listed_info.fetched"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "fetch_date": self.fetch_date.isoformat(),
            "count": self.count,
            "source": self.source,
        })
        return base_dict


@dataclass(frozen=True)
class ListedInfoStored(DomainEvent):
    """上場銘柄情報保存イベント"""
    
    store_date: date
    count: int
    new_count: int
    updated_count: int
    
    @property
    def event_type(self) -> str:
        return "listed_info.stored"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "store_date": self.store_date.isoformat(),
            "count": self.count,
            "new_count": self.new_count,
            "updated_count": self.updated_count,
        })
        return base_dict


@dataclass(frozen=True)
class NewListingDetected(DomainEvent):
    """新規上場銘柄検出イベント"""
    
    code: StockCode
    company_name: str
    listing_date: date
    market_code: Optional[str] = None
    market_name: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "listed_info.new_listing_detected"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "code": self.code.value,
            "company_name": self.company_name,
            "listing_date": self.listing_date.isoformat(),
            "market_code": self.market_code,
            "market_name": self.market_name,
        })
        return base_dict


@dataclass(frozen=True)
class DelistingDetected(DomainEvent):
    """上場廃止銘柄検出イベント"""
    
    code: StockCode
    company_name: str
    delisting_date: date
    reason: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "listed_info.delisting_detected"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "code": self.code.value,
            "company_name": self.company_name,
            "delisting_date": self.delisting_date.isoformat(),
            "reason": self.reason,
        })
        return base_dict


@dataclass(frozen=True)
class MarketChangeDetected(DomainEvent):
    """市場変更検出イベント"""
    
    code: StockCode
    company_name: str
    old_market_code: Optional[str]
    new_market_code: Optional[str]
    old_market_name: Optional[str]
    new_market_name: Optional[str]
    change_date: date
    
    @property
    def event_type(self) -> str:
        return "listed_info.market_change_detected"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "code": self.code.value,
            "company_name": self.company_name,
            "old_market_code": self.old_market_code,
            "new_market_code": self.new_market_code,
            "old_market_name": self.old_market_name,
            "new_market_name": self.new_market_name,
            "change_date": self.change_date.isoformat(),
        })
        return base_dict


@dataclass(frozen=True)
class CompanyNameChangeDetected(DomainEvent):
    """会社名変更検出イベント"""
    
    code: StockCode
    old_name: str
    new_name: str
    change_date: date
    
    @property
    def event_type(self) -> str:
        return "listed_info.company_name_change_detected"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "code": self.code.value,
            "old_name": self.old_name,
            "new_name": self.new_name,
            "change_date": self.change_date.isoformat(),
        })
        return base_dict


@dataclass(frozen=True)
class SectorChangeDetected(DomainEvent):
    """業種変更検出イベント"""
    
    code: StockCode
    company_name: str
    old_sector_17_code: Optional[str]
    new_sector_17_code: Optional[str]
    old_sector_33_code: Optional[str]
    new_sector_33_code: Optional[str]
    change_date: date
    
    @property
    def event_type(self) -> str:
        return "listed_info.sector_change_detected"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "code": self.code.value,
            "company_name": self.company_name,
            "old_sector_17_code": self.old_sector_17_code,
            "new_sector_17_code": self.new_sector_17_code,
            "old_sector_33_code": self.old_sector_33_code,
            "new_sector_33_code": self.new_sector_33_code,
            "change_date": self.change_date.isoformat(),
        })
        return base_dict


@dataclass(frozen=True)
class ListedInfoBulkChangesDetected(DomainEvent):
    """上場銘柄情報一括変更検出イベント"""
    
    change_date: date
    new_listings: List[str] = field(default_factory=list)
    delistings: List[str] = field(default_factory=list)
    market_changes: List[str] = field(default_factory=list)
    name_changes: List[str] = field(default_factory=list)
    sector_changes: List[str] = field(default_factory=list)
    
    @property
    def event_type(self) -> str:
        return "listed_info.bulk_changes_detected"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "change_date": self.change_date.isoformat(),
            "new_listings": self.new_listings,
            "delistings": self.delistings,
            "market_changes": self.market_changes,
            "name_changes": self.name_changes,
            "sector_changes": self.sector_changes,
            "total_changes": (
                len(self.new_listings) + 
                len(self.delistings) + 
                len(self.market_changes) + 
                len(self.name_changes) +
                len(self.sector_changes)
            ),
        })
        return base_dict