"""
株価データ同期サービスのテスト
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from app.services.daily_quotes_sync_service import DailyQuotesSyncService
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager, JQuantsDailyQuotesClient
from app.models.daily_quote import DailyQuote, DailyQuotesSyncHistory


class TestDailyQuotesSyncService:
    """株価データ同期サービスのテスト"""

    @pytest.fixture
    def mock_data_source_service(self):
        """モックデータソースサービス"""
        return Mock(spec=DataSourceService)

    @pytest.fixture
    def mock_jquants_client_manager(self):
        """モックJ-Quantsクライアント管理"""
        return Mock(spec=JQuantsClientManager)

    @pytest.fixture
    def mock_jquants_client(self):
        """モックJ-Quantsクライアント"""
        return Mock(spec=JQuantsDailyQuotesClient)

    @pytest.fixture
    def sync_service(self, mock_data_source_service, mock_jquants_client_manager):
        """同期サービスのインスタンス"""
        return DailyQuotesSyncService(
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_client_manager
        )

    @pytest.fixture
    def sample_jquants_data(self):
        """サンプルJ-Quantsデータ"""
        return [
            {
                "Date": "2024-12-26",
                "Code": "1234",
                "Open": 1000.0,
                "High": 1100.0,
                "Low": 950.0,
                "Close": 1050.0,
                "Volume": 1000000,
                "TurnoverValue": 1050000000,
                "AdjustmentFactor": 1.0,
                "AdjustmentOpen": 1000.0,
                "AdjustmentHigh": 1100.0,
                "AdjustmentLow": 950.0,
                "AdjustmentClose": 1050.0,
                "AdjustmentVolume": 1000000,
                "UpperLimit": False,
                "LowerLimit": False
            },
            {
                "Date": "2024-12-26",
                "Code": "5678",
                "Open": 2000.0,
                "High": 2200.0,
                "Low": 1900.0,
                "Close": 2100.0,
                "Volume": 2000000,
                "TurnoverValue": 4200000000,
                "AdjustmentFactor": 1.0,
                "UpperLimit": False,
                "LowerLimit": False
            }
        ]

    @pytest.mark.asyncio
    async def test_sync_incremental_data_success(
        self, sync_service, mock_jquants_client_manager, mock_jquants_client, sample_jquants_data
    ):
        """増分データ同期の成功テスト"""
        # クライアント取得をモック
        mock_jquants_client_manager.get_daily_quotes_client = AsyncMock(return_value=mock_jquants_client)
        mock_jquants_client.get_stock_prices_by_date = AsyncMock(return_value=sample_jquants_data)
        
        # データベースセッションをモック
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            # 同期履歴をモック
            mock_sync_history = Mock(spec=DailyQuotesSyncHistory)
            mock_sync_history.id = 1
            mock_sync_history.sync_type = "incremental"
            mock_sync_history.status = "completed"
            mock_sync_history.total_records = 2
            mock_sync_history.new_records = 2
            mock_sync_history.updated_records = 0
            mock_sync_history.skipped_records = 0
            
            with patch('app.services.daily_quotes_sync_service.DailyQuotesSyncHistory', return_value=mock_sync_history):
                # 既存レコードなし（新規作成）
                mock_session.execute.return_value.scalar_one_or_none.return_value = None
                
                # テスト実行
                result = await sync_service.sync_daily_quotes(
                    data_source_id=1,
                    sync_type="incremental",
                    target_date=date(2024, 12, 26)
                )
                
                # 結果検証
                assert result.sync_type == "incremental"
                assert result.status == "completed"
                assert result.total_records == 2
                assert result.new_records == 2
                assert result.updated_records == 0
                assert result.skipped_records == 0

    @pytest.mark.asyncio
    async def test_sync_full_data_success(
        self, sync_service, mock_jquants_client_manager, mock_jquants_client, sample_jquants_data
    ):
        """全データ同期の成功テスト"""
        mock_jquants_client_manager.get_daily_quotes_client = AsyncMock(return_value=mock_jquants_client)
        mock_jquants_client.get_stock_prices_by_date = AsyncMock(return_value=sample_jquants_data)
        
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            # テスト実行（1日分のみ）
            result = await sync_service.sync_daily_quotes(
                data_source_id=1,
                sync_type="full",
                from_date=date(2024, 12, 26),
                to_date=date(2024, 12, 26)
            )
            
            # 結果検証
            assert result.sync_type == "full"
            assert result.status == "completed"
            assert result.total_records == 2
            assert result.new_records == 2

    @pytest.mark.asyncio
    async def test_sync_single_stock_success(
        self, sync_service, mock_jquants_client_manager, mock_jquants_client, sample_jquants_data
    ):
        """特定銘柄同期の成功テスト"""
        mock_jquants_client_manager.get_daily_quotes_client = AsyncMock(return_value=mock_jquants_client)
        mock_jquants_client.get_stock_prices_by_date = AsyncMock(return_value=[sample_jquants_data[0]])
        
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            # テスト実行
            result = await sync_service.sync_daily_quotes(
                data_source_id=1,
                sync_type="single_stock",
                specific_codes=["1234"],
                target_date=date(2024, 12, 26)
            )
            
            # 結果検証
            assert result.sync_type == "single_stock"
            assert result.status == "completed"
            assert result.target_companies == 1
            assert result.total_records == 1
            assert result.new_records == 1

    @pytest.mark.asyncio
    async def test_sync_single_stock_no_codes_error(self, sync_service):
        """特定銘柄同期でコード未指定エラーテスト"""
        with pytest.raises(ValueError, match="specific_codes is required"):
            await sync_service.sync_daily_quotes(
                data_source_id=1,
                sync_type="single_stock"
            )

    @pytest.mark.asyncio
    async def test_sync_invalid_type_error(self, sync_service):
        """無効な同期タイプエラーテスト"""
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            with pytest.raises(ValueError, match="Unknown sync_type"):
                await sync_service.sync_daily_quotes(
                    data_source_id=1,
                    sync_type="invalid_type"
                )

    @pytest.mark.asyncio
    async def test_sync_api_error_handling(
        self, sync_service, mock_jquants_client_manager, mock_jquants_client
    ):
        """API エラーハンドリングのテスト"""
        mock_jquants_client_manager.get_daily_quotes_client = AsyncMock(return_value=mock_jquants_client)
        mock_jquants_client.get_stock_prices_by_date = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            # テスト実行
            with pytest.raises(Exception, match="API Error"):
                await sync_service.sync_daily_quotes(
                    data_source_id=1,
                    sync_type="incremental"
                )

    @pytest.mark.asyncio
    async def test_process_quotes_data_update_existing(
        self, sync_service, sample_jquants_data
    ):
        """既存レコード更新のテスト"""
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            # 既存レコードをモック
            existing_quote = Mock(spec=DailyQuote)
            mock_session.execute.return_value.scalar_one_or_none.return_value = existing_quote
            
            sync_history = Mock(spec=DailyQuotesSyncHistory)
            
            # テスト実行
            new_count, updated_count, skipped_count = await sync_service._process_quotes_data(
                mock_session, sample_jquants_data, sync_history
            )
            
            # 結果検証
            assert new_count == 0
            assert updated_count == 2
            assert skipped_count == 0

    def test_validate_quote_data_success(self, sync_service):
        """データ妥当性チェック成功テスト"""
        valid_data = {
            "Code": "1234",
            "Date": "2024-12-26",
            "Open": 1000.0,
            "High": 1100.0,
            "Low": 950.0,
            "Close": 1050.0
        }
        
        result = sync_service._validate_quote_data(valid_data)
        assert result is True

    def test_validate_quote_data_missing_required(self, sync_service):
        """必須フィールド不足での妥当性チェックテスト"""
        invalid_data = {
            "Date": "2024-12-26"
            # Code が不足
        }
        
        result = sync_service._validate_quote_data(invalid_data)
        assert result is False

    def test_validate_quote_data_invalid_date(self, sync_service):
        """無効な日付での妥当性チェックテスト"""
        invalid_data = {
            "Code": "1234",
            "Date": "invalid-date"
        }
        
        result = sync_service._validate_quote_data(invalid_data)
        assert result is False

    def test_validate_quote_data_invalid_ohlc(self, sync_service):
        """無効なOHLCでの妥当性チェックテスト"""
        invalid_data = {
            "Code": "1234",
            "Date": "2024-12-26",
            "Open": 1000.0,
            "High": 900.0,  # High < Open (無効)
            "Low": 950.0,
            "Close": 1050.0
        }
        
        result = sync_service._validate_quote_data(invalid_data)
        assert result is False

    def test_create_daily_quote(self, sync_service):
        """DailyQuote作成テスト"""
        quote_data = {
            "Code": "1234",
            "Date": "2024-12-26",
            "Open": 1000.0,
            "High": 1100.0,
            "Low": 950.0,
            "Close": 1050.0,
            "Volume": 1000000,
            "TurnoverValue": 1050000000,
            "AdjustmentFactor": 1.2,
            "UpperLimit": False,
            "LowerLimit": False
        }
        
        quote = sync_service._create_daily_quote(quote_data)
        
        assert quote.code == "1234"
        assert quote.trade_date == date(2024, 12, 26)
        assert quote.open_price == Decimal("1000.0")
        assert quote.high_price == Decimal("1100.0")
        assert quote.low_price == Decimal("950.0")
        assert quote.close_price == Decimal("1050.0")
        assert quote.volume == 1000000
        assert quote.adjustment_factor == Decimal("1.2")
        assert quote.upper_limit_flag is False

    def test_update_daily_quote(self, sync_service):
        """DailyQuote更新テスト"""
        existing_quote = Mock(spec=DailyQuote)
        
        quote_data = {
            "Open": 1100.0,
            "High": 1200.0,
            "Low": 1000.0,
            "Close": 1150.0,
            "Volume": 1500000,
            "UpperLimit": True
        }
        
        sync_service._update_daily_quote(existing_quote, quote_data)
        
        # 更新が呼ばれたことを確認
        assert existing_quote.open_price == Decimal("1100.0")
        assert existing_quote.high_price == Decimal("1200.0")
        assert existing_quote.volume == 1500000
        assert existing_quote.upper_limit_flag is True

    def test_safe_decimal_conversion(self, sync_service):
        """安全なDecimal変換テスト"""
        # 正常値
        assert sync_service._safe_decimal("1000.50") == Decimal("1000.50")
        assert sync_service._safe_decimal(1000.50) == Decimal("1000.50")
        
        # None値
        assert sync_service._safe_decimal(None) is None
        assert sync_service._safe_decimal("") is None
        
        # 無効値
        assert sync_service._safe_decimal("invalid") is None

    def test_safe_int_conversion(self, sync_service):
        """安全なint変換テスト"""
        # 正常値
        assert sync_service._safe_int("1000") == 1000
        assert sync_service._safe_int(1000.5) == 1000
        
        # None値
        assert sync_service._safe_int(None) is None
        assert sync_service._safe_int("") is None
        
        # 無効値
        assert sync_service._safe_int("invalid") is None

    def test_safe_bool_conversion(self, sync_service):
        """安全なbool変換テスト"""
        # True値
        assert sync_service._safe_bool(True) is True
        assert sync_service._safe_bool("true") is True
        assert sync_service._safe_bool("1") is True
        assert sync_service._safe_bool(1) is True
        
        # False値
        assert sync_service._safe_bool(False) is False
        assert sync_service._safe_bool("false") is False
        assert sync_service._safe_bool("0") is False
        assert sync_service._safe_bool(0) is False
        assert sync_service._safe_bool(None) is False

    @pytest.mark.asyncio
    async def test_get_sync_history(self, sync_service):
        """同期履歴取得テスト"""
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            # サンプル履歴データ
            sample_histories = [Mock(spec=DailyQuotesSyncHistory) for _ in range(3)]
            mock_session.execute.return_value.scalars.return_value.all.return_value = sample_histories
            
            # テスト実行
            result = await sync_service.get_sync_history(limit=10, offset=0)
            
            # 結果検証
            assert len(result) == 3
            assert all(isinstance(h, Mock) for h in result)

    @pytest.mark.asyncio
    async def test_get_sync_history_with_status_filter(self, sync_service):
        """ステータスフィルタ付き同期履歴取得テスト"""
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            sample_histories = [Mock(spec=DailyQuotesSyncHistory)]
            mock_session.execute.return_value.scalars.return_value.all.return_value = sample_histories
            
            # テスト実行
            result = await sync_service.get_sync_history(status="failed")
            
            # 結果検証
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_sync_status(self, sync_service):
        """同期ステータス取得テスト"""
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            sample_history = Mock(spec=DailyQuotesSyncHistory)
            mock_session.execute.return_value.scalar_one_or_none.return_value = sample_history
            
            # テスト実行
            result = await sync_service.get_sync_status(sync_id=1)
            
            # 結果検証
            assert result == sample_history

    @pytest.mark.asyncio
    async def test_get_sync_status_not_found(self, sync_service):
        """同期ステータス取得（見つからない場合）テスト"""
        with patch('app.services.daily_quotes_sync_service.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            # テスト実行
            result = await sync_service.get_sync_status(sync_id=999)
            
            # 結果検証
            assert result is None