"""
Celeryタスク統合テスト

実際の問題:
- 非同期処理のイベントループ管理
- StrategyRegistryの初期化タイミング
- タスクの進捗更新とステータス管理
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
import asyncio

from celery import Task
from celery.result import AsyncResult

from app.tasks.company_tasks import (
    sync_companies_task,
    sync_listed_companies,
    sync_companies_with_retry,
    test_jquants_connection
)
from app.models.company import CompanySyncHistory
from app.models.api_endpoint import APIEndpoint, APIEndpointExecutionLog


class TestCeleryTasksIntegration:
    """Celeryタスクの統合テスト"""
    
    @pytest.fixture
    def mock_celery_task(self):
        """Celeryタスクのモック"""
        task = MagicMock(spec=Task)
        task.request = Mock()
        task.request.id = "test-task-id"
        task.request.retries = 0
        task.update_state = Mock()
        return task
    
    @pytest.fixture
    def mock_sync_history(self):
        """同期履歴のモック"""
        history = Mock(spec=CompanySyncHistory)
        history.id = 1
        history.sync_date = date.today()
        history.sync_type = "full"
        history.total_companies = 4417
        history.new_companies = 4417
        history.updated_companies = 0
        history.deleted_companies = 0
        history.started_at = datetime.utcnow()
        history.completed_at = datetime.utcnow()
        return history
    
    @patch('app.tasks.company_tasks.async_session_maker')
    @patch('app.tasks.company_tasks.asyncio.new_event_loop')
    def test_sync_companies_task_event_loop_management(self, mock_new_loop, mock_session_maker, mock_celery_task):
        """
        イベントループ管理が正しく行われることを確認
        これが実際に問題となった箇所
        """
        # イベントループのモック
        mock_loop = MagicMock()
        mock_new_loop.return_value = mock_loop
        
        # 非同期セッションのモック
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        # sync_companiesタスクを実行
        with patch('app.tasks.company_tasks.DataSourceService') as mock_ds_service:
            with patch('app.tasks.company_tasks.JQuantsClientManager') as mock_client_manager:
                with patch('app.tasks.company_tasks.CompanySyncService') as mock_sync_service:
                    # モックの設定
                    mock_sync_instance = AsyncMock()
                    mock_sync_instance.sync_companies = AsyncMock(return_value=Mock(
                        id=1,
                        sync_date=date.today(),
                        sync_type="full",
                        total_companies=100,
                        new_companies=100,
                        updated_companies=0,
                        deleted_companies=0,
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    ))
                    mock_sync_service.return_value = mock_sync_instance
                    
                    # タスクをバインド
                    sync_companies_task.bind(mock_celery_task)
                    
                    # タスク実行
                    result = sync_companies_task.run(
                        mock_celery_task,
                        data_source_id=1,
                        sync_date=None,
                        sync_type="full",
                        execution_type="manual"
                    )
                    
                    # イベントループが正しく作成・使用・クローズされたことを確認
                    mock_new_loop.assert_called_once()
                    mock_loop.run_until_complete.assert_called()
                    mock_loop.close.assert_called_once()
                    
                    # 結果の確認
                    assert result["status"] == "success"
                    assert result["total_companies"] == 100
    
    @patch('app.tasks.company_tasks.SessionLocal')
    @patch('app.tasks.company_tasks.asyncio.new_event_loop')
    def test_sync_listed_companies_progress_updates(self, mock_new_loop, mock_session_local, mock_celery_task):
        """
        sync_listed_companiesタスクの進捗更新が正しく行われることを確認
        """
        # データベースセッションのモック
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        
        # エンドポイントのモック
        mock_endpoint = Mock(spec=APIEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.data_type = "listed_companies"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_endpoint
        
        # イベントループのモック
        mock_loop = MagicMock()
        mock_new_loop.return_value = mock_loop
        
        # 非同期処理の結果
        async_result = {
            "status": "success",
            "sync_count": 4417,
            "duration": 5.5,
            "executed_at": datetime.utcnow()
        }
        mock_loop.run_until_complete.return_value = async_result
        
        # タスクをバインド
        sync_listed_companies.bind(mock_celery_task)
        
        # タスク実行
        result = sync_listed_companies.run(mock_celery_task, execution_type="manual")
        
        # 進捗更新が呼ばれたことを確認
        assert mock_celery_task.update_state.call_count >= 2
        
        # 最初の進捗更新
        first_update = mock_celery_task.update_state.call_args_list[0]
        assert first_update[1]["state"] == "PROGRESS"
        assert "message" in first_update[1]["meta"]
        
        # 実行ログが作成されたことを確認
        assert mock_db.add.called
        execution_log = mock_db.add.call_args[0][0]
        assert isinstance(execution_log, APIEndpointExecutionLog)
        assert execution_log.execution_type == "manual"
        assert execution_log.success is True
        assert execution_log.data_count == 4417
    
    @patch('app.tasks.company_tasks.async_session_maker')
    def test_test_jquants_connection_with_strategy_registry(self, mock_session_maker, mock_celery_task):
        """
        J-Quants接続テストでStrategyRegistryが正しく使用されることを確認
        """
        # 非同期セッションのモック
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        with patch('app.tasks.company_tasks.DataSourceService') as mock_ds_service:
            with patch('app.tasks.company_tasks.JQuantsClientManager') as mock_client_manager:
                # JQuantsクライアントのモック
                mock_client = AsyncMock()
                mock_client.test_connection = AsyncMock(return_value=True)
                
                mock_manager_instance = AsyncMock()
                mock_manager_instance.get_client = AsyncMock(return_value=mock_client)
                mock_client_manager.return_value = mock_manager_instance
                
                # イベントループのモック
                with patch('app.tasks.company_tasks.asyncio.new_event_loop') as mock_new_loop:
                    mock_loop = MagicMock()
                    mock_new_loop.return_value = mock_loop
                    mock_loop.run_until_complete.return_value = {
                        "status": "success",
                        "data_source_id": 1,
                        "connected": True,
                        "tested_at": datetime.utcnow().isoformat(),
                        "message": "J-Quants API connection test completed"
                    }
                    
                    # タスクをバインド
                    test_jquants_connection.bind(mock_celery_task)
                    
                    # タスク実行
                    result = test_jquants_connection.run(mock_celery_task, data_source_id=1)
                    
                    # 結果の確認
                    assert result["status"] == "success"
                    assert result["connected"] is True
    
    def test_sync_companies_with_retry_error_handling(self, mock_celery_task):
        """
        リトライ機能付きタスクのエラーハンドリングテスト
        """
        # sync_companies_taskがエラーを返すようにモック
        with patch('app.tasks.company_tasks.sync_companies_task.delay') as mock_delay:
            mock_result = Mock()
            mock_result.get.side_effect = Exception("Connection error")
            mock_delay.return_value = mock_result
            
            # タスクをバインド
            sync_companies_with_retry.bind(mock_celery_task)
            
            # エラーが発生し、リトライが設定されることを確認
            with pytest.raises(Exception) as exc_info:
                sync_companies_with_retry.run(
                    mock_celery_task,
                    data_source_id=1,
                    sync_date=None,
                    sync_type="full"
                )
            
            # retryメソッドが呼ばれたことを確認
            assert mock_celery_task.retry.called
            retry_call = mock_celery_task.retry.call_args
            assert retry_call[1]["countdown"] == 60  # 最初のリトライは60秒後
    
    @patch('app.tasks.company_tasks.import_string')
    def test_celery_imports_strategies_on_worker_start(self, mock_import_string):
        """
        Celeryワーカー起動時にstrategiesがインポートされることを確認
        """
        # celery_appをインポート
        from app.core.celery_app import celery_app, setup_worker
        
        # ワーカー起動時の処理を実行
        setup_worker(sender=None)
        
        # StrategyRegistryが利用可能であることを確認
        from app.services.auth import StrategyRegistry
        assert "jquants" in StrategyRegistry.get_supported_providers()
    
    @patch('app.tasks.company_tasks.SessionLocal')
    def test_sync_listed_companies_database_transaction(self, mock_session_local, mock_celery_task):
        """
        データベーストランザクションが正しく管理されることを確認
        """
        # データベースセッションのモック
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        
        # エンドポイントのモック
        mock_endpoint = Mock(spec=APIEndpoint)
        mock_endpoint.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_endpoint
        
        # エラーを発生させる
        with patch('app.tasks.company_tasks.asyncio.new_event_loop') as mock_new_loop:
            mock_loop = MagicMock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.side_effect = Exception("Database error")
            
            # タスクをバインド
            sync_listed_companies.bind(mock_celery_task)
            
            # タスク実行（エラーが発生）
            result = sync_listed_companies.run(mock_celery_task, execution_type="manual")
            
            # ロールバックが呼ばれたことを確認
            mock_db.rollback.assert_called_once()
            
            # エラー結果が返されることを確認
            assert result["status"] == "failed"
            assert "error" in result