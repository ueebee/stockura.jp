"""Listed info event handlers."""
from typing import Dict, List

from app.core.logger import get_logger
from app.domain.events.base import DomainEvent, EventHandler
from app.domain.events.listed_info_events import (
    CompanyNameChangeDetected,
    DelistingDetected,
    ListedInfoBulkChangesDetected,
    ListedInfoFetched,
    ListedInfoStored,
    MarketChangeDetected,
    NewListingDetected,
    SectorChangeDetected,
)

logger = get_logger(__name__)


class ListedInfoEventLogger(EventHandler):
    """上場銘柄情報イベントをログに記録するハンドラー"""
    
    def can_handle(self, event: DomainEvent) -> bool:
        """上場銘柄情報関連のすべてのイベントを処理"""
        return event.event_type.startswith("listed_info.")
    
    async def handle(self, event: DomainEvent) -> None:
        """イベントをログに記録"""
        logger.info(
            f"Listed info event occurred: {event.event_type}",
            extra={
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "event_data": event.to_dict(),
            }
        )


class MarketChangeNotifier(EventHandler):
    """市場変更を通知するハンドラー"""
    
    def can_handle(self, event: DomainEvent) -> bool:
        """市場変更関連のイベントのみ処理"""
        return event.event_type in [
            "listed_info.new_listing_detected",
            "listed_info.delisting_detected",
            "listed_info.market_change_detected",
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """市場変更を通知"""
        if isinstance(event, NewListingDetected):
            await self._notify_new_listing(event)
        elif isinstance(event, DelistingDetected):
            await self._notify_delisting(event)
        elif isinstance(event, MarketChangeDetected):
            await self._notify_market_change(event)
    
    async def _notify_new_listing(self, event: NewListingDetected) -> None:
        """新規上場を通知"""
        logger.info(
            f"New listing detected: {event.code.value} - {event.company_name}",
            extra={
                "code": event.code.value,
                "company_name": event.company_name,
                "listing_date": event.listing_date.isoformat(),
                "market_code": event.market_code,
                "market_name": event.market_name,
            }
        )
        # 実際の通知処理（Slack 、メール等）はここに実装
    
    async def _notify_delisting(self, event: DelistingDetected) -> None:
        """上場廃止を通知"""
        logger.warning(
            f"Delisting detected: {event.code.value} - {event.company_name}",
            extra={
                "code": event.code.value,
                "company_name": event.company_name,
                "delisting_date": event.delisting_date.isoformat(),
                "reason": event.reason,
            }
        )
        # 実際の通知処理はここに実装
    
    async def _notify_market_change(self, event: MarketChangeDetected) -> None:
        """市場変更を通知"""
        logger.info(
            f"Market change detected: {event.code.value} - {event.company_name}",
            extra={
                "code": event.code.value,
                "company_name": event.company_name,
                "old_market": event.old_market_name,
                "new_market": event.new_market_name,
                "change_date": event.change_date.isoformat(),
            }
        )
        # 実際の通知処理はここに実装


class CompanyInfoChangeNotifier(EventHandler):
    """企業情報変更を通知するハンドラー"""
    
    def can_handle(self, event: DomainEvent) -> bool:
        """企業情報変更関連のイベントのみ処理"""
        return event.event_type in [
            "listed_info.company_name_change_detected",
            "listed_info.sector_change_detected",
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """企業情報変更を通知"""
        if isinstance(event, CompanyNameChangeDetected):
            await self._notify_name_change(event)
        elif isinstance(event, SectorChangeDetected):
            await self._notify_sector_change(event)
    
    async def _notify_name_change(self, event: CompanyNameChangeDetected) -> None:
        """会社名変更を通知"""
        logger.info(
            f"Company name change detected: {event.code.value}",
            extra={
                "code": event.code.value,
                "old_name": event.old_name,
                "new_name": event.new_name,
                "change_date": event.change_date.isoformat(),
            }
        )
        # 実際の通知処理はここに実装
    
    async def _notify_sector_change(self, event: SectorChangeDetected) -> None:
        """業種変更を通知"""
        logger.info(
            f"Sector change detected: {event.code.value} - {event.company_name}",
            extra={
                "code": event.code.value,
                "company_name": event.company_name,
                "old_sector_17": event.old_sector_17_code,
                "new_sector_17": event.new_sector_17_code,
                "old_sector_33": event.old_sector_33_code,
                "new_sector_33": event.new_sector_33_code,
                "change_date": event.change_date.isoformat(),
            }
        )
        # 実際の通知処理はここに実装


class BulkChangesReporter(EventHandler):
    """一括変更をレポートするハンドラー"""
    
    def can_handle(self, event: DomainEvent) -> bool:
        """一括変更イベントのみ処理"""
        return event.event_type == "listed_info.bulk_changes_detected"
    
    async def handle(self, event: DomainEvent) -> None:
        """一括変更をレポート"""
        if isinstance(event, ListedInfoBulkChangesDetected):
            await self._generate_changes_report(event)
    
    async def _generate_changes_report(self, event: ListedInfoBulkChangesDetected) -> None:
        """変更レポートを生成"""
        report_data = {
            "change_date": event.change_date.isoformat(),
            "summary": {
                "new_listings": len(event.new_listings),
                "delistings": len(event.delistings),
                "market_changes": len(event.market_changes),
                "name_changes": len(event.name_changes),
                "sector_changes": len(event.sector_changes),
                "total_changes": event.to_dict()["total_changes"],
            },
            "details": {
                "new_listings": event.new_listings[:10],  # 上位 10 件
                "delistings": event.delistings[:10],
                "market_changes": event.market_changes[:10],
                "name_changes": event.name_changes[:10],
                "sector_changes": event.sector_changes[:10],
            }
        }
        
        logger.info(
            f"Bulk changes detected on {event.change_date}",
            extra=report_data
        )
        
        # レポート生成とメール送信等の処理はここに実装


class ListedInfoStatisticsCollector(EventHandler):
    """上場銘柄情報の統計を収集するハンドラー"""
    
    def __init__(self):
        self.statistics: Dict[str, int] = {
            "total_fetched": 0,
            "total_stored": 0,
            "new_listings": 0,
            "delistings": 0,
            "market_changes": 0,
            "name_changes": 0,
            "sector_changes": 0,
        }
    
    def can_handle(self, event: DomainEvent) -> bool:
        """統計対象のイベントを処理"""
        return event.event_type in [
            "listed_info.fetched",
            "listed_info.stored",
            "listed_info.new_listing_detected",
            "listed_info.delisting_detected",
            "listed_info.market_change_detected",
            "listed_info.company_name_change_detected",
            "listed_info.sector_change_detected",
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """統計を更新"""
        if isinstance(event, ListedInfoFetched):
            self.statistics["total_fetched"] += event.count
        elif isinstance(event, ListedInfoStored):
            self.statistics["total_stored"] += event.count
        elif isinstance(event, NewListingDetected):
            self.statistics["new_listings"] += 1
        elif isinstance(event, DelistingDetected):
            self.statistics["delistings"] += 1
        elif isinstance(event, MarketChangeDetected):
            self.statistics["market_changes"] += 1
        elif isinstance(event, CompanyNameChangeDetected):
            self.statistics["name_changes"] += 1
        elif isinstance(event, SectorChangeDetected):
            self.statistics["sector_changes"] += 1
        
        # 定期的に統計をログ出力
        if self.statistics["total_stored"] % 1000 == 0:
            logger.info(
                "Listed info statistics",
                extra={"statistics": self.statistics}
            )