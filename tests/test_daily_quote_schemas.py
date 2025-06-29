"""
DailyQuoteスキーマのテスト
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.daily_quote import (
    DailyQuoteBase,
    DailyQuoteCreate,
    DailyQuoteUpdate,
    DailyQuote,
    DailyQuoteList,
    PaginationInfo,
    DailyQuoteSearchRequest,
    DailyQuotesSyncRequest,
    DailyQuotesSyncHistoryBase,
    DailyQuotesSyncHistory,
    DailyQuotesByCodeRequest,
    DailyQuotesByDateRequest,
    DailyQuoteSyncResponse,
    DailyQuoteSyncStatusResponse
)


class TestDailyQuoteBase:
    """DailyQuoteBaseスキーマのテスト"""

    def test_create_daily_quote_base_minimal(self):
        """最小限のデータでDailyQuoteBase作成テスト"""
        quote_data = {
            "code": "1234",
            "trade_date": "2024-12-26"
        }
        
        quote = DailyQuoteBase(**quote_data)
        
        assert quote.code == "1234"
        assert quote.trade_date == date(2024, 12, 26)
        assert quote.open_price is None
        assert quote.close_price is None
        assert quote.upper_limit_flag is False
        assert quote.lower_limit_flag is False

    def test_create_daily_quote_base_full(self):
        """全データでDailyQuoteBase作成テスト"""
        quote_data = {
            "code": "1234",
            "trade_date": "2024-12-26",
            "open_price": "1000.50",
            "high_price": "1100.00",
            "low_price": "950.25",
            "close_price": "1050.75",
            "volume": 1000000,
            "turnover_value": 1050000000,
            "adjustment_factor": "1.2",
            "adjustment_open": "1200.60",
            "adjustment_high": "1320.00",
            "adjustment_low": "1140.30",
            "adjustment_close": "1260.90",
            "adjustment_volume": 833333,
            "upper_limit_flag": True,
            "lower_limit_flag": False
        }
        
        quote = DailyQuoteBase(**quote_data)
        
        assert quote.code == "1234"
        assert quote.trade_date == date(2024, 12, 26)
        assert quote.open_price == Decimal("1000.50")
        assert quote.high_price == Decimal("1100.00")
        assert quote.low_price == Decimal("950.25")
        assert quote.close_price == Decimal("1050.75")
        assert quote.volume == 1000000
        assert quote.adjustment_factor == Decimal("1.2")
        assert quote.upper_limit_flag is True
        assert quote.lower_limit_flag is False

    def test_daily_quote_base_validation_errors(self):
        """DailyQuoteBaseのバリデーションエラーテスト"""
        # 必須フィールド不足
        with pytest.raises(ValidationError):
            DailyQuoteBase(code="1234")  # trade_date なし
        
        with pytest.raises(ValidationError):
            DailyQuoteBase(trade_date="2024-12-26")  # code なし
        
        # 無効な日付形式
        with pytest.raises(ValidationError):
            DailyQuoteBase(code="1234", trade_date="invalid-date")


class TestDailyQuoteCreate:
    """DailyQuoteCreateスキーマのテスト"""

    def test_create_daily_quote_create(self):
        """DailyQuoteCreate作成テスト"""
        quote_data = {
            "code": "1234",
            "trade_date": "2024-12-26",
            "close_price": "1050.00"
        }
        
        quote = DailyQuoteCreate(**quote_data)
        
        assert quote.code == "1234"
        assert quote.close_price == Decimal("1050.00")


class TestDailyQuoteUpdate:
    """DailyQuoteUpdateスキーマのテスト"""

    def test_create_daily_quote_update(self):
        """DailyQuoteUpdate作成テスト"""
        update_data = {
            "close_price": "1100.00",
            "volume": 1500000,
            "upper_limit_flag": True
        }
        
        quote_update = DailyQuoteUpdate(**update_data)
        
        assert quote_update.close_price == Decimal("1100.00")
        assert quote_update.volume == 1500000
        assert quote_update.upper_limit_flag is True
        assert quote_update.open_price is None  # 未指定

    def test_daily_quote_update_all_none(self):
        """全フィールドNoneのDailyQuoteUpdateテスト"""
        quote_update = DailyQuoteUpdate()
        
        assert quote_update.open_price is None
        assert quote_update.close_price is None
        assert quote_update.volume is None
        assert quote_update.upper_limit_flag is None


class TestDailyQuote:
    """DailyQuoteスキーマのテスト"""

    def test_create_daily_quote_response(self):
        """DailyQuoteレスポンススキーマ作成テスト"""
        quote_data = {
            "id": 1,
            "code": "1234",
            "trade_date": "2024-12-26",
            "open_price": "1000.00",
            "close_price": "1050.00",
            "volume": 1000000,
            "created_at": "2024-12-26T10:00:00",
            "updated_at": "2024-12-26T10:00:00"
        }
        
        quote = DailyQuote(**quote_data)
        
        assert quote.id == 1
        assert quote.code == "1234"
        assert quote.created_at == datetime(2024, 12, 26, 10, 0, 0)
        assert quote.updated_at == datetime(2024, 12, 26, 10, 0, 0)

    def test_daily_quote_with_premium_data(self):
        """Premium限定データ付きDailyQuoteテスト"""
        quote_data = {
            "id": 1,
            "code": "1234",
            "trade_date": "2024-12-26",
            "close_price": "1050.00",
            "created_at": "2024-12-26T10:00:00",
            "updated_at": "2024-12-26T10:00:00",
            "morning_open": "1000.00",
            "morning_close": "1030.00",
            "afternoon_open": "1030.00",
            "afternoon_close": "1050.00"
        }
        
        quote = DailyQuote(**quote_data)
        
        assert quote.morning_open == Decimal("1000.00")
        assert quote.morning_close == Decimal("1030.00")
        assert quote.afternoon_open == Decimal("1030.00")
        assert quote.afternoon_close == Decimal("1050.00")


class TestPaginationInfo:
    """PaginationInfoスキーマのテスト"""

    def test_create_pagination_info(self):
        """PaginationInfo作成テスト"""
        pagination_data = {
            "total": 1000,
            "limit": 50,
            "offset": 100,
            "has_next": True
        }
        
        pagination = PaginationInfo(**pagination_data)
        
        assert pagination.total == 1000
        assert pagination.limit == 50
        assert pagination.offset == 100
        assert pagination.has_next is True

    def test_pagination_info_no_next(self):
        """次ページなしのPaginationInfoテスト"""
        pagination_data = {
            "total": 50,
            "limit": 50,
            "offset": 0,
            "has_next": False
        }
        
        pagination = PaginationInfo(**pagination_data)
        
        assert pagination.has_next is False


class TestDailyQuoteList:
    """DailyQuoteListスキーマのテスト"""

    def test_create_daily_quote_list(self):
        """DailyQuoteList作成テスト"""
        quote_data = {
            "id": 1,
            "code": "1234",
            "trade_date": "2024-12-26",
            "close_price": "1050.00",
            "created_at": "2024-12-26T10:00:00",
            "updated_at": "2024-12-26T10:00:00"
        }
        
        list_data = {
            "data": [quote_data],
            "pagination": {
                "total": 1,
                "limit": 50,
                "offset": 0,
                "has_next": False
            }
        }
        
        quote_list = DailyQuoteList(**list_data)
        
        assert len(quote_list.data) == 1
        assert quote_list.data[0].code == "1234"
        assert quote_list.pagination.total == 1


class TestDailyQuoteSearchRequest:
    """DailyQuoteSearchRequestスキーマのテスト"""

    def test_create_search_request_minimal(self):
        """最小限のSearchRequest作成テスト"""
        request = DailyQuoteSearchRequest()
        
        assert request.codes is None
        assert request.date is None
        assert request.limit == 100
        assert request.offset == 0

    def test_create_search_request_full(self):
        """全パラメータ付きSearchRequest作成テスト"""
        request_data = {
            "codes": ["1234", "5678"],
            "date": "2024-12-26",
            "from_date": "2024-12-01",
            "to_date": "2024-12-26",
            "market_code": "0111",
            "sector17_code": "01",
            "limit": 50,
            "offset": 25
        }
        
        request = DailyQuoteSearchRequest(**request_data)
        
        assert request.codes == ["1234", "5678"]
        assert request.date == date(2024, 12, 26)
        assert request.from_date == date(2024, 12, 1)
        assert request.to_date == date(2024, 12, 26)
        assert request.market_code == "0111"
        assert request.sector17_code == "01"
        assert request.limit == 50
        assert request.offset == 25

    def test_search_request_validation(self):
        """SearchRequestのバリデーションテスト"""
        # 無効なlimit値
        with pytest.raises(ValidationError):
            DailyQuoteSearchRequest(limit=0)
        
        with pytest.raises(ValidationError):
            DailyQuoteSearchRequest(limit=1001)
        
        # 無効なoffset値
        with pytest.raises(ValidationError):
            DailyQuoteSearchRequest(offset=-1)


class TestDailyQuotesSyncRequest:
    """DailyQuotesSyncRequestスキーマのテスト"""

    def test_create_sync_request_incremental(self):
        """増分同期リクエスト作成テスト"""
        request_data = {
            "data_source_id": 1,
            "sync_type": "incremental",
            "target_date": "2024-12-26"
        }
        
        request = DailyQuotesSyncRequest(**request_data)
        
        assert request.data_source_id == 1
        assert request.sync_type == "incremental"
        assert request.target_date == date(2024, 12, 26)

    def test_create_sync_request_full(self):
        """全データ同期リクエスト作成テスト"""
        request_data = {
            "data_source_id": 1,
            "sync_type": "full",
            "from_date": "2024-12-01",
            "to_date": "2024-12-26"
        }
        
        request = DailyQuotesSyncRequest(**request_data)
        
        assert request.sync_type == "full"
        assert request.from_date == date(2024, 12, 1)
        assert request.to_date == date(2024, 12, 26)

    def test_create_sync_request_single_stock(self):
        """特定銘柄同期リクエスト作成テスト"""
        request_data = {
            "data_source_id": 1,
            "sync_type": "single_stock",
            "codes": ["1234", "5678"],
            "target_date": "2024-12-26"
        }
        
        request = DailyQuotesSyncRequest(**request_data)
        
        assert request.sync_type == "single_stock"
        assert request.codes == ["1234", "5678"]


class TestDailyQuotesSyncHistory:
    """DailyQuotesSyncHistoryスキーマのテスト"""

    def test_create_sync_history_base(self):
        """DailyQuotesSyncHistoryBase作成テスト"""
        history_data = {
            "sync_date": "2024-12-26",
            "sync_type": "full",
            "status": "completed",
            "target_companies": 100,
            "total_records": 5000,
            "new_records": 4000,
            "updated_records": 800,
            "skipped_records": 200,
            "started_at": "2024-12-26T09:00:00",
            "completed_at": "2024-12-26T09:30:00"
        }
        
        history = DailyQuotesSyncHistoryBase(**history_data)
        
        assert history.sync_date == date(2024, 12, 26)
        assert history.sync_type == "full"
        assert history.status == "completed"
        assert history.target_companies == 100
        assert history.total_records == 5000
        assert history.started_at == datetime(2024, 12, 26, 9, 0, 0)
        assert history.completed_at == datetime(2024, 12, 26, 9, 30, 0)

    def test_create_sync_history_response(self):
        """DailyQuotesSyncHistoryレスポンス作成テスト"""
        history_data = {
            "id": 1,
            "sync_date": "2024-12-26",
            "sync_type": "incremental",
            "status": "running",
            "started_at": "2024-12-26T10:00:00"
        }
        
        history = DailyQuotesSyncHistory(**history_data)
        
        assert history.id == 1
        assert history.sync_type == "incremental"
        assert history.status == "running"


class TestRequestSchemas:
    """リクエストスキーマのテスト"""

    def test_daily_quotes_by_code_request(self):
        """DailyQuotesByCodeRequest作成テスト"""
        request_data = {
            "from_date": "2024-12-01",
            "to_date": "2024-12-26",
            "limit": 200,
            "offset": 50
        }
        
        request = DailyQuotesByCodeRequest(**request_data)
        
        assert request.from_date == date(2024, 12, 1)
        assert request.to_date == date(2024, 12, 26)
        assert request.limit == 200
        assert request.offset == 50

    def test_daily_quotes_by_date_request(self):
        """DailyQuotesByDateRequest作成テスト"""
        request_data = {
            "limit": 5000,
            "offset": 1000
        }
        
        request = DailyQuotesByDateRequest(**request_data)
        
        assert request.limit == 5000
        assert request.offset == 1000

    def test_by_date_request_validation(self):
        """DailyQuotesByDateRequestバリデーションテスト"""
        # limit上限チェック
        with pytest.raises(ValidationError):
            DailyQuotesByDateRequest(limit=10001)


class TestResponseSchemas:
    """レスポンススキーマのテスト"""

    def test_daily_quote_sync_response(self):
        """DailyQuoteSyncResponse作成テスト"""
        response_data = {
            "sync_id": 123,
            "message": "同期を開始しました",
            "status": "queued"
        }
        
        response = DailyQuoteSyncResponse(**response_data)
        
        assert response.sync_id == 123
        assert response.message == "同期を開始しました"
        assert response.status == "queued"

    def test_daily_quote_sync_status_response(self):
        """DailyQuoteSyncStatusResponse作成テスト"""
        sync_history_data = {
            "id": 1,
            "sync_date": "2024-12-26",
            "sync_type": "full",
            "status": "completed",
            "started_at": "2024-12-26T09:00:00"
        }
        
        response_data = {
            "sync_history": sync_history_data,
            "is_running": False,
            "progress_percentage": 100.0,
            "estimated_completion": "2024-12-26T09:30:00"
        }
        
        response = DailyQuoteSyncStatusResponse(**response_data)
        
        assert response.is_running is False
        assert response.progress_percentage == 100.0
        assert response.estimated_completion == datetime(2024, 12, 26, 9, 30, 0)
        assert response.sync_history.id == 1


class TestSchemaEdgeCases:
    """スキーマのエッジケーステスト"""

    def test_decimal_precision_handling(self):
        """Decimal精度処理テスト"""
        quote_data = {
            "code": "1234",
            "trade_date": "2024-12-26",
            "close_price": "1050.123456789",  # 高精度
            "adjustment_factor": "1.123456"
        }
        
        quote = DailyQuoteBase(**quote_data)
        
        assert quote.close_price == Decimal("1050.123456789")
        assert quote.adjustment_factor == Decimal("1.123456")

    def test_large_numbers(self):
        """大きな数値のテスト"""
        quote_data = {
            "code": "1234",
            "trade_date": "2024-12-26",
            "volume": 999999999999,  # 大きな出来高
            "turnover_value": 9999999999999999  # 大きな取引代金
        }
        
        quote = DailyQuoteBase(**quote_data)
        
        assert quote.volume == 999999999999
        assert quote.turnover_value == 9999999999999999

    def test_optional_fields_with_none(self):
        """オプションフィールドのNone値テスト"""
        quote_data = {
            "code": "1234",
            "trade_date": "2024-12-26",
            "open_price": None,
            "high_price": None,
            "low_price": None,
            "close_price": None
        }
        
        quote = DailyQuoteBase(**quote_data)
        
        assert quote.open_price is None
        assert quote.high_price is None
        assert quote.low_price is None
        assert quote.close_price is None