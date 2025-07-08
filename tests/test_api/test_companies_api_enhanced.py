"""
企業関連APIエンドポイントの強化テスト（依存関係オーバーライド使用）
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date
from fastapi.testclient import TestClient
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.company import Company, CompanySyncHistory
from app.api.v1.endpoints.companies import get_session, get_company_sync_service
from app.services.company_sync_service import CompanySyncService


class TestCompaniesAPIEnhanced:
    """企業APIエンドポイントの強化テスト"""

    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)

    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_companies(self):
        """サンプル企業データ"""
        companies = []
        for i in range(1, 6):
            company = Mock(spec=Company)
            company.id = i
            company.code = f"{70000 + i}"  # 5桁コード対応
            company.company_name = f"テスト企業{i}"
            company.company_name_english = f"Test Company {i}"
            company.sector17_code = "6"
            company.sector33_code = "3700"
            company.scale_category = "TOPIX Large70"
            company.market_code = "0111"
            company.margin_code = "1"
            company.is_active = True
            company.created_at = datetime(2024, 12, 26, 10, 0, 0)
            company.updated_at = datetime(2024, 12, 26, 10, 0, 0)
            companies.append(company)
        return companies

    @pytest.fixture
    def sample_sync_history(self):
        """サンプル同期履歴"""
        history = Mock(spec=CompanySyncHistory)
        history.id = 1
        history.sync_date = date(2024, 12, 26)
        history.sync_type = "full"
        history.status = "completed"
        history.total_companies = 4412
        history.new_companies = 3
        history.updated_companies = 4409
        history.deleted_companies = 0
        history.started_at = datetime(2024, 12, 26, 9, 0, 0)
        history.completed_at = datetime(2024, 12, 26, 9, 30, 0)
        history.error_message = None
        return history

    def test_get_companies_success_with_dependency_override(self, client, mock_db_session, sample_companies):
        """企業一覧取得の成功テスト（依存関係オーバーライド使用）"""
        # クエリ結果をモック
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(sample_companies)
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = sample_companies
        
        mock_db_session.execute.side_effect = [mock_count_result, mock_data_result]
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_session] = lambda: mock_db_session
        
        try:
            # テスト実行
            response = client.get("/api/v1/companies/?page=1&per_page=5")
            
            # 結果検証
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "per_page" in data
            assert "pages" in data
            assert data["total"] == len(sample_companies)
            assert data["page"] == 1
            assert data["per_page"] == 5
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_get_company_by_code_success_with_dependency_override(self, client, mock_db_session, sample_companies):
        """特定企業取得の成功テスト（依存関係オーバーライド使用）"""
        # 特定の企業を返すモック
        target_company = sample_companies[0]
        target_company.code = "72030"  # トヨタ自動車コード
        target_company.company_name = "トヨタ自動車"
        target_company.company_name_english = "TOYOTA MOTOR CORPORATION"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = target_company
        mock_db_session.execute.return_value = mock_result
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_session] = lambda: mock_db_session
        
        try:
            # テスト実行
            response = client.get("/api/v1/companies/72030")
            
            # 結果検証
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == "72030"
            assert data["company_name"] == "トヨタ自動車"
            assert data["company_name_english"] == "TOYOTA MOTOR CORPORATION"
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_get_company_by_code_not_found_with_dependency_override(self, client, mock_db_session):
        """企業が見つからない場合のテスト（依存関係オーバーライド使用）"""
        # 企業が見つからない場合
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_session] = lambda: mock_db_session
        
        try:
            # テスト実行
            response = client.get("/api/v1/companies/99999")
            
            # 結果検証
            assert response.status_code == 404
            assert "Company not found" in response.json()["detail"]
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_sync_companies_success_with_dependency_override(self, client, sample_sync_history):
        """企業データ同期の成功テスト（依存関係オーバーライド使用）"""
        # 同期サービスをモック
        mock_sync_service = AsyncMock(spec=CompanySyncService)
        mock_sync_service.sync_companies.return_value = sample_sync_history
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_company_sync_service] = lambda: mock_sync_service
        
        try:
            # テスト実行
            response = client.post(
                "/api/v1/companies/sync",
                json={
                    "data_source_id": 1,
                    "sync_type": "full"
                }
            )
            
            # 結果検証
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["sync_type"] == "full"
            assert data["status"] == "completed"
            assert data["total_companies"] == 4412
            assert data["new_companies"] == 3
            assert data["updated_companies"] == 4409
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_sync_companies_error_with_dependency_override(self, client):
        """企業データ同期のエラーテスト（依存関係オーバーライド使用）"""
        # 同期サービスでエラーが発生
        mock_sync_service = AsyncMock(spec=CompanySyncService)
        mock_sync_service.sync_companies.side_effect = Exception("Sync failed")
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_company_sync_service] = lambda: mock_sync_service
        
        try:
            # テスト実行
            response = client.post(
                "/api/v1/companies/sync",
                json={
                    "data_source_id": 1,
                    "sync_type": "full"
                }
            )
            
            # 結果検証
            assert response.status_code == 400
            assert "Sync failed" in response.json()["detail"]
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    @pytest.mark.skip(reason="FastAPI TestClient does not handle async generator errors properly")
    def test_database_connection_error(self, client):
        """データベース接続エラーのテスト
        
        注: FastAPIのTestClientは非同期ジェネレータ内でのエラーを
        適切にハンドリングできないため、このテストはスキップ
        """
        # データベース接続エラーをシミュレート
        def mock_session_error():
            raise Exception("Database connection failed")
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_session] = mock_session_error
        
        try:
            # テスト実行
            response = client.get("/api/v1/companies/")
            
            # 結果検証（内部サーバーエラーになることを期待）
            assert response.status_code == 500
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    @patch('httpx.AsyncClient')
    def test_jquants_authentication_error(self, mock_http_client, client):
        """J-Quants認証エラーのテスト"""
        from httpx import HTTPStatusError
        
        # HTTP 401エラーをシミュレート
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_http_client.return_value.__aenter__.return_value.post.side_effect = HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        
        # 同期サービスで認証エラーが発生するモック
        mock_sync_service = AsyncMock(spec=CompanySyncService)
        mock_sync_service.sync_companies.side_effect = Exception("Authentication failed: J-Quants API returned 401")
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_company_sync_service] = lambda: mock_sync_service
        
        try:
            # テスト実行
            response = client.post(
                "/api/v1/companies/sync",
                json={
                    "data_source_id": 1,
                    "sync_type": "full"
                }
            )
            
            # 結果検証
            assert response.status_code == 400
            assert "Authentication failed" in response.json()["detail"]
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_jquants_token_expired_error(self, client):
        """J-Quantsトークン期限切れエラーのテスト"""
        # トークン期限切れエラーをシミュレート
        mock_sync_service = AsyncMock(spec=CompanySyncService)
        mock_sync_service.sync_companies.side_effect = Exception("Token expired: Please refresh authentication token")
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_company_sync_service] = lambda: mock_sync_service
        
        try:
            # テスト実行
            response = client.post(
                "/api/v1/companies/sync",
                json={
                    "data_source_id": 1,
                    "sync_type": "full"
                }
            )
            
            # 結果検証
            assert response.status_code == 400
            assert "Token expired" in response.json()["detail"]
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_jquants_rate_limit_error(self, client):
        """J-Quantsレートリミットエラーのテスト"""
        # レートリミットエラーをシミュレート
        mock_sync_service = AsyncMock(spec=CompanySyncService)
        mock_sync_service.sync_companies.side_effect = Exception("Rate limit exceeded: Too many requests")
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_company_sync_service] = lambda: mock_sync_service
        
        try:
            # テスト実行
            response = client.post(
                "/api/v1/companies/sync",
                json={
                    "data_source_id": 1,
                    "sync_type": "full"
                }
            )
            
            # 結果検証
            assert response.status_code == 400
            assert "Rate limit exceeded" in response.json()["detail"]
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_validation_errors(self, client):
        """バリデーションエラーのテスト"""
        # 無効なページ番号
        response = client.get("/api/v1/companies/?page=0")
        assert response.status_code == 422
        
        # 無効なper_page
        response = client.get("/api/v1/companies/?per_page=0")
        assert response.status_code == 422
        
        # 無効な同期リクエスト
        response = client.post(
            "/api/v1/companies/sync",
            json={"data_source_id": "invalid"}
        )
        assert response.status_code == 422

    def test_sql_injection_protection(self, client, mock_db_session):
        """SQLインジェクション攻撃からの保護テスト"""
        # SQLインジェクション試行
        malicious_input = "'; DROP TABLE companies; --"
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [mock_count_result, mock_data_result]
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_session] = lambda: mock_db_session
        
        try:
            # テスト実行
            response = client.get(f"/api/v1/companies/?code={malicious_input}")
            
            # 結果検証（正常にレスポンスが返されること）
            assert response.status_code == 200
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()

    def test_large_page_size_handling(self, client, mock_db_session):
        """大きなページサイズのハンドリングテスト"""
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [mock_count_result, mock_data_result]
        
        # 依存関係オーバーライド
        app.dependency_overrides[get_session] = lambda: mock_db_session
        
        try:
            # 最大サイズでのテスト
            response = client.get("/api/v1/companies/?per_page=1000")
            assert response.status_code == 200
            
            # 最大サイズを超える場合
            response = client.get("/api/v1/companies/?per_page=1001")
            assert response.status_code == 422
            
        finally:
            # 依存関係オーバーライドをクリア
            app.dependency_overrides.clear()