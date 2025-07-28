"""Tests for ListedInfo DTOs."""
import pytest
from datetime import date

from app.application.dtos.listed_info_dto import (
    FetchListedInfoResult,
    ListedInfoDTO,
    ListedInfoSearchCriteria,
)
from app.domain.entities.listed_info import ListedInfo
from app.domain.entities.stock import StockCode


class TestListedInfoDTO:
    """ListedInfoDTO tests."""

    def test_from_api_response(self):
        """API レスポンスから DTO が正しく作成されることを確認"""
        api_response = {
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

        dto = ListedInfoDTO.from_api_response(api_response)

        assert dto.date == "20240104"
        assert dto.code == "7203"
        assert dto.company_name == "トヨタ自動車"
        assert dto.company_name_english == "TOYOTA MOTOR CORPORATION"
        assert dto.sector_17_code == "6"
        assert dto.sector_17_code_name == "自動車・輸送機"
        assert dto.sector_33_code == "3700"
        assert dto.sector_33_code_name == "輸送用機器"
        assert dto.scale_category == "TOPIX Large70"
        assert dto.market_code == "0111"
        assert dto.market_code_name == "プライム"
        assert dto.margin_code == "1"
        assert dto.margin_code_name == "信用"

    def test_from_api_response_with_optional_fields(self):
        """オプショナルフィールドがない API レスポンスから DTO が作成されることを確認"""
        api_response = {
            "Date": "20240104",
            "Code": "7203",
            "CompanyName": "トヨタ自動車",
        }

        dto = ListedInfoDTO.from_api_response(api_response)

        assert dto.date == "20240104"
        assert dto.code == "7203"
        assert dto.company_name == "トヨタ自動車"
        assert dto.company_name_english is None
        assert dto.sector_17_code is None
        assert dto.margin_code is None

    def test_to_entity_yyyymmdd_format(self):
        """DTO からエンティティへの変換（YYYYMMDD 形式）が正しく動作することを確認"""
        dto = ListedInfoDTO(
            date="20240104",
            code="7203",
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

        entity = dto.to_entity()

        assert isinstance(entity, ListedInfo)
        assert entity.date == date(2024, 1, 4)
        assert entity.code.value == "7203"
        assert entity.company_name == "トヨタ自動車"
        assert entity.company_name_english == "TOYOTA MOTOR CORPORATION"

    def test_to_entity_yyyy_mm_dd_format(self):
        """DTO からエンティティへの変換（YYYY-MM-DD 形式）が正しく動作することを確認"""
        dto = ListedInfoDTO(
            date="2024-01-04",
            code="7203",
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

        entity = dto.to_entity()

        assert isinstance(entity, ListedInfo)
        assert entity.date == date(2024, 1, 4)
        assert entity.code.value == "7203"
        assert entity.company_name == "トヨタ自動車"

    def test_from_entity(self):
        """エンティティから DTO への変換が正しく動作することを確認"""
        entity = ListedInfo(
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

        dto = ListedInfoDTO.from_entity(entity)

        assert dto.date == "2024-01-04"
        assert dto.code == "7203"
        assert dto.company_name == "トヨタ自動車"
        assert dto.company_name_english == "TOYOTA MOTOR CORPORATION"
        assert dto.sector_17_code == "6"
        assert dto.margin_code == "1"

    def test_dto_is_frozen(self):
        """ListedInfoDTO が不変（frozen）であることを確認"""
        dto = ListedInfoDTO(
            date="20240104",
            code="7203",
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

        with pytest.raises(AttributeError):
            dto.company_name = "新しい会社名"  # type: ignore


class TestFetchListedInfoResult:
    """FetchListedInfoResult DTO tests."""

    def test_success_result(self):
        """成功結果の DTO が正しく作成されることを確認"""
        result = FetchListedInfoResult(
            success=True,
            fetched_count=100,
            saved_count=100,
            error_message=None,
            target_date=date(2024, 1, 4),
            code=None,
        )

        assert result.success is True
        assert result.fetched_count == 100
        assert result.saved_count == 100
        assert result.error_message is None
        assert result.target_date == date(2024, 1, 4)
        assert result.code is None

    def test_failure_result(self):
        """失敗結果の DTO が正しく作成されることを確認"""
        result = FetchListedInfoResult(
            success=False,
            fetched_count=0,
            saved_count=0,
            error_message="API connection failed",
            target_date=None,
            code="7203",
        )

        assert result.success is False
        assert result.fetched_count == 0
        assert result.saved_count == 0
        assert result.error_message == "API connection failed"
        assert result.target_date is None
        assert result.code == "7203"

    def test_partial_success_result(self):
        """部分的な成功結果の DTO が正しく作成されることを確認"""
        result = FetchListedInfoResult(
            success=False,
            fetched_count=100,
            saved_count=50,
            error_message="Database error occurred during save",
            target_date=date(2024, 1, 4),
            code=None,
        )

        assert result.success is False
        assert result.fetched_count == 100
        assert result.saved_count == 50
        assert result.error_message == "Database error occurred during save"

    def test_result_is_frozen(self):
        """FetchListedInfoResult が不変（frozen）であることを確認"""
        result = FetchListedInfoResult(
            success=True,
            fetched_count=100,
            saved_count=100,
        )

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore


class TestListedInfoSearchCriteria:
    """ListedInfoSearchCriteria DTO tests."""

    def test_empty_criteria(self):
        """空の検索条件が作成できることを確認"""
        criteria = ListedInfoSearchCriteria()

        assert criteria.date is None
        assert criteria.code is None
        assert criteria.market_code is None
        assert criteria.sector_17_code is None
        assert criteria.sector_33_code is None

    def test_full_criteria(self):
        """全ての検索条件を指定した DTO が作成できることを確認"""
        criteria = ListedInfoSearchCriteria(
            date=date(2024, 1, 4),
            code="7203",
            market_code="0111",
            sector_17_code="6",
            sector_33_code="3700",
        )

        assert criteria.date == date(2024, 1, 4)
        assert criteria.code == "7203"
        assert criteria.market_code == "0111"
        assert criteria.sector_17_code == "6"
        assert criteria.sector_33_code == "3700"

    def test_partial_criteria(self):
        """一部の検索条件を指定した DTO が作成できることを確認"""
        criteria = ListedInfoSearchCriteria(
            date=date(2024, 1, 4),
            market_code="0111",
        )

        assert criteria.date == date(2024, 1, 4)
        assert criteria.code is None
        assert criteria.market_code == "0111"
        assert criteria.sector_17_code is None
        assert criteria.sector_33_code is None

    def test_criteria_is_frozen(self):
        """ListedInfoSearchCriteria が不変（frozen）であることを確認"""
        criteria = ListedInfoSearchCriteria(
            date=date(2024, 1, 4),
            code="7203",
        )

        with pytest.raises(AttributeError):
            criteria.code = "9999"  # type: ignore