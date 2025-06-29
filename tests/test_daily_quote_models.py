"""
DailyQuoteモデルのテスト
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models.daily_quote import DailyQuote, DailyQuotesSyncHistory


class TestDailyQuote:
    """DailyQuoteモデルのテスト"""

    def test_create_daily_quote_minimal(self):
        """最小限のデータでDailyQuote作成テスト"""
        quote = DailyQuote(
            code="1234",
            trade_date=date(2024, 12, 26)
        )
        
        assert quote.code == "1234"
        assert quote.trade_date == date(2024, 12, 26)
        assert quote.adjustment_factor == Decimal("1.0")
        assert quote.upper_limit_flag is False
        assert quote.lower_limit_flag is False

    def test_create_daily_quote_full_data(self):
        """全データ項目でDailyQuote作成テスト"""
        quote = DailyQuote(
            code="1234",
            trade_date=date(2024, 12, 26),
            open_price=Decimal("1000.00"),
            high_price=Decimal("1100.00"),
            low_price=Decimal("950.00"),
            close_price=Decimal("1050.00"),
            volume=1000000,
            turnover_value=1050000000,
            adjustment_factor=Decimal("1.2"),
            adjustment_open=Decimal("1200.00"),
            adjustment_high=Decimal("1320.00"),
            adjustment_low=Decimal("1140.00"),
            adjustment_close=Decimal("1260.00"),
            adjustment_volume=833333,
            upper_limit_flag=False,
            lower_limit_flag=False,
            morning_open=Decimal("1000.00"),
            morning_high=Decimal("1080.00"),
            morning_low=Decimal("980.00"),
            morning_close=Decimal("1060.00"),
            morning_volume=500000,
            morning_turnover_value=525000000,
            afternoon_open=Decimal("1060.00"),
            afternoon_high=Decimal("1100.00"),
            afternoon_low=Decimal("950.00"),
            afternoon_close=Decimal("1050.00"),
            afternoon_volume=500000,
            afternoon_turnover_value=525000000
        )
        
        assert quote.code == "1234"
        assert quote.open_price == Decimal("1000.00")
        assert quote.high_price == Decimal("1100.00")
        assert quote.low_price == Decimal("950.00")
        assert quote.close_price == Decimal("1050.00")
        assert quote.volume == 1000000
        assert quote.adjustment_factor == Decimal("1.2")
        assert quote.morning_open == Decimal("1000.00")
        assert quote.afternoon_close == Decimal("1050.00")

    def test_daily_quote_repr(self):
        """DailyQuoteの文字列表現テスト"""
        quote = DailyQuote(
            code="1234",
            trade_date=date(2024, 12, 26),
            close_price=Decimal("1050.00")
        )
        
        repr_str = repr(quote)
        assert "1234" in repr_str
        assert "2024-12-26" in repr_str
        assert "1050.00" in repr_str

    def test_daily_quote_decimal_precision(self):
        """Decimal型の精度テスト"""
        quote = DailyQuote(
            code="1234",
            trade_date=date(2024, 12, 26),
            close_price=Decimal("1050.12"),
            adjustment_factor=Decimal("1.123456")
        )
        
        assert quote.close_price == Decimal("1050.12")
        assert quote.adjustment_factor == Decimal("1.123456")

    def test_daily_quote_limit_flags(self):
        """制限フラグのテスト"""
        # ストップ高
        quote_upper = DailyQuote(
            code="1234",
            trade_date=date(2024, 12, 26),
            upper_limit_flag=True,
            lower_limit_flag=False
        )
        assert quote_upper.upper_limit_flag is True
        assert quote_upper.lower_limit_flag is False

        # ストップ安
        quote_lower = DailyQuote(
            code="5678",
            trade_date=date(2024, 12, 26),
            upper_limit_flag=False,
            lower_limit_flag=True
        )
        assert quote_lower.upper_limit_flag is False
        assert quote_lower.lower_limit_flag is True

    def test_daily_quote_nullable_fields(self):
        """NULL許可フィールドのテスト"""
        quote = DailyQuote(
            code="1234",
            trade_date=date(2024, 12, 26),
            open_price=None,
            high_price=None,
            low_price=None,
            close_price=None,
            volume=None
        )
        
        assert quote.open_price is None
        assert quote.high_price is None
        assert quote.low_price is None
        assert quote.close_price is None
        assert quote.volume is None


class TestDailyQuotesSyncHistory:
    """DailyQuotesSyncHistoryモデルのテスト"""

    def test_create_sync_history_minimal(self):
        """最小限のデータでDailyQuotesSyncHistory作成テスト"""
        history = DailyQuotesSyncHistory(
            sync_date=date(2024, 12, 26),
            sync_type="full",
            status="running",
            started_at=datetime(2024, 12, 26, 9, 0, 0)
        )
        
        assert history.sync_date == date(2024, 12, 26)
        assert history.sync_type == "full"
        assert history.status == "running"
        assert history.started_at == datetime(2024, 12, 26, 9, 0, 0)

    def test_create_sync_history_completed(self):
        """完了した同期履歴のテスト"""
        history = DailyQuotesSyncHistory(
            sync_date=date(2024, 12, 26),
            sync_type="incremental",
            status="completed",
            target_companies=100,
            total_records=5000,
            new_records=4000,
            updated_records=800,
            skipped_records=200,
            started_at=datetime(2024, 12, 26, 9, 0, 0),
            completed_at=datetime(2024, 12, 26, 9, 30, 0),
            from_date=date(2024, 12, 25),
            to_date=date(2024, 12, 26)
        )
        
        assert history.sync_type == "incremental"
        assert history.status == "completed"
        assert history.target_companies == 100
        assert history.total_records == 5000
        assert history.new_records == 4000
        assert history.updated_records == 800
        assert history.skipped_records == 200
        assert history.completed_at == datetime(2024, 12, 26, 9, 30, 0)

    def test_create_sync_history_failed(self):
        """失敗した同期履歴のテスト"""
        history = DailyQuotesSyncHistory(
            sync_date=date(2024, 12, 26),
            sync_type="single_stock",
            status="failed",
            started_at=datetime(2024, 12, 26, 9, 0, 0),
            completed_at=datetime(2024, 12, 26, 9, 5, 0),
            error_message="API authentication failed",
            specific_codes='["1234", "5678"]'
        )
        
        assert history.status == "failed"
        assert history.error_message == "API authentication failed"
        assert history.specific_codes == '["1234", "5678"]'

    def test_sync_history_repr(self):
        """DailyQuotesSyncHistoryの文字列表現テスト"""
        history = DailyQuotesSyncHistory(
            sync_date=date(2024, 12, 26),
            sync_type="full",
            status="completed",
            started_at=datetime(2024, 12, 26, 9, 0, 0)
        )
        
        repr_str = repr(history)
        assert "2024-12-26" in repr_str
        assert "completed" in repr_str

    def test_sync_history_sync_types(self):
        """同期タイプのバリエーションテスト"""
        sync_types = ["full", "incremental", "single_stock"]
        
        for sync_type in sync_types:
            history = DailyQuotesSyncHistory(
                sync_date=date(2024, 12, 26),
                sync_type=sync_type,
                status="completed",
                started_at=datetime(2024, 12, 26, 9, 0, 0)
            )
            assert history.sync_type == sync_type

    def test_sync_history_status_types(self):
        """ステータスタイプのバリエーションテスト"""
        statuses = ["running", "completed", "failed"]
        
        for status in statuses:
            history = DailyQuotesSyncHistory(
                sync_date=date(2024, 12, 26),
                sync_type="full",
                status=status,
                started_at=datetime(2024, 12, 26, 9, 0, 0)
            )
            assert history.status == status

    def test_sync_history_nullable_fields(self):
        """NULL許可フィールドのテスト"""
        history = DailyQuotesSyncHistory(
            sync_date=date(2024, 12, 26),
            sync_type="full",
            status="running",
            started_at=datetime(2024, 12, 26, 9, 0, 0),
            target_companies=None,
            total_records=None,
            new_records=None,
            updated_records=None,
            skipped_records=None,
            completed_at=None,
            error_message=None,
            from_date=None,
            to_date=None,
            specific_codes=None
        )
        
        assert history.target_companies is None
        assert history.total_records is None
        assert history.completed_at is None
        assert history.error_message is None
        assert history.specific_codes is None