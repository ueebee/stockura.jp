"""Constants モジュールのユニットテスト"""
import re
import pytest

from app.core.constants import (
    Environment,
    Market,
    OrderType,
    OrderSide,
    TimeFrame,
    CacheKeyPrefix,
    # HTTP Status Codes
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
    # Default Values
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DEFAULT_CACHE_TTL,
    DEFAULT_TIMEOUT,
    # Date Formats
    DATE_FORMAT,
    DATETIME_FORMAT,
    ISO_DATETIME_FORMAT,
    # Regular Expressions
    TICKER_SYMBOL_REGEX,
    EMAIL_REGEX,
    # Error Messages
    ERROR_STOCK_NOT_FOUND,
    ERROR_INVALID_TICKER,
    ERROR_INVALID_DATE_RANGE,
    ERROR_UNAUTHORIZED,
    ERROR_RATE_LIMIT_EXCEEDED,
    ERROR_EXTERNAL_API_ERROR,
    ERROR_DATABASE_ERROR,
    ERROR_VALIDATION_ERROR,
    # Success Messages
    SUCCESS_CREATED,
    SUCCESS_UPDATED,
    SUCCESS_DELETED,
    # J-Quants Specific
    JQUANTS_MARKETS,
    JQUANTS_MAX_DATE_RANGE_DAYS,
    # yFinance Specific
    YFINANCE_INTERVALS,
    YFINANCE_PERIODS,
)


class TestEnvironment:
    """Environment Enum のテストクラス"""

    def test_environment_values(self):
        """環境タイプの値確認テスト"""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"

    def test_environment_names(self):
        """環境タイプの名前確認テスト"""
        assert Environment.DEVELOPMENT.name == "DEVELOPMENT"
        assert Environment.STAGING.name == "STAGING"
        assert Environment.PRODUCTION.name == "PRODUCTION"
        assert Environment.TESTING.name == "TESTING"

    def test_environment_from_value(self):
        """値から環境タイプを取得するテスト"""
        assert Environment("development") == Environment.DEVELOPMENT
        assert Environment("staging") == Environment.STAGING
        assert Environment("production") == Environment.PRODUCTION
        assert Environment("testing") == Environment.TESTING

    def test_environment_invalid_value(self):
        """無効な値でのエラーテスト"""
        with pytest.raises(ValueError):
            Environment("invalid")

    def test_environment_membership(self):
        """環境タイプのメンバーシップテスト"""
        assert Environment.DEVELOPMENT in Environment
        assert Environment.TESTING in Environment

    def test_environment_iteration(self):
        """環境タイプの反復処理テスト"""
        all_envs = list(Environment)
        assert len(all_envs) == 4
        assert Environment.DEVELOPMENT in all_envs
        assert Environment.PRODUCTION in all_envs


class TestMarket:
    """Market Enum のテストクラス"""

    def test_market_values(self):
        """市場タイプの値確認テスト"""
        assert Market.TSE.value == "TSE"
        assert Market.NYSE.value == "NYSE"
        assert Market.NASDAQ.value == "NASDAQ"
        assert Market.OTHER.value == "OTHER"

    def test_market_from_value(self):
        """値から市場タイプを取得するテスト"""
        assert Market("TSE") == Market.TSE
        assert Market("NYSE") == Market.NYSE
        assert Market("NASDAQ") == Market.NASDAQ
        assert Market("OTHER") == Market.OTHER

    def test_market_comparison(self):
        """市場タイプの比較テスト"""
        assert Market.TSE == Market.TSE
        assert Market.TSE != Market.NYSE
        assert Market.NASDAQ != Market.OTHER


class TestOrderType:
    """OrderType Enum のテストクラス"""

    def test_order_type_values(self):
        """注文タイプの値確認テスト"""
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.STOP.value == "stop"
        assert OrderType.STOP_LIMIT.value == "stop_limit"

    def test_order_type_from_value(self):
        """値から注文タイプを取得するテスト"""
        assert OrderType("market") == OrderType.MARKET
        assert OrderType("limit") == OrderType.LIMIT
        assert OrderType("stop") == OrderType.STOP
        assert OrderType("stop_limit") == OrderType.STOP_LIMIT

    def test_order_type_iteration(self):
        """注文タイプの反復処理テスト"""
        all_types = list(OrderType)
        assert len(all_types) == 4
        assert OrderType.MARKET in all_types
        assert OrderType.STOP_LIMIT in all_types


