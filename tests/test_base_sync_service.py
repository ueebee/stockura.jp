"""
BaseSyncServiceの単体テスト

抽象基底クラスのテストとして、具象クラスを作成してテストを実施
"""

import pytest

# 単体テストマーカーを追加
pytestmark = pytest.mark.unit
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.base_sync_service import BaseSyncService


# テスト用の履歴モデル
class MockSyncHistory:
    """テスト用の同期履歴モデル"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.sync_type = kwargs.get('sync_type', 'test')
        self.status = kwargs.get('status', 'running')
        self.started_at = kwargs.get('started_at', datetime.utcnow())
        self.completed_at = kwargs.get('completed_at', None)
        self.error_message = kwargs.get('error_message', None)


# テスト用の具象クラス
class MockSyncService(BaseSyncService[MockSyncHistory]):
    """テスト用の同期サービス"""
    
    def get_history_model(self) -> type:
        return MockSyncHistory
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """同期処理のモック実装"""
        if kwargs.get('should_fail', False):
            raise Exception("Test sync failure")
        
        return {
            "status": "success",
            "items_processed": kwargs.get('items_count', 10)
        }


class TestBaseSyncService:
    """BaseSyncServiceのテストクラス"""
    
    @pytest.fixture
    def mock_db_session(self):
        """モックのデータベースセッション"""
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def service(self, mock_db_session):
        """テスト用サービスインスタンス"""
        return MockSyncService(mock_db_session)
    
    def test_initialization(self, service):
        """初期化のテスト"""
        assert service.db is not None
        assert isinstance(service.logger, logging.Logger)
        assert service.logger.name == 'MockSyncService'
    
    def test_get_history_model(self, service):
        """履歴モデルの取得テスト"""
        assert service.get_history_model() == MockSyncHistory
    
    @pytest.mark.asyncio
    async def test_sync_success(self, service):
        """同期処理成功のテスト"""
        result = await service.sync(items_count=20)
        
        assert result["status"] == "success"
        assert result["items_processed"] == 20
    
    @pytest.mark.asyncio
    async def test_sync_failure(self, service):
        """同期処理失敗のテスト"""
        with pytest.raises(Exception) as exc_info:
            await service.sync(should_fail=True)
        
        assert str(exc_info.value) == "Test sync failure"
    
    @pytest.mark.asyncio
    async def test_create_sync_history(self, service, mock_db_session):
        """同期履歴作成のテスト"""
        # create_sync_historyを呼び出し
        history = await service.create_sync_history(
            sync_type="test_sync",
            additional_field="test_value"
        )
        
        # データベース操作の確認
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called
        
        # 履歴オブジェクトの確認
        assert history.sync_type == "test_sync"
        assert history.status == "running"
        assert history.started_at is not None
    
    @pytest.mark.asyncio
    async def test_update_sync_history_success(self, service, mock_db_session):
        """同期成功時の履歴更新テスト"""
        history = MockSyncHistory()
        
        updated_history = await service.update_sync_history_success(
            history,
            total_items=100,
            processed_items=100
        )
        
        assert updated_history.status == "completed"
        assert updated_history.completed_at is not None
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called
    
    @pytest.mark.asyncio
    async def test_update_sync_history_failure(self, service, mock_db_session):
        """同期失敗時の履歴更新テスト"""
        history = MockSyncHistory()
        error = Exception("Test error")
        
        updated_history = await service.update_sync_history_failure(
            history,
            error
        )
        
        assert updated_history.status == "failed"
        assert updated_history.completed_at is not None
        assert updated_history.error_message == "Test error"
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called
    
    # @pytest.mark.asyncio
    # async def test_get_sync_history(self, service, mock_db_session):
    #     """同期履歴取得のテスト"""
    #     # モックの履歴データ
    #     mock_histories = [
    #         MockSyncHistory(id=1, status="completed"),
    #         MockSyncHistory(id=2, status="completed"),
    #         MockSyncHistory(id=3, status="failed")
    #     ]
    #     
    #     # executeの結果をモック
    #     mock_result = Mock()
    #     mock_result.scalars.return_value.all.return_value = mock_histories[:2]
    #     mock_db_session.execute.return_value = mock_result
    #     
    #     # 履歴取得
    #     histories = await service.get_sync_history(limit=2, status="completed")
    #     
    #     assert len(histories) == 2
    #     assert all(h.status == "completed" for h in histories)
    #     assert mock_db_session.execute.called
    
    # @pytest.mark.asyncio
    # async def test_get_latest_sync_status(self, service, mock_db_session):
    #     """最新同期ステータス取得のテスト"""
    #     # モックの最新履歴
    #     latest_history = MockSyncHistory(
    #         id=10,
    #         status="completed",
    #         started_at=datetime.utcnow()
    #     )
    #     
    #     # executeの結果をモック
    #     mock_result = Mock()
    #     mock_result.scalar_one_or_none.return_value = latest_history
    #     mock_db_session.execute.return_value = mock_result
    #     
    #     # 最新ステータス取得
    #     latest = await service.get_latest_sync_status()
    #     
    #     assert latest is not None
    #     assert latest.id == 10
    #     assert latest.status == "completed"
    #     assert mock_db_session.execute.called
    
    def test_handle_error(self, service, caplog):
        """エラーハンドリングのテスト"""
        error = Exception("Test error message")
        context = {
            "sync_type": "test",
            "data_source_id": 1
        }
        
        # ログレベルを設定
        with caplog.at_level(logging.ERROR):
            service.handle_error(error, context)
        
        # ログメッセージの確認
        assert "MockSyncService sync error: Test error message" in caplog.text
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
    
    # @pytest.mark.asyncio
    # async def test_get_sync_statistics(self, service, mock_db_session):
    #     """同期統計情報取得のテスト"""
    #     # 総件数のモック
    #     mock_db_session.scalar = AsyncMock(return_value=100)
    #     
    #     # ステータス別統計のモック
    #     mock_result = Mock()
    #     mock_result.all.return_value = [
    #         ("completed", 80),
    #         ("failed", 15),
    #         ("running", 5)
    #     ]
    #     mock_db_session.execute.return_value = mock_result
    #     
    #     # 最新履歴のモック
    #     with patch.object(service, 'get_latest_sync_status') as mock_get_latest:
    #         latest_history = MockSyncHistory(
    #             status="completed",
    #             started_at=datetime.utcnow(),
    #             completed_at=datetime.utcnow()
    #         )
    #         mock_get_latest.return_value = latest_history
    #         
    #         # 統計情報取得
    #         stats = await service.get_sync_statistics()
    #     
    #     assert stats["total_syncs"] == 100
    #     assert stats["status_breakdown"]["completed"] == 80
    #     assert stats["status_breakdown"]["failed"] == 15
    #     assert stats["status_breakdown"]["running"] == 5
    #     assert stats["latest_sync"]["status"] == "completed"
    #     assert stats["latest_sync"]["started_at"] is not None
    #     assert stats["latest_sync"]["completed_at"] is not None
    
    # @pytest.mark.asyncio
    # async def test_get_sync_statistics_no_history(self, service, mock_db_session):
    #     """履歴がない場合の統計情報取得テスト"""
    #     # 総件数0のモック
    #     mock_db_session.scalar = AsyncMock(return_value=0)
    #     
    #     # 空のステータス統計
    #     mock_result = Mock()
    #     mock_result.all.return_value = []
    #     mock_db_session.execute.return_value = mock_result
    #     
    #     # 最新履歴なし
    #     with patch.object(service, 'get_latest_sync_status') as mock_get_latest:
    #         mock_get_latest.return_value = None
    #         
    #         # 統計情報取得
    #         stats = await service.get_sync_statistics()
    #     
    #     assert stats["total_syncs"] == 0
    #     assert stats["status_breakdown"] == {}
    #     assert stats["latest_sync"] is None