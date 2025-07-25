"""
CompanySyncServiceの統合テスト
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch

from app.services.company_sync_service import CompanySyncService
from app.models.company import Company, CompanySyncHistory


@pytest.mark.asyncio
class TestCompanySyncServiceIntegration:
    """CompanySyncServiceの統合テスト"""
    
    @pytest.fixture
    async def mock_db(self):
        """モックのデータベースセッション"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.add = Mock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db
    
    @pytest.fixture
    async def mock_data_source_service(self):
        """モックのデータソースサービス"""
        service = Mock()
        service.get_jquants_source = AsyncMock()
        
        # J-Quantsデータソースを返す
        mock_source = Mock()
        mock_source.id = 1
        service.get_jquants_source.return_value = mock_source
        
        return service
    
    @pytest.fixture
    async def mock_jquants_client_manager(self):
        """モックのJQuantsクライアントマネージャー"""
        manager = Mock()
        manager.get_client = AsyncMock()
        
        # モッククライアント
        client = Mock()
        client.get_all_listed_companies = AsyncMock()
        client.get_all_listed_companies.return_value = [
            {
                "Code": "1234",
                "CompanyName": "テスト株式会社",
                "CompanyNameEnglish": "Test Corp",
                "Sector17Code": "1"
            },
            {
                "Code": "5678",
                "CompanyName": "サンプル株式会社",
                "CompanyNameEnglish": "Sample Corp",
                "Sector17Code": "2"
            }
        ]
        
        manager.get_client.return_value = client
        return manager
    
    @pytest.fixture
    async def service(self, mock_db, mock_data_source_service, mock_jquants_client_manager):
        """テスト用のCompanySyncServiceインスタンス"""
        return CompanySyncService(
            db=mock_db,
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_client_manager
        )
    
    @pytest.fixture
    
    async def test_sync_companies_compatibility(self, service, mock_db):
        """sync_companiesメソッドの互換性テスト"""
        # モックの設定
        mock_history = Mock(spec=CompanySyncHistory)
        mock_history.id = 1
        mock_history.status = "completed"
        mock_history.total_companies = 2
        mock_history.new_companies = 2
        mock_history.updated_companies = 0
        
        # create_sync_historyのモック
        service.create_sync_history = AsyncMock(return_value=mock_history)
        service.update_sync_history_success = AsyncMock(return_value=mock_history)
        
        # 実行
        result = await service_v2.sync_companies(
            data_source_id=1,
            sync_type="full",
            sync_date=date.today(),
            execution_type="manual"
        )
        
        # 検証
        assert result == mock_history
        assert service_v2.create_sync_history.called
        assert service_v2.update_sync_history_success.called
    
    async def test_sync_method_compatibility(self, service_v2, mock_db):
        """syncメソッドの互換性テスト"""
        # モックの設定
        mock_history = Mock(spec=CompanySyncHistory)
        mock_history.id = 1
        mock_history.status = "completed"
        mock_history.total_companies = 2
        mock_history.new_companies = 2
        mock_history.updated_companies = 0
        
        service.sync_companies = AsyncMock(return_value=mock_history)
        
        # 実行
        result = await service_v2.sync(
            data_source_id=1,
            sync_type="full"
        )
        
        # 検証
        assert result["status"] == "completed"
        assert result["history_id"] == 1
        assert result["total_companies"] == 2
        assert result["new_companies"] == 2
        assert result["updated_companies"] == 0
    
    async def test_sync_all_companies_simple_compatibility(self, service_v2):
        """sync_all_companies_simpleメソッドの互換性テスト"""
        # 実行
        result = await service_v2.sync_all_companies_simple()
        
        # 検証
        assert result["status"] == "success"
        assert result["sync_count"] == 2
        assert "duration" in result
        assert "executed_at" in result
    
    async def test_error_handling_compatibility(self, service_v2, mock_db):
        """エラーハンドリングの互換性テスト"""
        # モックの設定
        mock_history = Mock(spec=CompanySyncHistory)
        mock_history.id = 1
        
        service.create_sync_history = AsyncMock(return_value=mock_history)
        service.update_sync_history_failure = AsyncMock(return_value=mock_history)
        
        # フェッチャーがエラーを発生させるように設定
        service._initialize_fetcher = Mock()
        mock_fetcher = Mock()
        mock_fetcher.fetch_all_companies = AsyncMock(side_effect=Exception("API Error"))
        service._initialize_fetcher.return_value = mock_fetcher
        
        # ErrorHandlerのモック
        with patch('app.services.company_sync_service.ErrorHandler.handle_sync_error') as mock_error_handler:
            mock_error_handler.return_value = {"error": "API Error"}
            
            # 実行と検証
            with pytest.raises(Exception) as exc_info:
                await service_v2.sync_companies(
                    data_source_id=1,
                    sync_type="full"
                )
            
            assert str(exc_info.value) == "API Error"
            assert service.update_sync_history_failure.called
    
    async def test_get_sync_history_with_count_compatibility(self, service, mock_db):
        """get_sync_history_with_countメソッドの互換性テスト"""
        # モックの設定
        mock_histories = [Mock(spec=CompanySyncHistory) for _ in range(3)]
        service.get_sync_history = AsyncMock(return_value=mock_histories)
        
        # countクエリの結果
        mock_result = Mock()
        mock_result.scalar.return_value = 10
        mock_db.execute.return_value = mock_result
        
        # 実行
        histories, total = await service.get_sync_history_with_count(
            limit=3,
            offset=0,
            status="completed"
        )
        
        # 検証
        assert len(histories) == 3
        assert total == 10
    