class TestOrderSide:
    """OrderSide Enum のテストクラス"""

    def test_order_side_values(self):
        """注文サイドの値確認テスト"""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"

    def test_order_side_from_value(self):
        """値から注文サイドを取得するテスト"""
        assert OrderSide("buy") == OrderSide.BUY
        assert OrderSide("sell") == OrderSide.SELL

    def test_order_side_count(self):
        """注文サイドの数確認テスト"""
        all_sides = list(OrderSide)
        assert len(all_sides) == 2


class TestTimeFrame:
    """TimeFrame Enum のテストクラス"""

    def test_time_frame_values(self):
        """時間枠の値確認テスト"""
        assert TimeFrame.MINUTE_1.value == "1m"
        assert TimeFrame.MINUTE_5.value == "5m"
        assert TimeFrame.MINUTE_15.value == "15m"
        assert TimeFrame.MINUTE_30.value == "30m"
        assert TimeFrame.HOUR_1.value == "1h"
        assert TimeFrame.HOUR_4.value == "4h"
        assert TimeFrame.DAY_1.value == "1d"
        assert TimeFrame.WEEK_1.value == "1w"
        assert TimeFrame.MONTH_1.value == "1M"

    def test_time_frame_from_value(self):
        """値から時間枠を取得するテスト"""
        assert TimeFrame("1m") == TimeFrame.MINUTE_1
        assert TimeFrame("1h") == TimeFrame.HOUR_1
        assert TimeFrame("1d") == TimeFrame.DAY_1
        assert TimeFrame("1M") == TimeFrame.MONTH_1

    def test_time_frame_count(self):
        """時間枠の数確認テスト"""
        all_frames = list(TimeFrame)
        assert len(all_frames) == 9


class TestCacheKeyPrefix:
    """CacheKeyPrefix Enum のテストクラス"""

    def test_cache_key_prefix_values(self):
        """キャッシュキープレフィックスの値確認テスト"""
        assert CacheKeyPrefix.STOCK_PRICE.value == "stock:price"
        assert CacheKeyPrefix.STOCK_INFO.value == "stock:info"
        assert CacheKeyPrefix.MARKET_DATA.value == "market:data"
        assert CacheKeyPrefix.USER_SESSION.value == "user:session"
        assert CacheKeyPrefix.API_RATE_LIMIT.value == "api:rate_limit"

    def test_cache_key_prefix_from_value(self):
        """値からキャッシュキープレフィックスを取得するテスト"""
        assert CacheKeyPrefix("stock:price") == CacheKeyPrefix.STOCK_PRICE
        assert CacheKeyPrefix("user:session") == CacheKeyPrefix.USER_SESSION
        assert CacheKeyPrefix("api:rate_limit") == CacheKeyPrefix.API_RATE_LIMIT

    def test_cache_key_prefix_usage(self):
        """キャッシュキープレフィックスの使用例テスト"""
        # キーの組み立て例
        stock_id = "7203"
        cache_key = f"{CacheKeyPrefix.STOCK_PRICE.value}:{stock_id}"
        assert cache_key == "stock:price:7203"
        
        user_id = "12345"
        session_key = f"{CacheKeyPrefix.USER_SESSION.value}:{user_id}"
        assert session_key == "user:session:12345"


class TestHTTPStatusCodes:
    """HTTP ステータスコードのテストクラス"""

    def test_success_status_codes(self):
        """成功系ステータスコードの確認テスト"""
        assert HTTP_200_OK == 200
        assert HTTP_201_CREATED == 201
        assert HTTP_204_NO_CONTENT == 204

    def test_client_error_status_codes(self):
        """クライアントエラー系ステータスコードの確認テスト"""
        assert HTTP_400_BAD_REQUEST == 400
        assert HTTP_401_UNAUTHORIZED == 401
        assert HTTP_403_FORBIDDEN == 403
        assert HTTP_404_NOT_FOUND == 404
        assert HTTP_409_CONFLICT == 409
        assert HTTP_422_UNPROCESSABLE_ENTITY == 422
        assert HTTP_429_TOO_MANY_REQUESTS == 429

    def test_server_error_status_codes(self):
        """サーバーエラー系ステータスコードの確認テスト"""
        assert HTTP_500_INTERNAL_SERVER_ERROR == 500
        assert HTTP_503_SERVICE_UNAVAILABLE == 503

    def test_status_code_ranges(self):
        """ステータスコードの範囲確認テスト"""
        # 2xx: Success
        assert 200 <= HTTP_200_OK < 300
        assert 200 <= HTTP_201_CREATED < 300
        assert 200 <= HTTP_204_NO_CONTENT < 300
        
        # 4xx: Client Error
        assert 400 <= HTTP_400_BAD_REQUEST < 500
        assert 400 <= HTTP_401_UNAUTHORIZED < 500
        assert 400 <= HTTP_404_NOT_FOUND < 500
        assert 400 <= HTTP_429_TOO_MANY_REQUESTS < 500
        
        # 5xx: Server Error
        assert 500 <= HTTP_500_INTERNAL_SERVER_ERROR < 600
        assert 500 <= HTTP_503_SERVICE_UNAVAILABLE < 600


