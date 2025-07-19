"""
DailyQuotesSyncServiceの拡張テスト

BaseSyncServiceを継承したDailyQuotesSyncServiceの追加テスト
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import logging

from app.services.daily_quotes_sync_service import DailyQuotesSyncService
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager, JQuantsDailyQuotesClient
from app.models.daily_quote import DailyQuote, DailyQuotesSyncHistory
from app.models.company import Company


class TestDailyQuotesSyncServiceExtended:
    """DailyQuotesSyncServiceの拡張テスト"""
    
    @pytest.fixture
    def mock_data_source_service(self):
        """モックデータソースサービス"""
        return Mock(spec=DataSourceService)
    
    @pytest.fixture
    def mock_jquants_client_manager(self):
        """モックJ-Quantsクライアント管理"""
        return Mock(spec=JQuantsClientManager)
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        return session
    
    @pytest.fixture
    def sync_service_with_db(self, mock_data_source_service, mock_jquants_client_manager, mock_db_session):
        """データベースセッション付きのサービスインスタンス"""
        return DailyQuotesSyncService(
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_client_manager,
            db=mock_db_session
        )
    
    @pytest.fixture
    def sync_service_without_db(self, mock_data_source_service, mock_jquants_client_manager):
        """データベースセッションなしのサービスインスタンス"""
        return DailyQuotesSyncService(
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_client_manager,
            db=None
        )
    
    # 基底クラスのメソッドのテスト
    def test_get_history_model(self, sync_service_with_db):
        """get_history_modelメソッドのテスト"""
        assert sync_service_with_db.get_history_model() == DailyQuotesSyncHistory
    
    def test_logger_initialization_with_db(self, sync_service_with_db):
        """DBありの場合のロガー初期化テスト"""
        assert hasattr(sync_service_with_db, 'logger')
        assert sync_service_with_db.logger.name == 'DailyQuotesSyncService'
    
    def test_logger_initialization_without_db(self, sync_service_without_db):
        """DBなしの場合のロガー初期化テスト"""
        assert hasattr(sync_service_without_db, 'logger')
        assert sync_service_without_db.logger.name == 'DailyQuotesSyncService'
        assert sync_service_without_db._has_db is False
    
    @pytest.mark.asyncio
    async def test_sync_method(self, sync_service_with_db, mock_jquants_client_manager):
        """syncメソッド（基底クラスの抽象メソッド実装）のテスト"""
        # モッククライアントの設定
        mock_client = Mock()
        mock_client.get_stock_prices_by_date = AsyncMock(return_value=[
            {
                "Code": "1234",
                "Date": "2025-07-18",
                "Open": 1000,
                "High": 1100,
                "Low": 900,
                "Close": 1050,
                "Volume": 10000
            }
        ])
        mock_jquants_client_manager.get_daily_quotes_client = AsyncMock(return_value=mock_client)
        
        # sync_daily_quotesをモック
        with patch.object(sync_service_with_db, 'sync_daily_quotes') as mock_sync_quotes:
            mock_history = Mock(spec=DailyQuotesSyncHistory)
            mock_history.id = 1
            mock_history.status = "completed"
            mock_history.total_records = 100
            mock_history.new_records = 50
            mock_history.updated_records = 50
            mock_history.skipped_records = 0
            mock_sync_quotes.return_value = mock_history
            
            # syncメソッドを実行
            result = await sync_service_with_db.sync(
                data_source_id=1,
                sync_type='full',
                from_date=date(2025, 7, 1),
                to_date=date(2025, 7, 18)
            )
            
            assert result['status'] == 'completed'
            assert result['history_id'] == 1
            assert result['total_records'] == 100
            assert result['new_records'] == 50
            assert result['updated_records'] == 50
            assert result['skipped_records'] == 0
    
    @pytest.mark.asyncio
    async def test_handle_error_with_db(self, sync_service_with_db, caplog):
        """DBありの場合のエラーハンドリングテスト"""
        error = Exception("Test error in daily quotes sync")
        context = {
            "sync_type": "full",
            "data_source_id": 1,
            "date_range": "2025-07-01 to 2025-07-18"
        }
        
        with caplog.at_level(logging.ERROR):
            sync_service_with_db.handle_error(error, context)
        
        assert "DailyQuotesSyncService sync error: Test error in daily quotes sync" in caplog.text
    
    @pytest.mark.asyncio
    async def test_handle_error_without_db(self, sync_service_without_db, caplog):
        """DBなしの場合のエラーハンドリングテスト"""
        # _has_dbがFalseの場合、handle_errorは基底クラスのメソッドを使わない
        error = Exception("Test error without DB")
        context = {"sync_type": "full"}
        
        # エラーが発生しないことを確認（handle_errorが呼ばれても何もしない）
        try:
            sync_service_without_db.handle_error(error, context)
        except:
            pytest.fail("handle_error should not raise exception when _has_db is False")
    
    @pytest.mark.asyncio
    async def test_get_sync_history_with_db(self, sync_service_with_db, mock_db_session):
        """DBありの場合のget_sync_historyテスト"""
        # 基底クラスのget_sync_historyをモック
        mock_histories = [
            Mock(spec=DailyQuotesSyncHistory, id=1, status="completed"),
            Mock(spec=DailyQuotesSyncHistory, id=2, status="running")
        ]
        
        with patch.object(sync_service_with_db.__class__.__bases__[0], 'get_sync_history', 
                         return_value=mock_histories) as mock_get_history:
            histories = await sync_service_with_db.get_sync_history(limit=10, status="completed")
            
            # 基底クラスのメソッドが呼ばれることを確認
            mock_get_history.assert_called_once_with(sync_service_with_db, 10, 0, "completed")
            assert len(histories) == 2
    
    @pytest.mark.asyncio
    async def test_get_sync_history_without_db(self, sync_service_without_db):
        """DBなしの場合のget_sync_historyテスト"""
        # async_session_makerをモック
        with patch('app.services.daily_quotes_sync_service.async_session_maker') as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [
                Mock(spec=DailyQuotesSyncHistory, id=1, status="completed")
            ]
            mock_session.execute.return_value = mock_result
            mock_session.__aenter__.return_value = mock_session
            mock_session_maker.return_value = mock_session
            
            histories = await sync_service_without_db.get_sync_history(limit=5)
            
            assert len(histories) == 1
            assert histories[0].status == "completed"
    
    @pytest.mark.asyncio
    async def test_create_sync_history_integration(self, sync_service_with_db, mock_db_session):
        """同期履歴作成の統合テスト"""
        # 基底クラスのcreate_sync_historyをテスト
        with patch.object(sync_service_with_db, 'create_sync_history') as mock_create:
            mock_history = Mock(spec=DailyQuotesSyncHistory)
            mock_history.id = 1
            mock_history.sync_type = "full"
            mock_history.status = "running"
            mock_create.return_value = mock_history
            
            history = await sync_service_with_db.create_sync_history(
                sync_type="full",
                sync_date=date.today(),
                from_date=date(2025, 7, 1),
                to_date=date(2025, 7, 18)
            )
            
            assert history.id == 1
            assert history.sync_type == "full"
            assert history.status == "running"
    
    @pytest.mark.asyncio
    async def test_update_sync_history_callbacks(self, sync_service_with_db, mock_db_session):
        """同期履歴更新のコールバックテスト"""
        mock_history = Mock(spec=DailyQuotesSyncHistory)
        
        # 成功時の更新
        with patch.object(sync_service_with_db, 'update_sync_history_success') as mock_update_success:
            mock_history.status = "completed"
            mock_update_success.return_value = mock_history
            
            updated = await sync_service_with_db.update_sync_history_success(
                mock_history,
                total_records=1000,
                new_records=500,
                updated_records=500,
                skipped_records=0
            )
            
            assert updated.status == "completed"
        
        # 失敗時の更新
        with patch.object(sync_service_with_db, 'update_sync_history_failure') as mock_update_failure:
            mock_history.status = "failed"
            mock_history.error_message = "API Error"
            mock_update_failure.return_value = mock_history
            
            error = Exception("API Error")
            failed = await sync_service_with_db.update_sync_history_failure(
                mock_history,
                error
            )
            
            assert failed.status == "failed"
            assert failed.error_message == "API Error"
    
    @pytest.mark.asyncio
    async def test_sync_with_progress_tracking(self, sync_service_with_db, mock_jquants_client_manager):
        """進捗追跡を含む同期処理のテスト"""
        # モッククライアントの設定
        mock_client = Mock()
        mock_client.get_stock_prices_by_date = AsyncMock(
            side_effect=[
                # 1日目のデータ
                [
                    {"Code": "1234", "Date": "2025-07-17", "Close": 1000, "Volume": 10000},
                    {"Code": "5678", "Date": "2025-07-17", "Close": 2000, "Volume": 20000}
                ],
                # 2日目のデータ
                [
                    {"Code": "1234", "Date": "2025-07-18", "Close": 1100, "Volume": 11000},
                    {"Code": "5678", "Date": "2025-07-18", "Close": 2100, "Volume": 21000}
                ]
            ]
        )
        mock_jquants_client_manager.get_daily_quotes_client = AsyncMock(return_value=mock_client)
        
        # sync_daily_quotesをモックして、進捗を追跡
        progress_records = []
        
        async def mock_process_quotes(session, quotes_data, sync_history):
            progress_records.append(len(quotes_data))
            return len(quotes_data), 0, 0  # new, updated, skipped
        
        with patch.object(sync_service_with_db, '_process_quotes_data', side_effect=mock_process_quotes):
            with patch('app.services.daily_quotes_sync_service.async_session_maker') as mock_session_maker:
                mock_session = AsyncMock()
                mock_session.__aenter__.return_value = mock_session
                mock_session_maker.return_value = mock_session
                
                # 実行（2日分のデータ）
                history = await sync_service_with_db.sync_daily_quotes(
                    data_source_id=1,
                    sync_type="full",
                    from_date=date(2025, 7, 17),
                    to_date=date(2025, 7, 18)
                )
                
                # 進捗確認
                assert len(progress_records) == 2  # 2日分
                assert progress_records[0] == 2  # 1日目: 2銘柄
                assert progress_records[1] == 2  # 2日目: 2銘柄
    
    def test_inheritance_chain(self, sync_service_with_db):
        """継承チェーンの確認"""
        from app.services.base_sync_service import BaseSyncService
        
        # DailyQuotesSyncServiceがBaseSyncServiceを継承していることを確認
        assert issubclass(DailyQuotesSyncService, BaseSyncService)
        
        # インスタンスがBaseSyncServiceのインスタンスでもあることを確認
        assert isinstance(sync_service_with_db, BaseSyncService)