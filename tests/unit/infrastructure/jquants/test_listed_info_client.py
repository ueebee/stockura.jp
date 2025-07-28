"""Tests for JQuantsListedInfoClient."""
import pytest
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, List

from app.infrastructure.jquants.listed_info_client import JQuantsListedInfoClient
from app.infrastructure.jquants.base_client import JQuantsBaseClient
from app.domain.exceptions.jquants_exceptions import (
    NetworkError,
    RateLimitError,
    ValidationError,
)


class TestJQuantsListedInfoClient:
    """JQuantsListedInfoClient tests."""

    def setup_method(self):
        """テストのセットアップ"""
        self.base_client = AsyncMock(spec=JQuantsBaseClient)
        self.client = JQuantsListedInfoClient(self.base_client)

    @pytest.mark.asyncio
    async def test_get_listed_info_without_params(self):
        """パラメータなしで get_listed_info が正しく動作することを確認"""
        # モックの設定
        expected_response = {
            "info": [
                {
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
                }
            ]
        }
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_listed_info()

        # 検証
        assert len(result) == 1
        assert result[0]["Code"] == "7203"
        assert result[0]["CompanyName"] == "トヨタ自動車"
        self.base_client.get.assert_called_once_with("/listed/info", params={})

    @pytest.mark.asyncio
    async def test_get_listed_info_with_code(self):
        """コード指定で get_listed_info が正しく動作することを確認"""
        # モックの設定
        expected_response = {
            "info": [
                {
                    "Date": "20240104",
                    "Code": "7203",
                    "CompanyName": "トヨタ自動車",
                }
            ]
        }
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_listed_info(code="7203")

        # 検証
        assert len(result) == 1
        assert result[0]["Code"] == "7203"
        self.base_client.get.assert_called_once_with(
            "/listed/info", params={"code": "7203"}
        )

    @pytest.mark.asyncio
    async def test_get_listed_info_with_date(self):
        """日付指定で get_listed_info が正しく動作することを確認"""
        # モックの設定
        expected_response = {
            "info": [
                {
                    "Date": "20240104",
                    "Code": "7203",
                    "CompanyName": "トヨタ自動車",
                },
                {
                    "Date": "20240104",
                    "Code": "9984",
                    "CompanyName": "ソフトバンクグループ",
                },
            ]
        }
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_listed_info(date="20240104")

        # 検証
        assert len(result) == 2
        assert result[0]["Code"] == "7203"
        assert result[1]["Code"] == "9984"
        self.base_client.get.assert_called_once_with(
            "/listed/info", params={"date": "20240104"}
        )

    @pytest.mark.asyncio
    async def test_get_listed_info_with_code_and_date(self):
        """コードと日付の両方を指定した場合のテスト"""
        # モックの設定
        expected_response = {
            "info": [
                {
                    "Date": "20240104",
                    "Code": "7203",
                    "CompanyName": "トヨタ自動車",
                }
            ]
        }
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_listed_info(code="7203", date="20240104")

        # 検証
        assert len(result) == 1
        assert result[0]["Code"] == "7203"
        assert result[0]["Date"] == "20240104"
        self.base_client.get.assert_called_once_with(
            "/listed/info", params={"code": "7203", "date": "20240104"}
        )

    @pytest.mark.asyncio
    async def test_get_listed_info_empty_response(self):
        """空のレスポンスの場合のテスト"""
        # モックの設定
        expected_response = {"info": []}
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_listed_info()

        # 検証
        assert len(result) == 0
        self.base_client.get.assert_called_once_with("/listed/info", params={})

    @pytest.mark.asyncio
    async def test_get_listed_info_no_info_key(self):
        """レスポンスに info キーがない場合のテスト"""
        # モックの設定
        expected_response = {}
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_listed_info()

        # 検証
        assert len(result) == 0
        self.base_client.get.assert_called_once_with("/listed/info", params={})

    @pytest.mark.asyncio
    async def test_get_listed_info_network_error(self):
        """ネットワークエラーが発生した場合のテスト"""
        # モックの設定
        self.base_client.get.side_effect = NetworkError("Connection failed")

        # 実行と検証
        with pytest.raises(NetworkError) as exc_info:
            await self.client.get_listed_info()
        
        assert str(exc_info.value) == "Connection failed"

    @pytest.mark.asyncio
    async def test_get_listed_info_rate_limit_error(self):
        """レート制限エラーが発生した場合のテスト"""
        # モックの設定
        self.base_client.get.side_effect = RateLimitError("Rate limit exceeded")

        # 実行と検証
        with pytest.raises(RateLimitError) as exc_info:
            await self.client.get_listed_info()
        
        assert str(exc_info.value) == "Rate limit exceeded"

    @pytest.mark.asyncio
    async def test_get_all_listed_info_single_page(self):
        """get_all_listed_info でページネーションなしの場合のテスト"""
        # モックの設定
        expected_response = {
            "info": [
                {"Date": "20240104", "Code": "7203", "CompanyName": "トヨタ自動車"},
                {"Date": "20240104", "Code": "9984", "CompanyName": "ソフトバンクグループ"},
            ]
        }
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_all_listed_info()

        # 検証
        assert len(result) == 2
        assert result[0]["Code"] == "7203"
        assert result[1]["Code"] == "9984"
        self.base_client.get.assert_called_once_with("/listed/info", params={})

    @pytest.mark.asyncio
    async def test_get_all_listed_info_with_pagination(self):
        """get_all_listed_info でページネーションありの場合のテスト"""
        # モックの設定
        # 1 ページ目
        first_response = {
            "info": [
                {"Date": "20240104", "Code": "7203", "CompanyName": "トヨタ自動車"},
                {"Date": "20240104", "Code": "9984", "CompanyName": "ソフトバンクグループ"},
            ],
            "pagination_key": "next_page_key"
        }
        # 2 ページ目
        second_response = {
            "info": [
                {"Date": "20240104", "Code": "6758", "CompanyName": "ソニーグループ"},
                {"Date": "20240104", "Code": "8306", "CompanyName": "三菱 UFJ フィナンシャル・グループ"},
            ]
        }
        
        self.base_client.get.side_effect = [first_response, second_response]

        # 実行
        result = await self.client.get_all_listed_info()

        # 検証
        assert len(result) == 4
        assert result[0]["Code"] == "7203"
        assert result[1]["Code"] == "9984"
        assert result[2]["Code"] == "6758"
        assert result[3]["Code"] == "8306"
        
        # get メソッドが 2 回呼ばれたことを確認
        assert self.base_client.get.call_count == 2
        # 1 回目の呼び出し
        self.base_client.get.assert_any_call("/listed/info", params={})
        # 2 回目の呼び出し（pagination_key 付き）
        self.base_client.get.assert_any_call(
            "/listed/info", params={"pagination_key": "next_page_key"}
        )

    @pytest.mark.asyncio
    async def test_get_all_listed_info_with_date(self):
        """get_all_listed_info で日付指定の場合のテスト"""
        # モックの設定
        expected_response = {
            "info": [
                {"Date": "20240104", "Code": "7203", "CompanyName": "トヨタ自動車"},
            ]
        }
        self.base_client.get.return_value = expected_response

        # 実行
        result = await self.client.get_all_listed_info(date="20240104")

        # 検証
        assert len(result) == 1
        assert result[0]["Date"] == "20240104"
        self.base_client.get.assert_called_once_with(
            "/listed/info", params={"date": "20240104"}
        )

    @pytest.mark.asyncio
    async def test_get_all_listed_info_multiple_pages_with_date(self):
        """get_all_listed_info で日付指定かつ複数ページの場合のテスト"""
        # モックの設定
        first_response = {
            "info": [
                {"Date": "20240104", "Code": "7203", "CompanyName": "トヨタ自動車"},
            ],
            "pagination_key": "page2"
        }
        second_response = {
            "info": [
                {"Date": "20240104", "Code": "9984", "CompanyName": "ソフトバンクグループ"},
            ],
            "pagination_key": "page3"
        }
        third_response = {
            "info": [
                {"Date": "20240104", "Code": "6758", "CompanyName": "ソニーグループ"},
            ]
        }
        
        self.base_client.get.side_effect = [first_response, second_response, third_response]

        # 実行
        result = await self.client.get_all_listed_info(date="20240104")

        # 検証
        assert len(result) == 3
        assert self.base_client.get.call_count == 3
        
        # 各呼び出しの確認
        self.base_client.get.assert_any_call(
            "/listed/info", params={"date": "20240104"}
        )
        self.base_client.get.assert_any_call(
            "/listed/info", params={"date": "20240104", "pagination_key": "page2"}
        )
        self.base_client.get.assert_any_call(
            "/listed/info", params={"date": "20240104", "pagination_key": "page3"}
        )