"""
DailyQuotesSyncServiceの単体テスト
"""

import pytest
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.daily_quotes_sync_service import DailyQuotesSyncService
from app.models.daily_quote import DailyQuotesSyncHistory
from app.services.interfaces.daily_quotes_sync_interfaces import (
    DataFetchError,
    RateLimitError
)


class TestDailyQuotesSyncService:
    """DailyQuotesSyncServiceのテストクラス"""
    
    @pytest_asyncio.fixture
    async def mock_data_source_service(self):
        """モックデータソースサービス"""
        return AsyncMock()
    
    @pytest_asyncio.fixture
    async def mock_jquants_client_manager(self):
        """モックJ-Quantsクライアントマネージャー"""
        return AsyncMock()
    
    @pytest_asyncio.fixture
    async def mock_fetcher(self):
        """モックフェッチャー"""
        return AsyncMock()
    
    @pytest_asyncio.fixture
    async def mock_mapper(self):
        """モックマッパー"""
        mapper = AsyncMock()
        # デフォルトでは全てのデータをそのまま返す
        mapper.map_to_model.side_effect = lambda x: x
        return mapper
    
    @pytest_asyncio.fixture
    async def mock_repository(self):
        """モックリポジトリ"""
        return AsyncMock()
    
    @pytest_asyncio.fixture
    async def service(
        self,
        mock_data_source_service,
        mock_jquants_client_manager,
        mock_fetcher,
        mock_mapper,
        mock_repository
    ):
        """サービスインスタンスを作成"""
        return DailyQuotesSyncService(
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_client_manager,
            fetcher=mock_fetcher,
            mapper=mock_mapper,
            repository=mock_repository
        )
    
    @pytest.mark.asyncio
    async def test_sync_entry_point(self, service):
        """syncメソッドのエントリーポイントテスト"""
        # sync_daily_quotesをモック
        mock_history = DailyQuotesSyncHistory(
            id=1,
            status="completed",
            total_records=100,
            new_records=50,
            updated_records=40,
            skipped_records=10
        )
        
        with patch.object(service, 'sync_daily_quotes', return_value=mock_history) as mock_sync:
            result = await service.sync(
                data_source_id=1,
                sync_type="full",
                target_date=date(2024, 1, 15)
            )
        
        assert result["status"] == "completed"
        assert result["history_id"] == 1
        assert result["total_records"] == 100
        assert result["new_records"] == 50
        assert result["updated_records"] == 40
        assert result["skipped_records"] == 10
        
        mock_sync.assert_called_once_with(
            data_source_id=1,
            sync_type="full",
            target_date=date(2024, 1, 15),
            from_date=None,
            to_date=None,
            specific_codes=None,
            execution_type="manual"
        )
    
    @pytest.mark.asyncio
    async def test_sync_full_data_success(self, service, mock_fetcher, mock_mapper, mock_repository):
        """全データ同期の成功テスト"""
        # モックデータ
        mock_quotes_data = {
            date(2024, 1, 15): [
                {"Code": "1234", "Date": "2024-01-15", "Open": "1000"},
                {"Code": "5678", "Date": "2024-01-15", "Open": "2000"}
            ],
            date(2024, 1, 16): [
                {"Code": "1234", "Date": "2024-01-16", "Open": "1010"}
            ]
        }
        
        # モックの設定
        mock_fetcher.fetch_quotes_by_date_range.return_value = mock_quotes_data
        # 各日付で呼ばれるため、返り値を調整
        mock_repository.bulk_upsert.side_effect = [
            (2, 0, 0),  # 1月15日: 新規2件
            (1, 0, 0)   # 1月16日: 新規1件
        ]
        
        # 同期履歴オブジェクト
        sync_history = DailyQuotesSyncHistory()
        
        # テスト実行
        await service._sync_full_data(
            mock_fetcher,
            mock_repository,
            sync_history,
            date(2024, 1, 15),
            date(2024, 1, 16)
        )
        
        # 検証
        assert sync_history.total_records == 3
        assert sync_history.new_records == 3
        assert sync_history.updated_records == 0
        assert sync_history.skipped_records == 0
        
        mock_fetcher.fetch_quotes_by_date_range.assert_called_once_with(
            date(2024, 1, 15),
            date(2024, 1, 16)
        )
        assert mock_repository.bulk_upsert.call_count == 2
    
    @pytest.mark.asyncio
    async def test_sync_incremental_data_success(self, service, mock_fetcher, mock_mapper, mock_repository):
        """増分データ同期の成功テスト"""
        # モックデータ
        mock_quotes_data = [
            {"Code": "1234", "Date": "2024-01-15", "Open": "1000"},
            {"Code": "5678", "Date": "2024-01-15", "Open": "2000"}
        ]
        
        # モックの設定
        mock_fetcher.fetch_quotes_by_date.return_value = mock_quotes_data
        mock_repository.bulk_upsert.return_value = (2, 0, 0)
        
        # 同期履歴オブジェクト
        sync_history = DailyQuotesSyncHistory()
        
        # テスト実行
        await service._sync_incremental_data(
            mock_fetcher,
            mock_repository,
            sync_history,
            date(2024, 1, 15)
        )
        
        # 検証
        assert sync_history.total_records == 2
        assert sync_history.new_records == 2
        assert sync_history.updated_records == 0
        assert sync_history.skipped_records == 0
        
        mock_fetcher.fetch_quotes_by_date.assert_called_once_with(date(2024, 1, 15))
        mock_repository.bulk_upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_single_stock_data_success(self, service, mock_fetcher, mock_mapper, mock_repository):
        """特定銘柄同期の成功テスト"""
        # モックデータ
        mock_quotes_data = [
            {"Code": "1234", "Date": "2024-01-15", "Open": "1000"}
        ]
        specific_codes = ["1234", "5678"]
        
        # モックの設定
        mock_fetcher.fetch_quotes_by_date.return_value = mock_quotes_data
        mock_repository.bulk_upsert.return_value = (1, 0, 0)
        
        # 同期履歴オブジェクト
        sync_history = DailyQuotesSyncHistory()
        
        # テスト実行
        await service._sync_single_stock_data(
            mock_fetcher,
            mock_repository,
            sync_history,
            specific_codes,
            date(2024, 1, 15)
        )
        
        # 検証
        assert sync_history.target_companies == 2
        assert sync_history.total_records == 1
        assert sync_history.new_records == 1
        assert sync_history.updated_records == 0
        assert sync_history.skipped_records == 0
        
        mock_fetcher.fetch_quotes_by_date.assert_called_once_with(
            date(2024, 1, 15),
            specific_codes
        )
    
    @pytest.mark.asyncio
    async def test_sync_single_stock_data_no_codes(self, service, mock_fetcher, mock_repository):
        """特定銘柄同期（銘柄指定なし）"""
        sync_history = DailyQuotesSyncHistory()
        
        # テスト実行
        with pytest.raises(ValueError) as exc_info:
            await service._sync_single_stock_data(
                mock_fetcher,
                mock_repository,
                sync_history,
                None,  # specific_codes なし
                date(2024, 1, 15)
            )
        
        assert "specific_codes is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_sync_with_data_fetch_error(self, service, mock_fetcher, mock_repository):
        """データ取得エラー時のテスト"""
        # モックの設定
        mock_fetcher.fetch_quotes_by_date.side_effect = DataFetchError("API Error")
        
        sync_history = DailyQuotesSyncHistory()
        
        # テスト実行
        with pytest.raises(DataFetchError):
            await service._sync_incremental_data(
                mock_fetcher,
                mock_repository,
                sync_history,
                date(2024, 1, 15)
            )
    
    @pytest.mark.asyncio
    async def test_sync_with_rate_limit_error(self, service, mock_fetcher, mock_repository):
        """レート制限エラー時のテスト"""
        # モックの設定
        mock_fetcher.fetch_quotes_by_date.side_effect = RateLimitError(
            "Rate limit exceeded",
            retry_after=60
        )
        
        sync_history = DailyQuotesSyncHistory()
        
        # テスト実行
        with pytest.raises(RateLimitError):
            await service._sync_incremental_data(
                mock_fetcher,
                mock_repository,
                sync_history,
                date(2024, 1, 15)
            )
    
    @pytest.mark.asyncio
    async def test_get_history_model(self, service):
        """履歴モデルクラスの取得"""
        model = service.get_history_model()
        assert model == DailyQuotesSyncHistory
    
    @pytest.mark.asyncio
    @patch('app.services.daily_quotes_sync_service.async_session_maker')
    async def test_sync_daily_quotes_full_flow(self, mock_session_maker, service):
        """sync_daily_quotesの全体フローテスト"""
        # モックセッション
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        # _sync_full_dataをモック
        with patch.object(service, '_sync_full_data', new_callable=AsyncMock) as mock_sync_full:
            # ErrorHandlerをモック
            with patch('app.services.daily_quotes_sync_service.ErrorHandler.handle_sync_error'):
                result = await service.sync_daily_quotes(
                    data_source_id=1,
                    sync_type="full",
                    from_date=date(2024, 1, 1),
                    to_date=date(2024, 1, 31)
                )
        
        assert result.status == "completed"
        assert result.sync_type == "full"
        mock_sync_full.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_default_date_ranges(self, service, mock_fetcher, mock_repository):
        """デフォルトの日付範囲テスト"""
        # モックの設定
        mock_fetcher.fetch_quotes_by_date_range.return_value = {}
        
        sync_history = DailyQuotesSyncHistory()
        
        # from_date, to_date を指定しない
        with patch('app.services.daily_quotes_sync_service.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            await service._sync_full_data(
                mock_fetcher,
                mock_repository,
                sync_history,
                None,  # from_date
                None   # to_date
            )
        
        # デフォルト値の確認
        expected_from = date(2024, 1, 15) - timedelta(days=365)
        expected_to = date(2024, 1, 15) - timedelta(days=1)
        
        mock_fetcher.fetch_quotes_by_date_range.assert_called_once_with(
            expected_from,
            expected_to
        )