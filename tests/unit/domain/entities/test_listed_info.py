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

    def test_is_prime_market(self):
        """is_prime_market メソッドが正しく動作することを確認"""
        prime_market_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code="0111",
            market_code_name="プライム",
            margin_code=None,
            margin_code_name=None,
        )
        
        non_prime_market_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("1234"),
            company_name="テスト企業",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code="0112",
            market_code_name="スタンダード",
            margin_code=None,
            margin_code_name=None,
        )
        
        assert prime_market_info.is_prime_market() is True
        assert non_prime_market_info.is_prime_market() is False

    def test_market_methods(self):
        """市場判定メソッドが正しく動作することを確認"""
        standard_market_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("1234"),
            company_name="スタンダード企業",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code="0112",
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )
        
        growth_market_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("5678"),
            company_name="グロース企業",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code="0113",
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )
        
        assert standard_market_info.is_standard_market() is True
        assert standard_market_info.is_growth_market() is False
        assert growth_market_info.is_growth_market() is True
        assert growth_market_info.is_standard_market() is False

    def test_sector_methods(self):
        """業種判定メソッドが正しく動作することを確認"""
        listed_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english=None,
            sector_17_code="6",
            sector_17_code_name="自動車・輸送機",
            sector_33_code="3700",
            sector_33_code_name="輸送用機器",
            scale_category=None,
            market_code=None,
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )
        
        assert listed_info.belongs_to_sector_17("6") is True
        assert listed_info.belongs_to_sector_17("1") is False
        assert listed_info.belongs_to_sector_33("3700") is True
        assert listed_info.belongs_to_sector_33("1000") is False

    def test_margin_and_scale_methods(self):
        """信用取引可能判定と規模判定メソッドが正しく動作することを確認"""
        large_cap_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("7203"),
            company_name="大型株企業",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category="TOPIX Large70",
            market_code=None,
            market_code_name=None,
            margin_code="1",
            margin_code_name="信用",
        )
        
        mid_cap_info = ListedInfo(
            date=date(2024, 1, 4),
            code=StockCode("1234"),
            company_name="中型株企業",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category="TOPIX Mid400",
            market_code=None,
            market_code_name=None,
            margin_code="0",
            margin_code_name=None,
        )
        
        assert large_cap_info.is_marginable() is True
        assert large_cap_info.is_large_cap() is True
        assert large_cap_info.is_mid_cap() is False
        assert mid_cap_info.is_marginable() is False
        assert mid_cap_info.is_mid_cap() is True
        assert mid_cap_info.is_large_cap() is False

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