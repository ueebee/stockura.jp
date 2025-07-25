"""
CompanyDataFetcherの単体テスト
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import date

from app.services.company.company_data_fetcher import CompanyDataFetcher
from app.services.interfaces.company_sync_interfaces import DataFetchError
from app.core.exceptions import APIError, DataSourceNotFoundError


class TestCompanyDataFetcher:
    """CompanyDataFetcherのテストクラス"""
    
    @pytest.fixture
    def mock_jquants_client_manager(self):
        """モックのJQuantsClientManager"""
        manager = Mock()
        manager.get_client = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_jquants_client(self):
        """モックのJQuantsクライアント"""
        client = Mock()
        client.get_all_listed_companies = AsyncMock()
        client.get_company_info = AsyncMock()
        return client
    
    @pytest.fixture
    async def fetcher(self, mock_jquants_client_manager):
        """テスト用のフェッチャーインスタンス"""
        return CompanyDataFetcher(
            jquants_client_manager=mock_jquants_client_manager,
            data_source_id=1
        )
    
    @pytest.fixture
    def sample_companies_data(self):
        """サンプルの企業データ"""
        return [
            {
                "Code": "1234",
                "CompanyName": "テスト株式会社",
                "CompanyNameEnglish": "Test Corp",
                "Sector17Code": "1",
                "MarketCode": "0111"
            },
            {
                "Code": "5678",
                "CompanyName": "サンプル株式会社",
                "CompanyNameEnglish": "Sample Corp",
                "Sector17Code": "2",
                "MarketCode": "0111"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_fetch_all_companies_success(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client, sample_companies_data
    ):
        """全企業データ取得の正常系テスト"""
        # モックの設定
        mock_jquants_client.get_all_listed_companies.return_value = sample_companies_data
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        # 実行
        result = await fetcher.fetch_all_companies()
        
        # 検証
        assert result == sample_companies_data
        assert len(result) == 2
        mock_jquants_client_manager.get_client.assert_called_once_with(1)
        mock_jquants_client.get_all_listed_companies.assert_called_once_with(date=None)
    
    @pytest.mark.asyncio
    async def test_fetch_all_companies_with_date(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client, sample_companies_data
    ):
        """日付指定での全企業データ取得テスト"""
        # モックの設定
        mock_jquants_client.get_all_listed_companies.return_value = sample_companies_data
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        target_date = date(2024, 1, 15)
        
        # 実行
        result = await fetcher.fetch_all_companies(target_date=target_date)
        
        # 検証
        assert result == sample_companies_data
        mock_jquants_client.get_all_listed_companies.assert_called_once_with(date=target_date)
    
    @pytest.mark.asyncio
    async def test_fetch_all_companies_empty_result(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client
    ):
        """空の結果が返ってきた場合のテスト"""
        # モックの設定
        mock_jquants_client.get_all_listed_companies.return_value = []
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        # 実行
        result = await fetcher.fetch_all_companies()
        
        # 検証
        assert result == []
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_all_companies_data_source_not_found(
        self, fetcher, mock_jquants_client_manager
    ):
        """データソースが見つからない場合のテスト"""
        # モックの設定
        mock_jquants_client_manager.get_client.side_effect = DataSourceNotFoundError(1)
        
        # 実行と検証
        with pytest.raises(DataFetchError) as exc_info:
            await fetcher.fetch_all_companies()
        
        # DataSourceNotFoundErrorの場合、初期化エラーとして処理される
        assert "Failed to initialize J-Quants client" in str(exc_info.value) or "Data source not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_all_companies_api_error(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client
    ):
        """APIエラーが発生した場合のテスト"""
        # モックの設定
        mock_jquants_client.get_all_listed_companies.side_effect = APIError("API rate limit exceeded")
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        # 実行と検証
        with pytest.raises(DataFetchError) as exc_info:
            await fetcher.fetch_all_companies()
        
        assert "J-Quants API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_all_companies_unexpected_error(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client
    ):
        """予期しないエラーが発生した場合のテスト"""
        # モックの設定
        mock_jquants_client.get_all_listed_companies.side_effect = Exception("Unexpected error")
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        # 実行と検証
        with pytest.raises(DataFetchError) as exc_info:
            await fetcher.fetch_all_companies()
        
        assert "Unexpected error fetching companies data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_company_by_code_success(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client
    ):
        """特定企業データ取得の正常系テスト"""
        # モックの設定
        company_data = {
            "Code": "1234",
            "CompanyName": "テスト株式会社",
            "CompanyNameEnglish": "Test Corp"
        }
        mock_jquants_client.get_company_info.return_value = company_data
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        # 実行
        result = await fetcher.fetch_company_by_code("1234")
        
        # 検証
        assert result == company_data
        mock_jquants_client.get_company_info.assert_called_once_with(code="1234", date=None)
    
    @pytest.mark.asyncio
    async def test_fetch_company_by_code_not_found(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client
    ):
        """企業が見つからない場合のテスト"""
        # モックの設定
        mock_jquants_client.get_company_info.return_value = None
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        # 実行
        result = await fetcher.fetch_company_by_code("9999")
        
        # 検証
        assert result is None
        mock_jquants_client.get_company_info.assert_called_once_with(code="9999", date=None)
    
    @pytest.mark.asyncio
    async def test_fetch_company_by_code_with_date(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client
    ):
        """日付指定での特定企業データ取得テスト"""
        # モックの設定
        company_data = {"Code": "1234", "CompanyName": "テスト株式会社"}
        mock_jquants_client.get_company_info.return_value = company_data
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        target_date = date(2024, 1, 15)
        
        # 実行
        result = await fetcher.fetch_company_by_code("1234", target_date=target_date)
        
        # 検証
        assert result == company_data
        mock_jquants_client.get_company_info.assert_called_once_with(
            code="1234", date=target_date
        )
    
    @pytest.mark.asyncio
    async def test_client_lazy_initialization(
        self, fetcher, mock_jquants_client_manager, mock_jquants_client, sample_companies_data
    ):
        """クライアントの遅延初期化テスト"""
        # モックの設定
        mock_jquants_client.get_all_listed_companies.return_value = sample_companies_data
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        
        # 初回呼び出し
        await fetcher.fetch_all_companies()
        
        # 2回目の呼び出し
        await fetcher.fetch_all_companies()
        
        # クライアント取得は1回だけ呼ばれる（キャッシュされる）
        mock_jquants_client_manager.get_client.assert_called_once()
        
        # API呼び出しは2回実行される
        assert mock_jquants_client.get_all_listed_companies.call_count == 2
    
    @pytest.mark.asyncio
    async def test_client_initialization_error(
        self, fetcher, mock_jquants_client_manager
    ):
        """クライアント初期化エラーのテスト"""
        # モックの設定
        mock_jquants_client_manager.get_client.side_effect = Exception("Client init error")
        
        # 実行と検証
        with pytest.raises(DataFetchError) as exc_info:
            await fetcher.fetch_all_companies()
        
        assert "Failed to initialize J-Quants client" in str(exc_info.value)