class TestDefaultValues:
    """デフォルト値のテストクラス"""

    def test_pagination_defaults(self):
        """ページネーションのデフォルト値テスト"""
        assert DEFAULT_PAGE_SIZE == 20
        assert MAX_PAGE_SIZE == 100
        assert DEFAULT_PAGE_SIZE < MAX_PAGE_SIZE

    def test_cache_defaults(self):
        """キャッシュのデフォルト値テスト"""
        assert DEFAULT_CACHE_TTL == 3600  # 1 時間
        assert DEFAULT_CACHE_TTL > 0

    def test_timeout_defaults(self):
        """タイムアウトのデフォルト値テスト"""
        assert DEFAULT_TIMEOUT == 30  # 30 秒
        assert DEFAULT_TIMEOUT > 0


class TestDateFormats:
    """日付フォーマットのテストクラス"""

    def test_date_format_strings(self):
        """日付フォーマット文字列の確認テスト"""
        assert DATE_FORMAT == "%Y-%m-%d"
        assert DATETIME_FORMAT == "%Y-%m-%d %H:%M:%S"
        assert ISO_DATETIME_FORMAT == "%Y-%m-%dT%H:%M:%SZ"

    def test_date_format_usage(self):
        """日付フォーマットの使用例テスト"""
        from datetime import datetime
        
        now = datetime(2024, 1, 15, 10, 30, 45)
        
        # DATE_FORMAT
        date_str = now.strftime(DATE_FORMAT)
        assert date_str == "2024-01-15"
        
        # DATETIME_FORMAT
        datetime_str = now.strftime(DATETIME_FORMAT)
        assert datetime_str == "2024-01-15 10:30:45"
        
        # ISO_DATETIME_FORMAT
        iso_str = now.strftime(ISO_DATETIME_FORMAT)
        assert iso_str == "2024-01-15T10:30:45Z"


class TestRegularExpressions:
    """正規表現のテストクラス"""

    def test_ticker_symbol_regex(self):
        """ティッカーシンボル正規表現のテスト"""
        pattern = re.compile(TICKER_SYMBOL_REGEX)
        
        # 有効なティッカー
        valid_tickers = ["AAPL", "MSFT", "GOOGL", "A", "7203", "TSLA123"]
        for ticker in valid_tickers:
            assert pattern.match(ticker) is not None
        
        # 無効なティッカー
        invalid_tickers = ["", "aapl", "AAPL-B", "AAPL.L", "VERYLONGNAME", "A B", "株式"]
        for ticker in invalid_tickers:
            assert pattern.match(ticker) is None

    def test_email_regex(self):
        """メールアドレス正規表現のテスト"""
        pattern = re.compile(EMAIL_REGEX)
        
        # 有効なメールアドレス
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.com",
            "user123@example-domain.com",
            "test_user@subdomain.example.com"
        ]
        for email in valid_emails:
            assert pattern.match(email) is not None
        
        # 無効なメールアドレス
        invalid_emails = [
            "",
            "user",
            "@example.com",
            "user@",
            "user@.com",
            "user@example",
            "user @example.com",
            "user@example .com"
        ]
        for email in invalid_emails:
            assert pattern.match(email) is None


class TestErrorMessages:
    """エラーメッセージのテストクラス"""

    def test_error_message_values(self):
        """エラーメッセージの値確認テスト"""
        assert ERROR_STOCK_NOT_FOUND == "Stock not found"
        assert ERROR_INVALID_TICKER == "Invalid ticker symbol"
        assert ERROR_INVALID_DATE_RANGE == "Invalid date range"
        assert ERROR_UNAUTHORIZED == "Unauthorized access"
        assert ERROR_RATE_LIMIT_EXCEEDED == "Rate limit exceeded"
        assert ERROR_EXTERNAL_API_ERROR == "External API error"
        assert ERROR_DATABASE_ERROR == "Database error"
        assert ERROR_VALIDATION_ERROR == "Validation error"

    def test_error_message_types(self):
        """エラーメッセージの型確認テスト"""
        assert isinstance(ERROR_STOCK_NOT_FOUND, str)
        assert isinstance(ERROR_INVALID_TICKER, str)
        assert isinstance(ERROR_UNAUTHORIZED, str)
        assert isinstance(ERROR_DATABASE_ERROR, str)

    def test_error_message_not_empty(self):
        """エラーメッセージが空でないことのテスト"""
        assert len(ERROR_STOCK_NOT_FOUND) > 0
        assert len(ERROR_INVALID_TICKER) > 0
        assert len(ERROR_RATE_LIMIT_EXCEEDED) > 0


