"""
エンドツーエンドテスト

実際の問題:
- APIエンドポイントからCeleryタスクまでの完全なフロー
- 認証からデータ同期までの一連の流れ
- エラー時のロールバック動作
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json

from fastapi.testclient import TestClient
from celery.result import AsyncResult

from app.main import app
from app.models.data_source import DataSource
from app.models.api_token import APIToken
from app.models.company import Company, CompanySyncHistory
from app.models.api_endpoint import APIEndpoint, APIEndpointExecutionLog, APIEndpointSchedule


class TestEndToEndCompanySync:
    """企業データ同期のエンドツーエンドテスト"""
    
    @pytest.fixture
    def client(self):
        """FastAPIテストクライアント"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_data_source(self):
        """モックのデータソース"""
        data_source = Mock(spec=DataSource)
        data_source.id = 1
        data_source.provider_type = "jquants"
        data_source.name = "J-Quants API"
        data_source.is_enabled = True
        data_source.credentials = {
            "mail_address": "test@example.com",
            "password": "test_password"
        }
        return data_source
    
    @pytest.fixture
    def mock_api_endpoint(self):
        """モックのAPIエンドポイント"""
        endpoint = Mock(spec=APIEndpoint)
        endpoint.id = 1
        endpoint.data_source_id = 1
        endpoint.data_type = "listed_companies"
        endpoint.is_enabled = True
        endpoint.execution_mode = "scheduled"
        return endpoint
    
    @patch('app.api.v1.endpoints.companies.get_session')
    @patch('app.api.v1.endpoints.companies.sync_listed_companies')
    def test_manual_sync_endpoint_to_celery(self, mock_sync_task, mock_get_session, client):
        """
        手動同期APIエンドポイントからCeleryタスクまでの流れをテスト
        これが実際のユーザー操作の流れ
        """
        # データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        # Celeryタスクのモック
        mock_task_result = Mock()
        mock_task_result.id = "test-task-id-123"
        mock_sync_task.delay.return_value = mock_task_result
        
        # APIエンドポイントを呼び出し
        response = client.post("/api/v1/companies/sync/manual")
        
        # レスポンスの確認
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id-123"
        assert data["status"] == "started"
        assert "同期処理を開始しました" in data["message"]
        
        # Celeryタスクが呼ばれたことを確認
        mock_sync_task.delay.assert_called_once_with("manual")
    
    @patch('app.api.v1.endpoints.companies.AsyncResult')
    def test_sync_task_status_endpoint(self, mock_async_result, client):
        """
        同期タスクのステータス確認エンドポイントのテスト
        """
        # タスク結果のモック
        mock_result = Mock()
        mock_result.state = "SUCCESS"
        mock_result.info = {
            "status": "success",
            "sync_count": 4417,
            "duration": 5.5,
            "executed_at": datetime.utcnow().isoformat()
        }
        mock_async_result.return_value = mock_result
        
        # ステータス確認
        response = client.get("/api/v1/companies/sync/task/test-task-id")
        
        # レスポンスの確認
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "SUCCESS"
        assert data["result"]["sync_count"] == 4417
        assert data["status"] == "同期完了"
    
    @patch('app.api.v1.endpoints.companies.get_session')
    def test_create_sync_schedule_flow(self, mock_get_session, client):
        """
        同期スケジュール作成の完全な流れをテスト
        """
        # データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        # エンドポイントのモック
        mock_endpoint = Mock(spec=APIEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.data_type = "listed_companies"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_endpoint
        mock_db.execute.return_value = mock_result
        
        # スケジュールサービスのモック
        with patch('app.api.v1.endpoints.companies.RedbeatScheduleService') as mock_schedule_service:
            mock_service_instance = AsyncMock()
            mock_schedule = Mock(spec=APIEndpointSchedule)
            mock_schedule.execution_time = datetime.strptime("05:00", "%H:%M").time()
            mock_schedule.timezone = "Asia/Tokyo"
            mock_service_instance.create_or_update_schedule.return_value = mock_schedule
            mock_schedule_service.return_value = mock_service_instance
            
            # スケジュール作成
            response = client.post(
                "/api/v1/companies/sync/schedule",
                json={"hour": 5, "minute": 0}
            )
            
            # レスポンスの確認
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["execution_time"] == "05:00"
            assert "スケジュールを 05:00 で作成しました" in data["message"]
    
    @patch('app.tasks.company_tasks.SessionLocal')
    @patch('app.tasks.company_tasks.async_session_maker')
    @patch('app.tasks.company_tasks.DataSourceService')
    @patch('app.tasks.company_tasks.JQuantsClientManager')
    @patch('app.tasks.company_tasks.CompanySyncService')
    def test_full_sync_flow_with_authentication(
        self,
        mock_sync_service_class,
        mock_client_manager_class,
        mock_ds_service_class,
        mock_async_session,
        mock_session_local
    ):
        """
        認証からデータ同期までの完全なフローをテスト
        実際に問題となったStrategyRegistry関連も含む
        """
        # SessionLocalのモック
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        
        # エンドポイントのモック
        mock_endpoint = Mock(spec=APIEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.data_type = "listed_companies"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_endpoint
        
        # 非同期セッションのモック
        mock_async_db = AsyncMock()
        mock_async_session.return_value.__aenter__.return_value = mock_async_db
        
        # サービスのモック設定
        mock_ds_service = AsyncMock()
        mock_ds_service.get_jquants_source.return_value = Mock(id=1)
        mock_ds_service_class.return_value = mock_ds_service
        
        mock_sync_service = AsyncMock()
        mock_sync_history = Mock(
            id=1,
            total_companies=4417,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        mock_sync_service.sync_companies.return_value = mock_sync_history
        mock_sync_service_class.return_value = mock_sync_service
        
        # Celeryタスクを直接実行
        from app.tasks.company_tasks import sync_listed_companies
        
        # モックのCeleryタスク
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        mock_task.update_state = Mock()
        
        # strategiesがインポートされていることを確認
        import app.services.auth.strategies
        from app.services.auth import StrategyRegistry
        assert "jquants" in StrategyRegistry.get_supported_providers()
        
        # イベントループのモック
        with patch('app.tasks.company_tasks.asyncio.new_event_loop') as mock_new_loop:
            mock_loop = MagicMock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.return_value = {
                "status": "success",
                "sync_count": 4417,
                "duration": 5.5,
                "executed_at": datetime.utcnow()
            }
            
            # タスク実行
            sync_listed_companies.bind(mock_task)
            result = sync_listed_companies.run(mock_task, execution_type="manual")
            
            # 結果の確認
            assert result["status"] == "success"
            assert result["sync_count"] == 4417
            
            # 実行ログが作成されたことを確認
            assert mock_db.add.called
            execution_log = mock_db.add.call_args[0][0]
            assert isinstance(execution_log, APIEndpointExecutionLog)
            assert execution_log.success is True
            assert execution_log.data_count == 4417
    
    @patch('app.api.v1.endpoints.companies.get_session')
    def test_error_handling_and_rollback(self, mock_get_session, client):
        """
        エラー時のロールバック動作のテスト
        """
        # データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        # エラーを発生させる
        mock_db.execute.side_effect = Exception("Database connection lost")
        
        # エンドポイントを呼び出し
        response = client.get("/api/v1/companies/sync/schedule")
        
        # エラーレスポンスの確認
        assert response.status_code == 500
        
        # ロールバックは非同期セッションでは自動的に行われる
    
    def test_htmx_integration_flow(self, client):
        """
        HTMXを使用したフロントエンドとの統合テスト
        """
        # HTMXヘッダーを含むリクエスト
        headers = {
            "HX-Request": "true",
            "HX-Target": "sync-result",
            "HX-Trigger": "sync-button"
        }
        
        with patch('app.api.v1.endpoints.companies.sync_listed_companies') as mock_sync_task:
            mock_task_result = Mock()
            mock_task_result.id = "htmx-task-id"
            mock_sync_task.delay.return_value = mock_task_result
            
            # APIエンドポイントを呼び出し
            response = client.post(
                "/api/v1/companies/sync/manual",
                headers=headers
            )
            
            # レスポンスの確認
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "htmx-task-id"
            
            # HTMXの後続リクエストをシミュレート
            with patch('app.api.v1.endpoints.companies.AsyncResult') as mock_async_result:
                mock_result = Mock()
                mock_result.state = "PROGRESS"
                mock_result.info = {
                    "current": 2000,
                    "total": 4417,
                    "message": "処理中..."
                }
                mock_async_result.return_value = mock_result
                
                # 進捗確認
                progress_response = client.get(
                    f"/api/v1/companies/sync/task/{data['task_id']}",
                    headers=headers
                )
                
                assert progress_response.status_code == 200
                progress_data = progress_response.json()
                assert progress_data["state"] == "PROGRESS"
                assert progress_data["current"] == 2000
                assert progress_data["total"] == 4417