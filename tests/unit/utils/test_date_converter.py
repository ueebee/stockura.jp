"""
DateConverterのテスト
"""

import pytest
from datetime import date, datetime
from app.utils.date_converter import DateConverter


class TestDateConverter:
    """DateConverterクラスのテスト"""
    
    def test_to_date_with_date_object(self):
        """dateオブジェクトをそのまま返すことを確認"""
        input_date = date(2025, 7, 26)
        result = DateConverter.to_date(input_date)
        assert result == input_date
        assert isinstance(result, date)
    
    def test_to_date_with_datetime_object(self):
        """datetimeオブジェクトをdateに変換することを確認"""
        input_datetime = datetime(2025, 7, 26, 10, 30, 45)
        result = DateConverter.to_date(input_datetime)
        assert result == date(2025, 7, 26)
        assert isinstance(result, date)
    
    def test_to_date_with_yyyymmdd_string(self):
        """YYYYMMDD形式の文字列をdateに変換することを確認"""
        result = DateConverter.to_date("20250726")
        assert result == date(2025, 7, 26)
        assert isinstance(result, date)
    
    def test_to_date_with_iso_string(self):
        """YYYY-MM-DD形式の文字列をdateに変換することを確認"""
        result = DateConverter.to_date("2025-07-26")
        assert result == date(2025, 7, 26)
        assert isinstance(result, date)
    
    def test_to_date_with_none(self):
        """Noneの場合はNoneを返すことを確認"""
        result = DateConverter.to_date(None)
        assert result is None
    
    def test_to_date_with_invalid_string_format(self):
        """不正な文字列形式でValueErrorが発生することを確認"""
        with pytest.raises(ValueError, match="Unsupported date string format"):
            DateConverter.to_date("2025/07/26")
        
        with pytest.raises(ValueError, match="Invalid date value in YYYYMMDD format"):
            DateConverter.to_date("20250732")  # 不正な日付
    
    def test_to_date_with_unsupported_type(self):
        """サポートされていない型でValueErrorが発生することを確認"""
        with pytest.raises(ValueError, match="Unsupported date type"):
            DateConverter.to_date(12345)
        
        with pytest.raises(ValueError, match="Unsupported date type"):
            DateConverter.to_date([2025, 7, 26])
    
    def test_to_yyyymmdd_string(self):
        """dateオブジェクトをYYYYMMDD形式に変換することを確認"""
        input_date = date(2025, 7, 26)
        result = DateConverter.to_yyyymmdd_string(input_date)
        assert result == "20250726"
        assert isinstance(result, str)
    
    def test_to_yyyymmdd_string_with_none(self):
        """NoneをNoneとして返すことを確認"""
        result = DateConverter.to_yyyymmdd_string(None)
        assert result is None
    
    def test_to_iso_string(self):
        """dateオブジェクトをYYYY-MM-DD形式に変換することを確認"""
        input_date = date(2025, 7, 26)
        result = DateConverter.to_iso_string(input_date)
        assert result == "2025-07-26"
        assert isinstance(result, str)
    
    def test_to_iso_string_with_none(self):
        """NoneをNoneとして返すことを確認"""
        result = DateConverter.to_iso_string(None)
        assert result is None
    
    def test_date_conversion_roundtrip(self):
        """日付変換の往復テスト"""
        original_date = date(2025, 7, 26)
        
        # date -> YYYYMMDD -> date
        yyyymmdd = DateConverter.to_yyyymmdd_string(original_date)
        converted_back = DateConverter.to_date(yyyymmdd)
        assert converted_back == original_date
        
        # date -> ISO -> date
        iso_string = DateConverter.to_iso_string(original_date)
        converted_back = DateConverter.to_date(iso_string)
        assert converted_back == original_date