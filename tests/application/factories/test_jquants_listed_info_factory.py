"""Tests for ListedInfoFactory."""
import pytest
from datetime import date

from app.domain.factories.jquants_listed_info_factory import ListedInfoFactory
from app.domain.entities.jquants_listed_info import JQuantsListedInfo
from app.domain.value_objects.stock_code import StockCode


class TestListedInfoFactory:
    """ListedInfoFactory tests."""

    def test_from_jquants_response_yyyymmdd_format(self):
        """from_jquants_response メソッドで YYYYMMDD 形式の日付が解析できることを確認"""
        data = {
            "Date": "20240104",
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
            "CompanyNameEnglish": "TOYOTA MOTOR CORPORATION",
            "Sector17Code": "6",
            "Sector17CodeName": "自動車・輸送機",
            "Sector33Code": "3700",
            "Sector33CodeName": "輸送用機器",
            "ScaleCategory": "TOPIX Large70",
            "MarketCode": "0111",
            "MarketCodeName": "プライム",
            "MarginCode": "1",
            "MarginCodeName": "信用",
        }

        listed_info = ListedInfoFactory.from_jquants_response(data)

        assert listed_info.date == date(2024, 1, 4)
        assert listed_info.code.value == "7203"
        assert listed_info.company_name == "トヨタ自動車"
        assert listed_info.company_name_english == "TOYOTA MOTOR CORPORATION"
        assert listed_info.sector_17_code == "6"
        assert listed_info.sector_17_code_name == "自動車・輸送機"
        assert listed_info.sector_33_code == "3700"
        assert listed_info.sector_33_code_name == "輸送用機器"
        assert listed_info.scale_category == "TOPIX Large70"
        assert listed_info.market_code == "0111"
        assert listed_info.market_code_name == "プライム"
        assert listed_info.margin_code == "1"
        assert listed_info.margin_code_name == "信用"

    def test_from_jquants_response_yyyy_mm_dd_format(self):
        """from_jquants_response メソッドで YYYY-MM-DD 形式の日付が解析できることを確認"""
        data = {
            "Date": "2024-01-04",
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
        }

        listed_info = ListedInfoFactory.from_jquants_response(data)

        assert listed_info.date == date(2024, 1, 4)
        assert listed_info.code.value == "7203"
        assert listed_info.company_name == "トヨタ自動車"

    def test_from_jquants_response_with_optional_fields(self):
        """from_jquants_response メソッドでオプショナルフィールドが正しく処理されることを確認"""
        data = {
            "Date": "20240104",
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
            # オプショナルフィールドは含まない
        }

        listed_info = ListedInfoFactory.from_jquants_response(data)

        assert listed_info.date == date(2024, 1, 4)
        assert listed_info.code.value == "7203"
        assert listed_info.company_name == "トヨタ自動車"
        assert listed_info.company_name_english is None
        assert listed_info.sector_17_code is None
        assert listed_info.sector_17_code_name is None
        assert listed_info.sector_33_code is None
        assert listed_info.sector_33_code_name is None
        assert listed_info.scale_category is None
        assert listed_info.market_code is None
        assert listed_info.market_code_name is None
        assert listed_info.margin_code is None
        assert listed_info.margin_code_name is None

    def test_create_multiple(self):
        """create_multiple メソッドが正しく動作することを確認"""
        data_list = [
            {
                "Date": "20240104",
                "Code": "7203",
                "CompanyName": "トヨタ自動車",
            },
            {
                "Date": "20240104",
                "Code": "6758",
                "CompanyName": "ソニーグループ",
            },
            {
                "Date": "20240104",
                "Code": "9984",
                "CompanyName": "ソフトバンクグループ",
            },
        ]

        listed_infos = ListedInfoFactory.create_multiple(data_list)

        assert len(listed_infos) == 3
        assert listed_infos[0].code.value == "7203"
        assert listed_infos[0].company_name == "トヨタ自動車"
        assert listed_infos[1].code.value == "6758"
        assert listed_infos[1].company_name == "ソニーグループ"
        assert listed_infos[2].code.value == "9984"
        assert listed_infos[2].company_name == "ソフトバンクグループ"

    def test_create_multiple_empty_list(self):
        """create_multiple メソッドに空のリストを渡した場合の動作を確認"""
        listed_infos = ListedInfoFactory.create_multiple([])
        assert len(listed_infos) == 0

    def test_factory_creates_frozen_entities(self):
        """ファクトリーが作成するエンティティが不変であることを確認"""
        data = {
            "Date": "20240104",
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
        }

        listed_info = ListedInfoFactory.from_jquants_response(data)

        # 属性の変更を試みる
        with pytest.raises(AttributeError):
            listed_info.company_name = "新しい会社名"  # type: ignore