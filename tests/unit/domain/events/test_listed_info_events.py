"""Tests for listed info domain events."""
import pytest
from datetime import date
from uuid import uuid4

from app.domain.events.listed_info_events import (
    ListedInfoFetched,
    ListedInfoStored,
    NewListingDetected,
    DelistingDetected,
    MarketChangeDetected,
    CompanyNameChangeDetected,
    SectorChangeDetected,
    ListedInfoBulkChangesDetected,
)
from app.domain.value_objects.stock_code import StockCode


class TestListedInfoEvents:
    """Listed info events tests."""
    
    def test_listed_info_fetched_event(self):
        """ListedInfoFetched イベントのテスト"""
        fetch_date = date(2024, 1, 4)
        event = ListedInfoFetched(
            aggregate_id=uuid4(),
            fetch_date=fetch_date,
            count=3500,
            source="J-Quants"
        )
        
        assert event.event_type == "listed_info.fetched"
        assert event.fetch_date == fetch_date
        assert event.count == 3500
        assert event.source == "J-Quants"
        
        event_dict = event.to_dict()
        assert event_dict["fetch_date"] == "2024-01-04"
        assert event_dict["count"] == 3500
    
    def test_listed_info_stored_event(self):
        """ListedInfoStored イベントのテスト"""
        store_date = date(2024, 1, 4)
        event = ListedInfoStored(
            aggregate_id=uuid4(),
            store_date=store_date,
            count=3500,
            new_count=10,
            updated_count=50
        )
        
        assert event.event_type == "listed_info.stored"
        assert event.store_date == store_date
        assert event.count == 3500
        assert event.new_count == 10
        assert event.updated_count == 50
    
    def test_new_listing_detected_event(self):
        """NewListingDetected イベントのテスト"""
        listing_date = date(2024, 1, 4)
        code = StockCode("1234")
        event = NewListingDetected(
            aggregate_id=uuid4(),
            code=code,
            company_name="新規上場株式会社",
            listing_date=listing_date,
            market_code="0113",
            market_name="グロース"
        )
        
        assert event.event_type == "listed_info.new_listing_detected"
        assert event.code == code
        assert event.company_name == "新規上場株式会社"
        assert event.listing_date == listing_date
        assert event.market_code == "0113"
        assert event.market_name == "グロース"
        
        event_dict = event.to_dict()
        assert event_dict["code"] == "1234"
        assert event_dict["listing_date"] == "2024-01-04"
    
    def test_delisting_detected_event(self):
        """DelistingDetected イベントのテスト"""
        delisting_date = date(2024, 1, 4)
        code = StockCode("5678")
        event = DelistingDetected(
            aggregate_id=uuid4(),
            code=code,
            company_name="上場廃止株式会社",
            delisting_date=delisting_date,
            reason="MBO"
        )
        
        assert event.event_type == "listed_info.delisting_detected"
        assert event.code == code
        assert event.company_name == "上場廃止株式会社"
        assert event.delisting_date == delisting_date
        assert event.reason == "MBO"
    
    def test_market_change_detected_event(self):
        """MarketChangeDetected イベントのテスト"""
        change_date = date(2024, 1, 4)
        code = StockCode("7203")
        event = MarketChangeDetected(
            aggregate_id=uuid4(),
            code=code,
            company_name="トヨタ自動車",
            old_market_code="0112",
            new_market_code="0111",
            old_market_name="スタンダード",
            new_market_name="プライム",
            change_date=change_date
        )
        
        assert event.event_type == "listed_info.market_change_detected"
        assert event.code == code
        assert event.company_name == "トヨタ自動車"
        assert event.old_market_code == "0112"
        assert event.new_market_code == "0111"
        assert event.old_market_name == "スタンダード"
        assert event.new_market_name == "プライム"
        assert event.change_date == change_date
    
    def test_company_name_change_detected_event(self):
        """CompanyNameChangeDetected イベントのテスト"""
        change_date = date(2024, 1, 4)
        code = StockCode("9984")
        event = CompanyNameChangeDetected(
            aggregate_id=uuid4(),
            code=code,
            old_name="ソフトバンク",
            new_name="ソフトバンクグループ",
            change_date=change_date
        )
        
        assert event.event_type == "listed_info.company_name_change_detected"
        assert event.code == code
        assert event.old_name == "ソフトバンク"
        assert event.new_name == "ソフトバンクグループ"
        assert event.change_date == change_date
    
    def test_sector_change_detected_event(self):
        """SectorChangeDetected イベントのテスト"""
        change_date = date(2024, 1, 4)
        code = StockCode("4755")
        event = SectorChangeDetected(
            aggregate_id=uuid4(),
            code=code,
            company_name="楽天グループ",
            old_sector_17_code="10",
            new_sector_17_code="11",
            old_sector_33_code="5250",
            new_sector_33_code="7100",
            change_date=change_date
        )
        
        assert event.event_type == "listed_info.sector_change_detected"
        assert event.code == code
        assert event.company_name == "楽天グループ"
        assert event.old_sector_17_code == "10"
        assert event.new_sector_17_code == "11"
        assert event.old_sector_33_code == "5250"
        assert event.new_sector_33_code == "7100"
        assert event.change_date == change_date
    
    def test_listed_info_bulk_changes_detected_event(self):
        """ListedInfoBulkChangesDetected イベントのテスト"""
        change_date = date(2024, 1, 4)
        event = ListedInfoBulkChangesDetected(
            aggregate_id=uuid4(),
            change_date=change_date,
            new_listings=["1234", "5678"],
            delistings=["9999"],
            market_changes=["7203", "9984"],
            name_changes=["4755"],
            sector_changes=["2371", "3990"]
        )
        
        assert event.event_type == "listed_info.bulk_changes_detected"
        assert event.change_date == change_date
        assert event.new_listings == ["1234", "5678"]
        assert event.delistings == ["9999"]
        assert event.market_changes == ["7203", "9984"]
        assert event.name_changes == ["4755"]
        assert event.sector_changes == ["2371", "3990"]
        
        event_dict = event.to_dict()
        assert event_dict["total_changes"] == 8
    
    def test_event_immutability(self):
        """イベントの不変性テスト"""
        event = NewListingDetected(
            aggregate_id=uuid4(),
            code=StockCode("1234"),
            company_name="テスト株式会社",
            listing_date=date(2024, 1, 4)
        )
        
        # frozen=True により属性変更は不可
        with pytest.raises(AttributeError):
            event.company_name = "新しい名前"
        
        with pytest.raises(AttributeError):
            event.listing_date = date(2024, 1, 5)