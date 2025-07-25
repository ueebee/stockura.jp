"""
DailyQuotesDataMapperの単体テスト
"""

import pytest
from decimal import Decimal
from datetime import datetime

from app.services.daily_quotes.daily_quotes_data_mapper import DailyQuotesDataMapper


class TestDailyQuotesDataMapper:
    """DailyQuotesDataMapperのテストクラス"""
    
    @pytest.fixture
    def mapper(self):
        """マッパーインスタンスを作成"""
        return DailyQuotesDataMapper()
    
    @pytest.fixture
    def valid_quote_data(self):
        """有効な株価データサンプル"""
        return {
            "Code": "1234",
            "Date": "2024-01-15",
            "Open": "1000.0",
            "High": "1050.0",
            "Low": "990.0",
            "Close": "1030.0",
            "Volume": "100000",
            "TurnoverValue": "103000000",
            "AdjustmentFactor": "1.0",
            "AdjustmentOpen": "1000.0",
            "AdjustmentHigh": "1050.0",
            "AdjustmentLow": "990.0",
            "AdjustmentClose": "1030.0",
            "AdjustmentVolume": "100000",
            "UpperLimit": False,
            "LowerLimit": False
        }
    
    def test_map_to_model_valid_data(self, mapper, valid_quote_data):
        """正常なデータのマッピングテスト"""
        result = mapper.map_to_model(valid_quote_data)
        
        assert result is not None
        assert result["code"] == "1234"
        assert result["trade_date"] == datetime(2024, 1, 15).date()
        assert result["open_price"] == Decimal("1000.0")
        assert result["high_price"] == Decimal("1050.0")
        assert result["low_price"] == Decimal("990.0")
        assert result["close_price"] == Decimal("1030.0")
        assert result["volume"] == 100000
        assert result["turnover_value"] == 103000000
        assert result["adjustment_factor"] == Decimal("1.0")
        assert result["upper_limit_flag"] is False
        assert result["lower_limit_flag"] is False
    
    def test_map_to_model_missing_required_fields(self, mapper):
        """必須フィールドが欠けている場合のテスト"""
        # Codeが欠けている
        data = {"Date": "2024-01-15"}
        result = mapper.map_to_model(data)
        assert result is None
        
        # Dateが欠けている
        data = {"Code": "1234"}
        result = mapper.map_to_model(data)
        assert result is None
    
    def test_map_to_model_with_none_values(self, mapper):
        """Noneや空文字列を含むデータのマッピングテスト"""
        data = {
            "Code": "1234",
            "Date": "2024-01-15",
            "Open": None,
            "High": "",
            "Low": "990.0",
            "Close": "1030.0",
            "Volume": None,
            "TurnoverValue": ""
        }
        
        result = mapper.map_to_model(data)
        assert result is not None
        assert result["open_price"] is None
        assert result["high_price"] is None
        assert result["volume"] is None
        assert result["turnover_value"] is None
    
    def test_validate_quote_data_valid(self, mapper, valid_quote_data):
        """正常なデータの検証テスト"""
        is_valid, error_msg = mapper.validate_quote_data(valid_quote_data)
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_quote_data_invalid_date_format(self, mapper):
        """不正な日付フォーマットの検証テスト"""
        data = {
            "Code": "1234",
            "Date": "2024/01/15"  # 不正なフォーマット
        }
        
        is_valid, error_msg = mapper.validate_quote_data(data)
        assert is_valid is False
        assert "Invalid date format" in error_msg
    
    def test_validate_quote_data_invalid_ohlc_relationship(self, mapper):
        """OHLCの論理的整合性チェックテスト"""
        # High < Low の場合
        data = {
            "Code": "1234",
            "Date": "2024-01-15",
            "Open": "1000.0",
            "High": "990.0",  # Low より小さい
            "Low": "1010.0",
            "Close": "1030.0"
        }
        
        is_valid, error_msg = mapper.validate_quote_data(data)
        assert is_valid is False
        assert "Invalid OHLC relationship" in error_msg
    
    def test_validate_quote_data_negative_prices(self, mapper):
        """負の価格データの検証テスト"""
        data = {
            "Code": "1234",
            "Date": "2024-01-15",
            "Open": "-1000.0",
            "High": "1050.0",
            "Low": "990.0",
            "Close": "1030.0"
        }
        
        is_valid, error_msg = mapper.validate_quote_data(data)
        assert is_valid is False
        assert "Negative price values detected" in error_msg
    
    def test_convert_price_fields(self, mapper):
        """価格フィールド変換テスト"""
        # 正常な値
        assert mapper.convert_price_fields("1234.56") == Decimal("1234.56")
        assert mapper.convert_price_fields(1234.56) == Decimal("1234.56")
        assert mapper.convert_price_fields("0") == Decimal("0")
        
        # None、空文字列
        assert mapper.convert_price_fields(None) is None
        assert mapper.convert_price_fields("") is None
        
        # 負の値
        assert mapper.convert_price_fields("-100") is None
        
        # 変換できない値
        assert mapper.convert_price_fields("abc") is None
        assert mapper.convert_price_fields("1,234.56") is None
    
    def test_convert_volume_fields(self, mapper):
        """出来高フィールド変換テスト"""
        # 正常な値
        assert mapper.convert_volume_fields("1000") == 1000
        assert mapper.convert_volume_fields(1000) == 1000
        assert mapper.convert_volume_fields("1000.0") == 1000
        assert mapper.convert_volume_fields(1000.5) == 1000
        
        # None、空文字列
        assert mapper.convert_volume_fields(None) is None
        assert mapper.convert_volume_fields("") is None
        
        # 負の値
        assert mapper.convert_volume_fields("-100") is None
        
        # 変換できない値
        assert mapper.convert_volume_fields("abc") is None
    
    def test_convert_bool(self, mapper):
        """ブール値変換テスト"""
        # True になるケース
        assert mapper._convert_bool(True) is True
        assert mapper._convert_bool(1) is True
        assert mapper._convert_bool("true") is True
        assert mapper._convert_bool("True") is True
        assert mapper._convert_bool("1") is True
        assert mapper._convert_bool("yes") is True
        assert mapper._convert_bool("t") is True
        assert mapper._convert_bool("y") is True
        
        # False になるケース
        assert mapper._convert_bool(False) is False
        assert mapper._convert_bool(0) is False
        assert mapper._convert_bool("false") is False
        assert mapper._convert_bool("0") is False
        assert mapper._convert_bool("no") is False
        assert mapper._convert_bool(None) is False
        assert mapper._convert_bool("") is False
        assert mapper._convert_bool("random") is False
    
    def test_map_to_model_with_premium_data(self, mapper):
        """Premium限定データを含むマッピングテスト"""
        data = {
            "Code": "1234",
            "Date": "2024-01-15",
            "Open": "1000.0",
            "High": "1050.0",
            "Low": "990.0",
            "Close": "1030.0",
            "MorningOpen": "1000.0",
            "MorningHigh": "1020.0",
            "MorningLow": "990.0",
            "MorningClose": "1010.0",
            "MorningVolume": "50000",
            "MorningTurnoverValue": "50500000",
            "AfternoonOpen": "1010.0",
            "AfternoonHigh": "1050.0",
            "AfternoonLow": "1005.0",
            "AfternoonClose": "1030.0",
            "AfternoonVolume": "50000",
            "AfternoonTurnoverValue": "52500000"
        }
        
        result = mapper.map_to_model(data)
        
        assert result is not None
        # 前場データ
        assert result["morning_open"] == Decimal("1000.0")
        assert result["morning_high"] == Decimal("1020.0")
        assert result["morning_low"] == Decimal("990.0")
        assert result["morning_close"] == Decimal("1010.0")
        assert result["morning_volume"] == 50000
        assert result["morning_turnover_value"] == 50500000
        
        # 後場データ
        assert result["afternoon_open"] == Decimal("1010.0")
        assert result["afternoon_high"] == Decimal("1050.0")
        assert result["afternoon_low"] == Decimal("1005.0")
        assert result["afternoon_close"] == Decimal("1030.0")
        assert result["afternoon_volume"] == 50000
        assert result["afternoon_turnover_value"] == 52500000