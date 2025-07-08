"""
J-Quants クライアントのテスト
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date
from typing import Dict, Any, List

from app.services.jquants_client import JQuantsListedInfoClient, JQuantsClientManager
from app.services.data_source_service import DataSourceService


class TestJQuantsListedInfoClient:
    """J-Quants上場情報クライアントのテスト"""

    @pytest.fixture
    def mock_data_source_service(self):
        """モックデータソースサービス"""
        mock_service = Mock(spec=DataSourceService)
        mock_service.get_valid_api_token = AsyncMock(return_value="test_id_token")
        return mock_service

    @pytest.fixture
    def client(self, mock_data_source_service):
        """JQuantsListedInfoClientのインスタンス"""
        return JQuantsListedInfoClient(
            data_source_service=mock_data_source_service,
            data_source_id=1,
            base_url="https://api.jquants.com"
        )

    @pytest.fixture
    def sample_jquants_response(self):
        """サンプルのJ-Quants APIレスポンス"""
        return {
            "info": [
                {
                    "Date": "20241226",
                    "Code": "1234",
                    "CompanyName": "テスト株式会社",
                    "CompanyNameEnglish": "Test Corporation",
                    "Sector17Code": "01",
                    "Sector17CodeName": "食品",
                    "Sector33Code": "050",
                    "Sector33CodeName": "食料品",
                    "ScaleCategory": "TOPIX Large70",
                    "MarketCode": "0111",
                    "MarketCodeName": "プライム",
                    "MarginCode": "1",
                    "MarginCodeName": "制度信用"
                },
                {
                    "Date": "20241226",
                    "Code": "5678",
                    "CompanyName": "サンプル商事",
                    "CompanyNameEnglish": "Sample Trading Co.",
                    "Sector17Code": "02",
                    "Sector17CodeName": "繊維製品",
                    "Sector33Code": "100",
                    "Sector33CodeName": "繊維製品",
                    "ScaleCategory": "TOPIX Mid400",
                    "MarketCode": "0112",
                    "MarketCodeName": "スタンダード",
                    "MarginCode": "2",
                    "MarginCodeName": "一般信用"
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_listed_info_success(self, client, sample_jquants_response):
        """上場情報取得の成功テスト"""
        with patch('httpx.AsyncClient') as mock_client:
            # HTTPレスポンスをモック
            mock_response = Mock()
            mock_response.json.return_value = sample_jquants_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # テスト実行
            result = await client.get_listed_info()
            
            # 結果検証
            assert len(result) == 2
            assert result[0]["Code"] == "1234"
            assert result[0]["CompanyName"] == "テスト株式会社"
            assert result[1]["Code"] == "5678"
            assert result[1]["CompanyName"] == "サンプル商事"

    @pytest.mark.asyncio
    async def test_get_listed_info_with_code(self, client, sample_jquants_response):
        """特定銘柄コードでの上場情報取得テスト"""
        with patch('httpx.AsyncClient') as mock_client:
            # 1件のみ返すレスポンス
            filtered_response = {
                "info": [sample_jquants_response["info"][0]]
            }
            
            mock_response = Mock()
            mock_response.json.return_value = filtered_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # テスト実行
            result = await client.get_listed_info(code="1234")
            
            # 結果検証
            assert len(result) == 1
            assert result[0]["Code"] == "1234"
            
            # リクエストパラメータの検証
            mock_client.return_value.__aenter__.return_value.get.assert_called_once()
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]["params"]["code"] == "1234"

    @pytest.mark.asyncio
    async def test_get_listed_info_with_date(self, client, sample_jquants_response):
        """特定日付での上場情報取得テスト"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = sample_jquants_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # テスト実行（date型）
            test_date = date(2024, 12, 26)
            result = await client.get_listed_info(date=test_date)
            
            # 結果検証
            assert len(result) == 2
            
            # リクエストパラメータの検証
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]["params"]["date"] == "20241226"

    @pytest.mark.asyncio
    async def test_get_listed_info_with_datetime(self, client, sample_jquants_response):
        """datetime型での上場情報取得テスト"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = sample_jquants_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # テスト実行（datetime型）
            test_datetime = datetime(2024, 12, 26, 15, 30, 0)
            result = await client.get_listed_info(date=test_datetime)
            
            # 結果検証
            assert len(result) == 2
            
            # リクエストパラメータの検証
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]["params"]["date"] == "20241226"

    @pytest.mark.asyncio
    async def test_get_listed_info_no_token_error(self, mock_data_source_service):
        """トークン取得失敗のエラーテスト"""
        # トークン取得を失敗させる
        mock_data_source_service.get_valid_api_token.return_value = None
        
        client = JQuantsListedInfoClient(
            data_source_service=mock_data_source_service,
            data_source_id=1
        )
        
        # テスト実行
        with pytest.raises(Exception) as exc_info:
            await client.get_listed_info()
        
        assert "Failed to get valid API token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_listed_info_http_error(self, client):
        """HTTP エラーのテスト"""
        with patch('httpx.AsyncClient') as mock_client:
            # HTTPエラーをモック
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            
            from httpx import HTTPStatusError
            mock_client.return_value.__aenter__.return_value.get.side_effect = HTTPStatusError(
                "Unauthorized", request=Mock(), response=mock_response
            )
            
            # テスト実行
            with pytest.raises(Exception) as exc_info:
                await client.get_listed_info()
            
            assert "J-Quants API HTTP error: 401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_company_info_success(self, client, sample_jquants_response):
        """特定企業情報取得の成功テスト"""
        with patch('httpx.AsyncClient') as mock_client:
            # 1件のみ返すレスポンス
            filtered_response = {
                "info": [sample_jquants_response["info"][0]]
            }
            
            mock_response = Mock()
            mock_response.json.return_value = filtered_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # テスト実行
            result = await client.get_company_info("1234")
            
            # 結果検証
            assert result is not None
            assert result["Code"] == "1234"
            assert result["CompanyName"] == "テスト株式会社"

    @pytest.mark.asyncio
    async def test_get_company_info_not_found(self, client):
        """企業情報が見つからない場合のテスト"""
        with patch('httpx.AsyncClient') as mock_client:
            # 空のレスポンス
            empty_response = {"info": []}
            
            mock_response = Mock()
            mock_response.json.return_value = empty_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # テスト実行
            result = await client.get_company_info("9999")
            
            # 結果検証
            assert result is None

    @pytest.mark.asyncio
    async def test_test_connection_success(self, client, sample_jquants_response):
        """接続テストの成功テスト"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = sample_jquants_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # テスト実行
            result = await client.test_connection()
            
            # 結果検証
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client):
        """接続テストの失敗テスト"""
        with patch('httpx.AsyncClient') as mock_client:
            # 例外を発生させる
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Connection failed")
            
            # テスト実行
            result = await client.test_connection()
            
            # 結果検証
            assert result is False


