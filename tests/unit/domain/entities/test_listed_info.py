"""Tests for ListedInfo entity."""
import pytest
from datetime import date

from app.domain.entities.listed_info import ListedInfo
from app.domain.value_objects.stock_code import StockCode


class TestListedInfo:
    """ListedInfo entity tests."""

    def test_create_valid_listed_info(self):
        """正常な ListedInfo エンティティが作成できることを確認"""
        listed_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english="TOYOTA MOTOR CORPORATION",
            sector_17_code="6",
            sector_17_code_name="自動車・輸送機",
            sector_33_code="3700",
            sector_33_code_name="輸送用機器",
            scale_category="TOPIX Large70",
            market_code="0111",
            market_code_name="プライム",
            margin_code="1",
            margin_code_name="信用",
        )

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

    def test_create_minimal_listed_info(self):
        """必須項目のみで ListedInfo エンティティが作成できることを確認"""
        listed_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code=None,
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )

        assert listed_info.date == date(2024, 1, 4)
        assert listed_info.code.value == "7203"
        assert listed_info.company_name == "トヨタ自動車"
        assert listed_info.company_name_english is None

    def test_company_name_required(self):
        """会社名が必須であることを確認"""
        with pytest.raises(ValueError, match="会社名は必須です"):
            ListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("7203"),
                company_name="",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code=None,
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            )

    def test_date_must_be_date_type(self):
        """日付が date 型である必要があることを確認"""
        with pytest.raises(ValueError, match="日付は date 型である必要があります"):
            ListedInfo(
                date="2024-01-04",  # type: ignore
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code=None,
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            )

    def test_from_dict_yyyymmdd_format(self):
        """from_dict メソッドで YYYYMMDD 形式の日付が解析できることを確認"""
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

        listed_info = ListedInfo.from_dict(data)

        assert listed_info.date == date(2024, 1, 4)
        assert listed_info.code.value == "7203"
        assert listed_info.company_name == "トヨタ自動車"

    def test_from_dict_yyyy_mm_dd_format(self):
        """from_dict メソッドで YYYY-MM-DD 形式の日付が解析できることを確認"""
        data = {
            "Date": "2024-01-04",
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
        }

        listed_info = ListedInfo.from_dict(data)

        assert listed_info.date == date(2024, 1, 4)
        assert listed_info.code.value == "7203"
        assert listed_info.company_name == "トヨタ自動車"

    def test_from_dict_with_optional_fields(self):
        """from_dict メソッドでオプショナルフィールドが正しく処理されることを確認"""
        data = {
            "Date": "20240104",
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
            # オプショナルフィールドは含まない
        }

        listed_info = ListedInfo.from_dict(data)

        assert listed_info.date == date(2024, 1, 4)
        assert listed_info.code.value == "7203"
        assert listed_info.company_name == "トヨタ自動車"
        assert listed_info.company_name_english is None
        assert listed_info.sector_17_code is None

    def test_is_same_listing(self):
        """is_same_listing メソッドが正しく動作することを確認"""
        listed_info1 = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code=None,
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )

        listed_info2 = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="TOYOTA",  # 異なる会社名
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code=None,
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )

        listed_info3 = ListedInfo(
            date=date(2024, 1, 5),  # 異なる日付
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code=None,
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )

        # 同じ日付・同じコード
        assert listed_info1.is_same_listing(listed_info2) is True
        # 異なる日付
        assert listed_info1.is_same_listing(listed_info3) is False

    def test_frozen_dataclass(self):
        """ListedInfo が不変（frozen）であることを確認"""
        listed_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code=None,
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )

        # 属性の変更を試みる
        with pytest.raises(AttributeError):
            listed_info.company_name = "新しい会社名"  # type: ignore