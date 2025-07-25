"""
DailyQuotesDataFetcherの単体テスト
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio

from app.services.daily_quotes.daily_quotes_data_fetcher import DailyQuotesDataFetcher
from app.services.interfaces.daily_quotes_sync_interfaces import (
    DataFetchError,
    RateLimitError
)


class TestDailyQuotesDataFetcher:
    """DailyQuotesDataFetcherのテストクラス"""
    
    @pytest_asyncio.fixture
    async def mock_client_manager(self):
        """モッククライアントマネージャーを作成"""
        manager = AsyncMock()
        return manager
    
    @pytest_asyncio.fixture
    async def mock_client(self):
        """モッククライアントを作成"""
        client = AsyncMock()
        return client
    
    @pytest_asyncio.fixture
    async def fetcher(self, mock_client_manager):
        """フェッチャーインスタンスを作成"""
        return DailyQuotesDataFetcher(mock_client_manager, data_source_id=1)
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_success(self, fetcher, mock_client_manager, mock_client):
        """指定日の株価データ取得（成功）"""
        # モックデータ
        mock_quotes = [
            {"Code": "1234", "Date": "2024-01-15", "Open": "1000"},
            {"Code": "5678", "Date": "2024-01-15", "Open": "2000"}
        ]
        
        # モックの設定
        mock_client.get_stock_prices_by_date.return_value = mock_quotes
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # テスト実行
        result = await fetcher.fetch_quotes_by_date(date(2024, 1, 15))
        
        assert result == mock_quotes
        mock_client.get_stock_prices_by_date.assert_called_once_with("2024-01-15")
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_with_codes(self, fetcher, mock_client_manager, mock_client):
        """指定日の株価データ取得（銘柄指定）"""
        # モックデータ
        mock_quotes = [
            {"Code": "1234", "Date": "2024-01-15", "Open": "1000"}
        ]
        
        # モックの設定
        mock_client.get_stock_prices_by_date.return_value = mock_quotes
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # テスト実行
        result = await fetcher.fetch_quotes_by_date(
            date(2024, 1, 15),
            codes=["1234", "5678"]
        )
        
        # 各銘柄ごとに呼ばれることを確認
        assert mock_client.get_stock_prices_by_date.call_count == 2
        assert len(result) == 2  # 2銘柄分のデータ
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_authentication_error(self, fetcher, mock_client_manager, mock_client):
        """認証エラーの処理"""
        # モックの設定
        mock_client.get_stock_prices_by_date.side_effect = Exception("401 Unauthorized")
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # テスト実行
        with pytest.raises(DataFetchError) as exc_info:
            await fetcher.fetch_quotes_by_date(date(2024, 1, 15))
        
        assert "Authentication failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_rate_limit_error(self, fetcher, mock_client_manager, mock_client):
        """レート制限エラーの処理"""
        # モックの設定
        mock_client.get_stock_prices_by_date.side_effect = Exception("429 Too Many Requests")
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # テスト実行
        with pytest.raises(RateLimitError) as exc_info:
            await fetcher.fetch_quotes_by_date(date(2024, 1, 15))
        
        assert exc_info.value.retry_after == 60
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_no_data(self, fetcher, mock_client_manager, mock_client):
        """データが存在しない場合（404）"""
        # モックの設定
        mock_client.get_stock_prices_by_date.side_effect = Exception("404 Not Found")
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # テスト実行
        result = await fetcher.fetch_quotes_by_date(date(2024, 1, 15))
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_range_success(self, fetcher, mock_client_manager, mock_client):
        """日付範囲の株価データ取得（成功）"""
        # モックデータ
        mock_quotes_15 = [{"Code": "1234", "Date": "2024-01-15", "Open": "1000"}]
        mock_quotes_16 = [{"Code": "1234", "Date": "2024-01-16", "Open": "1010"}]
        
        # モックの設定
        mock_client.get_stock_prices_by_date.side_effect = [
            mock_quotes_15,
            mock_quotes_16
        ]
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # テスト実行
        result = await fetcher.fetch_quotes_by_date_range(
            date(2024, 1, 15),
            date(2024, 1, 16)
        )
        
        assert len(result) == 2
        assert result[date(2024, 1, 15)] == mock_quotes_15
        assert result[date(2024, 1, 16)] == mock_quotes_16
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_range_invalid_range(self, fetcher):
        """無効な日付範囲"""
        # テスト実行
        with pytest.raises(DataFetchError) as exc_info:
            await fetcher.fetch_quotes_by_date_range(
                date(2024, 1, 16),
                date(2024, 1, 15)
            )
        
        assert "Invalid date range" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_by_date_range_with_rate_limit(self, fetcher, mock_client_manager, mock_client):
        """レート制限エラー時のリトライ"""
        # モックデータ
        mock_quotes = [{"Code": "1234", "Date": "2024-01-15", "Open": "1000"}]
        
        # モックの設定（最初はレート制限、次は成功）
        mock_client.get_stock_prices_by_date.side_effect = [
            Exception("429 Rate Limit"),
            mock_quotes
        ]
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # sleepをモック化
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await fetcher.fetch_quotes_by_date_range(
                date(2024, 1, 15),
                date(2024, 1, 15)
            )
        
        assert len(result) == 1
        assert result[date(2024, 1, 15)] == mock_quotes
        assert mock_client.get_stock_prices_by_date.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_client_initialization(self, fetcher, mock_client_manager, mock_client):
        """クライアントの遅延初期化"""
        # モックの設定
        mock_client_manager.get_daily_quotes_client.return_value = mock_client
        
        # 初回呼び出し
        client1 = await fetcher._get_client()
        assert client1 == mock_client
        assert mock_client_manager.get_daily_quotes_client.call_count == 1
        
        # 2回目呼び出し（キャッシュされる）
        client2 = await fetcher._get_client()
        assert client2 == mock_client
        assert mock_client_manager.get_daily_quotes_client.call_count == 1  # 増えない
    
    @pytest.mark.asyncio
    async def test_get_client_error(self, fetcher, mock_client_manager):
        """クライアント取得エラー"""
        # モックの設定
        mock_client_manager.get_daily_quotes_client.side_effect = Exception("Connection error")
        
        # テスト実行
        from app.core.exceptions import DataSourceNotFoundError
        
        with pytest.raises(DataSourceNotFoundError) as exc_info:
            await fetcher._get_client()
        
        assert "Failed to get J-Quants client" in str(exc_info.value)