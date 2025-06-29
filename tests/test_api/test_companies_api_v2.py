"""
企業関連APIエンドポイントのテスト（Pydantic v2対応版）
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date
from fastapi.testclient import TestClient
from typing import List

from app.main import app
from app.models.company import Company, CompanySyncHistory


class TestCompaniesAPIv2:
    """企業APIエンドポイントのテスト（Pydantic v2対応）"""

    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)

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

    @patch('app.api.v1.endpoints.companies.get_session')
    def test_get_companies_success(self, mock_get_session, client, sample_companies):
        """企業一覧取得の成功テスト"""
        # 非同期データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        # クエリ結果をモック
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(sample_companies)
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = sample_companies
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
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

    @patch('app.api.v1.endpoints.companies.get_session')
    def test_get_company_by_code_success(self, mock_get_session, client, sample_companies):
        """特定企業取得の成功テスト（5桁コード）"""
        # 非同期データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        # 特定の企業を返すモック
        target_company = sample_companies[0]
        target_company.code = "72030"  # トヨタ自動車コード
        target_company.company_name = "トヨタ自動車"
        target_company.company_name_english = "TOYOTA MOTOR CORPORATION"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = target_company
        mock_db.execute.return_value = mock_result
        
        # テスト実行
        response = client.get("/api/v1/companies/72030")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "72030"
        assert data["company_name"] == "トヨタ自動車"
        assert data["company_name_english"] == "TOYOTA MOTOR CORPORATION"

    @patch('app.api.v1.endpoints.companies.get_session')
    def test_get_company_by_code_not_found(self, mock_get_session, client):
        """企業が見つからない場合のテスト"""
        # 非同期データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        # 企業が見つからない場合
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # テスト実行
        response = client.get("/api/v1/companies/99999")
        
        # 結果検証
        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]

    @patch('app.api.v1.endpoints.companies.get_company_sync_service')
    def test_sync_companies_success(self, mock_get_sync_service, client, sample_sync_history):
        """企業データ同期の成功テスト"""
        # 同期サービスをモック
        mock_sync_service = Mock()
        mock_sync_service.sync_companies = AsyncMock(return_value=sample_sync_history)
        mock_get_sync_service.return_value = mock_sync_service
        
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

    @patch('app.api.v1.endpoints.companies.get_company_sync_service')
    def test_sync_companies_error(self, mock_get_sync_service, client):
        """企業データ同期のエラーテスト"""
        # 同期サービスでエラーが発生
        mock_sync_service = Mock()
        mock_sync_service.sync_companies = AsyncMock(side_effect=Exception("Sync failed"))
        mock_get_sync_service.return_value = mock_sync_service
        
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

    @patch('app.api.v1.endpoints.companies.get_company_sync_service')
    def test_get_sync_history_success(self, mock_get_sync_service, client):
        """同期履歴取得の成功テスト"""
        # 履歴データを作成
        histories = []
        for i in range(3):
            history = Mock(spec=CompanySyncHistory)
            history.id = i + 1
            history.sync_date = date(2024, 12, 26 - i)
            history.sync_type = "full"
            history.status = "completed"
            history.total_companies = 4412 - i * 10
            history.new_companies = 5 - i
            history.updated_companies = 4407 - i * 10
            history.deleted_companies = 0
            history.started_at = datetime(2024, 12, 26 - i, 9, 0, 0)
            history.completed_at = datetime(2024, 12, 26 - i, 9, 30, 0)
            history.error_message = None
            histories.append(history)
        
        # 同期サービスをモック
        mock_sync_service = Mock()
        mock_sync_service.get_sync_history = AsyncMock(return_value=(histories, len(histories)))
        mock_get_sync_service.return_value = mock_sync_service
        
        # テスト実行
        response = client.get("/api/v1/companies/sync/history")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == len(histories)
        assert len(data["items"]) == len(histories)

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

    @patch('app.api.v1.endpoints.companies.get_session')
    def test_search_companies_with_filters(self, mock_get_session, client, sample_companies):
        """フィルタ付き企業検索のテスト"""
        # 非同期データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        # フィルタされた結果をモック
        filtered_companies = sample_companies[:2]
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(filtered_companies)
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = filtered_companies
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # テスト実行（フィルタパラメータ付き）
        response = client.get(
            "/api/v1/companies/?code=72030&company_name=トヨタ&sector17_code=6&is_active=true&page=1&per_page=10"
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(filtered_companies)
        assert data["per_page"] == 10

    @patch('app.api.v1.endpoints.companies.get_session')
    def test_get_sector17_masters(self, mock_get_session, client):
        """17業種区分マスター取得のテスト"""
        # サンプルマスターデータ
        masters = []
        for i in range(3):
            master = Mock()
            master.id = i + 1
            master.code = f"{i + 1}"
            master.name = f"業種{i + 1}"
            master.name_english = f"Sector {i + 1}"
            master.display_order = i + 1
            master.is_active = True
            master.created_at = datetime.now()
            master.updated_at = datetime.now()
            masters.append(master)
        
        # 非同期データベースセッションのモック
        mock_db = AsyncMock()
        mock_get_session.return_value = mock_db
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = masters
        mock_db.execute.return_value = mock_result
        
        # テスト実行
        response = client.get("/api/v1/companies/masters/sectors17")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["code"] == "1"
        assert data[0]["name"] == "業種1"

    def test_api_performance_with_large_dataset(self, client):
        """大量データでのAPI性能テスト"""
        # 大量データを想定したパラメータでのテスト
        response = client.get("/api/v1/companies/?page=1&per_page=1000")
        
        # レスポンスが適切に処理されることを確認
        # 実際のデータがなくても、バリデーションは通るはず
        assert response.status_code in [200, 307]  # 成功またはリダイレクト

    def test_concurrent_api_access(self, client):
        """同時アクセス時のAPIテスト"""
        import concurrent.futures
        import requests
        
        def make_request():
            try:
                response = client.get("/api/v1/companies/?page=1&per_page=1")
                return response.status_code
            except Exception:
                return 500
        
        # 複数の同時リクエストをシミュレート
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 少なくとも一部のリクエストが成功することを確認
        success_codes = [200, 307]  # 成功またはリダイレクト
        assert any(code in success_codes for code in results)

    def test_api_with_special_characters(self, client):
        """特殊文字を含むパラメータでのAPIテスト"""
        # 日本語文字を含む検索
        response = client.get("/api/v1/companies/?company_name=トヨタ自動車")
        assert response.status_code in [200, 307]
        
        # エンコードされた文字列での検索
        response = client.get("/api/v1/companies/?company_name=%E3%83%88%E3%83%A8%E3%82%BF")
        assert response.status_code in [200, 307]

    def test_api_edge_cases(self, client):
        """APIのエッジケーステスト"""
        # 最大ページサイズでのテスト
        response = client.get("/api/v1/companies/?per_page=1000")
        assert response.status_code in [200, 307]
        
        # 最大ページサイズを超える場合
        response = client.get("/api/v1/companies/?per_page=1001")
        assert response.status_code == 422
        
        # 存在しない企業コードでのテスト
        response = client.get("/api/v1/companies/00000")
        assert response.status_code == 404