class TestJQuantsClientManager:
    """J-Quantsクライアント管理のテスト"""

    @pytest.fixture
    def mock_data_source_service(self):
        """モックデータソースサービス"""
        return Mock(spec=DataSourceService)

    @pytest.fixture
    def manager(self, mock_data_source_service):
        """JQuantsClientManagerのインスタンス"""
        return JQuantsClientManager(mock_data_source_service)

    @pytest.fixture
    def sample_data_source(self):
        """サンプルデータソース"""
        mock_data_source = Mock()
        mock_data_source.provider_type = "jquants"
        mock_data_source.base_url = "https://api.jquants.com"
        return mock_data_source

    @pytest.mark.asyncio
    async def test_get_client_success(self, manager, mock_data_source_service, sample_data_source):
        """クライアント取得の成功テスト"""
        # データソース取得をモック
        mock_data_source_service.get_data_source.return_value = sample_data_source
        
        # テスト実行
        client = await manager.get_client(1)
        
        # 結果検証
        assert isinstance(client, JQuantsListedInfoClient)
        assert client.data_source_id == 1
        assert client.base_url == "https://api.jquants.com"

    @pytest.mark.asyncio
    async def test_get_client_not_found(self, manager, mock_data_source_service):
        """データソースが見つからない場合のテスト"""
        # データソースが見つからない場合
        mock_data_source_service.get_data_source.return_value = None
        
        # テスト実行
        with pytest.raises(Exception) as exc_info:
            await manager.get_client(999)
        
        assert "Data source not found: 999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_wrong_provider(self, manager, mock_data_source_service):
        """プロバイダタイプが違う場合のテスト"""
        # 異なるプロバイダタイプ
        mock_data_source = Mock()
        mock_data_source.provider_type = "yfinance"
        mock_data_source_service.get_data_source.return_value = mock_data_source
        
        # テスト実行
        with pytest.raises(Exception) as exc_info:
            await manager.get_client(1)
        
        assert "is not a J-Quants provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_caching(self, manager, mock_data_source_service, sample_data_source):
        """クライアントのキャッシュテスト"""
        # データソース取得をモック
        mock_data_source_service.get_data_source.return_value = sample_data_source
        
        # 同じIDで2回取得
        client1 = await manager.get_client(1)
        client2 = await manager.get_client(1)
        
        # 同じインスタンスが返されることを確認
        assert client1 is client2
        
        # データソース取得は1回だけ呼ばれることを確認
        assert mock_data_source_service.get_data_source.call_count == 1

    def test_clear_client_cache(self, manager):
        """クライアントキャッシュのクリアテスト"""
        # キャッシュにダミーデータを設定
        manager._listed_clients[1] = Mock()
        manager._listed_clients[2] = Mock()
        manager._daily_quotes_clients[1] = Mock()
        manager._daily_quotes_clients[2] = Mock()
        
        # 特定のクライアントをクリア
        manager.clear_client_cache(1)
        assert 1 not in manager._listed_clients
        assert 2 in manager._listed_clients
        assert 1 not in manager._daily_quotes_clients
        assert 2 in manager._daily_quotes_clients
        
        # 全てクリア
        manager.clear_client_cache()
        assert len(manager._listed_clients) == 0
        assert len(manager._daily_quotes_clients) == 0