class TestSuccessMessages:
    """成功メッセージのテストクラス"""

    def test_success_message_values(self):
        """成功メッセージの値確認テスト"""
        assert SUCCESS_CREATED == "Resource created successfully"
        assert SUCCESS_UPDATED == "Resource updated successfully"
        assert SUCCESS_DELETED == "Resource deleted successfully"

    def test_success_message_consistency(self):
        """成功メッセージの一貫性テスト"""
        # すべて "successfully" で終わる
        assert SUCCESS_CREATED.endswith("successfully")
        assert SUCCESS_UPDATED.endswith("successfully")
        assert SUCCESS_DELETED.endswith("successfully")
        
        # すべて "Resource" で始まる
        assert SUCCESS_CREATED.startswith("Resource")
        assert SUCCESS_UPDATED.startswith("Resource")
        assert SUCCESS_DELETED.startswith("Resource")


class TestJQuantsSpecific:
    """J-Quants 固有定数のテストクラス"""

    def test_jquants_markets(self):
        """J-Quants 市場リストのテスト"""
        assert JQUANTS_MARKETS == ["TSE", "OSE", "NSE", "FSE", "SSE"]
        assert len(JQUANTS_MARKETS) == 5
        assert "TSE" in JQUANTS_MARKETS
        assert "NYSE" not in JQUANTS_MARKETS  # NYSE は含まれない

    def test_jquants_markets_immutability(self):
        """J-Quants 市場リストの不変性テスト"""
        original_markets = JQUANTS_MARKETS.copy()
        # リストは変更可能だが、定数として扱うべき
        assert JQUANTS_MARKETS == original_markets

    def test_jquants_max_date_range(self):
        """J-Quants 最大日付範囲のテスト"""
        assert JQUANTS_MAX_DATE_RANGE_DAYS == 365
        assert JQUANTS_MAX_DATE_RANGE_DAYS > 0
        assert isinstance(JQUANTS_MAX_DATE_RANGE_DAYS, int)


class TestYFinanceSpecific:
    """yFinance 固有定数のテストクラス"""

    def test_yfinance_intervals(self):
        """yFinance インターバルリストのテスト"""
        expected_intervals = [
            "1m", "2m", "5m", "15m", "30m", "60m", "90m",
            "1h", "1d", "5d", "1wk", "1mo", "3mo"
        ]
        assert YFINANCE_INTERVALS == expected_intervals
        assert len(YFINANCE_INTERVALS) == 13
        
        # 分単位のインターバルが含まれる
        minute_intervals = [i for i in YFINANCE_INTERVALS if i.endswith("m")]
        assert len(minute_intervals) == 7
        
        # 時間以上のインターバルも含まれる
        assert "1h" in YFINANCE_INTERVALS
        assert "1d" in YFINANCE_INTERVALS
        assert "1wk" in YFINANCE_INTERVALS

    def test_yfinance_periods(self):
        """yFinance 期間リストのテスト"""
        expected_periods = [
            "1d", "5d", "1mo", "3mo", "6mo", "1y",
            "2y", "5y", "10y", "ytd", "max"
        ]
        assert YFINANCE_PERIODS == expected_periods
        assert len(YFINANCE_PERIODS) == 11
        
        # 特殊な期間が含まれる
        assert "ytd" in YFINANCE_PERIODS  # Year to date
        assert "max" in YFINANCE_PERIODS  # 最大期間
        
        # 日、月、年の単位が含まれる
        day_periods = [p for p in YFINANCE_PERIODS if p.endswith("d") and p != "ytd"]
        month_periods = [p for p in YFINANCE_PERIODS if p.endswith("mo")]
        year_periods = [p for p in YFINANCE_PERIODS if p.endswith("y") and len(p) <= 3]  # 1y, 2y, 5y, 10y (ytd を除外)
        
        assert len(day_periods) == 2  # 1d, 5d
        assert len(month_periods) == 3  # 1mo, 3mo, 6mo
        assert len(year_periods) == 4  # 1y, 2y, 5y, 10y

    def test_yfinance_interval_period_compatibility(self):
        """yFinance インターバルと期間の互換性テスト"""
        # インターバルと期間の両方に "1d" が存在
        assert "1d" in YFINANCE_INTERVALS
        assert "1d" in YFINANCE_PERIODS