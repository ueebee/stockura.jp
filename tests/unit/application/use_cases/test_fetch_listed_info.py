"""Tests for FetchListedInfoUseCase."""
import pytest
from datetime import date
from unittest.mock import AsyncMock, Mock
from typing import List

from app.application.dtos.listed_info_dto import FetchListedInfoResult
from app.application.use_cases.fetch_listed_info import FetchListedInfoUseCase
from app.domain.entities.listed_info import ListedInfo
from app.domain.entities.stock import StockCode
from app.domain.exceptions.listed_info_exceptions import (
    ListedInfoAPIError,
    ListedInfoDataError,
    ListedInfoStorageError,
)


class TestFetchListedInfoUseCase:
    """FetchListedInfoUseCase tests."""

    def setup_method(self):
        """テストのセットアップ"""
        self.jquants_client = AsyncMock()
        self.repository = AsyncMock()
        self.logger = Mock()
        self.use_case = FetchListedInfoUseCase(
            jquants_client=self.jquants_client,
            listed_info_repository=self.repository,
            logger=self.logger,
        )

    @pytest.mark.asyncio
    async def test_execute_success_all_stocks(self):
        """全銘柄の取得が成功することを確認"""
        # API レスポンスのモック
        api_data = [
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
            },
            {
                "Date": "20240104",
                "Code": "9984",
                "CompanyName": "ソフトバンクグループ",
                "CompanyNameEnglish": "SoftBank Group Corp.",
                "Sector17Code": "10",
                "Sector17CodeName": "情報通信・サービスその他",
                "Sector33Code": "5250",
                "Sector33CodeName": "情報・通信業",
                "ScaleCategory": "TOPIX Large70",
                "MarketCode": "0111",
                "MarketCodeName": "プライム",
            },
        ]
        self.jquants_client.get_all_listed_info.return_value = api_data

        # 実行
        result = await self.use_case.execute()

        # 検証
        assert result.success is True
        assert result.fetched_count == 2
        assert result.saved_count == 2
        assert result.error_message is None
        assert result.target_date is None
        assert result.code is None

        # メソッド呼び出しの検証
        self.jquants_client.get_all_listed_info.assert_called_once_with(date=None)
        self.repository.save_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_success_specific_stock(self):
        """特定銘柄の取得が成功することを確認"""
        # API レスポンスのモック
        api_data = [
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
        self.jquants_client.get_listed_info.return_value = api_data

        # 実行
        result = await self.use_case.execute(code="7203", target_date=date(2024, 1, 4))

        # 検証
        assert result.success is True
        assert result.fetched_count == 1
        assert result.saved_count == 1
        assert result.error_message is None
        assert result.target_date == date(2024, 1, 4)
        assert result.code == "7203"

        # メソッド呼び出しの検証
        self.jquants_client.get_listed_info.assert_called_once_with(
            code="7203", date="20240104"
        )
        self.repository.save_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_empty_response(self):
        """空のレスポンスの場合の処理を確認"""
        # API レスポンスのモック
        self.jquants_client.get_all_listed_info.return_value = []

        # 実行
        result = await self.use_case.execute()

        # 検証
        assert result.success is True
        assert result.fetched_count == 0
        assert result.saved_count == 0
        assert result.error_message is None

        # save_all が呼ばれていないことを確認
        self.repository.save_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_batch_processing(self):
        """バッチ処理が正しく動作することを確認"""
        # 2000 件のデータを作成（バッチサイズ 1000 を超える）
        api_data = [
            {
                "Date": "20240104",
                "Code": f"{i:04d}",
                "CompanyName": f"会社{i}",
            }
            for i in range(1, 2001)
        ]
        self.jquants_client.get_all_listed_info.return_value = api_data

        # 実行
        result = await self.use_case.execute()

        # 検証
        assert result.success is True
        assert result.fetched_count == 2000
        assert result.saved_count == 2000

        # save_all が 2 回呼ばれることを確認（1000 件ずつ）
        assert self.repository.save_all.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """API エラーが発生した場合の処理を確認"""
        # API エラーを設定
        self.jquants_client.get_all_listed_info.side_effect = ListedInfoAPIError(
            "API connection failed"
        )

        # 実行
        result = await self.use_case.execute()

        # 検証
        assert result.success is False
        assert result.fetched_count == 0
        assert result.saved_count == 0
        assert result.error_message == "API error: API connection failed"

    @pytest.mark.asyncio
    async def test_execute_data_error(self):
        """データエラーが発生した場合の処理を確認"""
        # 不正な API レスポンス
        api_data = [{"InvalidKey": "InvalidValue"}]
        self.jquants_client.get_all_listed_info.return_value = api_data

        # 実行（KeyError が発生して ListedInfoDataError として処理されることを想定）
        result = await self.use_case.execute()

        # 検証
        assert result.success is False
        assert result.fetched_count == 1
        assert result.saved_count == 0
        assert "Unexpected error" in result.error_message or "Data error" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_storage_error(self):
        """ストレージエラーが発生した場合の処理を確認"""
        # API レスポンスのモック
        api_data = [
            {
                "Date": "20240104",
                "Code": "7203",
                "CompanyName": "トヨタ自動車",
            }
        ]
        self.jquants_client.get_all_listed_info.return_value = api_data

        # リポジトリエラーを設定
        self.repository.save_all.side_effect = ListedInfoStorageError(
            "Database connection failed"
        )

        # 実行
        result = await self.use_case.execute()

        # 検証
        assert result.success is False
        assert result.fetched_count == 1
        assert result.saved_count == 0
        assert result.error_message == "Storage error: Database connection failed"

    @pytest.mark.asyncio
    async def test_fetch_and_update_all(self):
        """fetch_and_update_all メソッドが正しく動作することを確認"""
        # API レスポンスのモック
        api_data = [
            {
                "Date": "20240104",
                "Code": "7203",
                "CompanyName": "トヨタ自動車",
            }
        ]
        self.jquants_client.get_all_listed_info.return_value = api_data

        # 実行
        result = await self.use_case.fetch_and_update_all(target_date=date(2024, 1, 4))

        # 検証
        assert result.success is True
        assert result.fetched_count == 1
        assert result.saved_count == 1
        assert result.target_date == date(2024, 1, 4)
        assert result.code is None

    @pytest.mark.asyncio
    async def test_fetch_by_code(self):
        """fetch_by_code メソッドが正しく動作することを確認"""
        # API レスポンスのモック
        api_data = [
            {
                "Date": "20240104",
                "Code": "7203",
                "CompanyName": "トヨタ自動車",
            }
        ]
        self.jquants_client.get_listed_info.return_value = api_data

        # 実行
        result = await self.use_case.fetch_by_code("7203", target_date=date(2024, 1, 4))

        # 検証
        assert result.success is True
        assert result.fetched_count == 1
        assert result.saved_count == 1
        assert result.target_date == date(2024, 1, 4)
        assert result.code == "7203"

    @pytest.mark.asyncio
    async def test_logging(self):
        """ログ出力が正しく行われることを確認"""
        # API レスポンスのモック
        api_data = [
            {
                "Date": "20240104",
                "Code": "7203",
                "CompanyName": "トヨタ自動車",
            }
        ]
        self.jquants_client.get_all_listed_info.return_value = api_data

        # 実行
        await self.use_case.execute()

        # ログ出力の検証
        self.logger.info.assert_any_call("Fetching listed info - code: None, date: None")
        self.logger.info.assert_any_call("Fetched 1 records from API")
        self.logger.info.assert_any_call("Saved batch 1 - 1 records")
        self.logger.info.assert_any_call("Successfully saved 1 listed info records")