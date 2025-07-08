"""
企業関連APIエンドポイントのテスト
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, AsyncGenerator

from app.main import app
from app.models.company import Company, CompanySyncHistory
from app.db.session import get_session
from app.schemas.company import Sector17Master, Sector33Master, MarketMaster


class TestCompaniesAPI:
    """企業APIエンドポイントのテスト"""

    @pytest_asyncio.fixture
    async def client(self) -> AsyncGenerator[AsyncClient, None]:
        """非同期テストクライアント"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def sample_companies(self):
        """サンプル企業データ"""
        companies = []
        for i in range(1, 6):
            company = Mock(spec=Company)
            company.id = i
            company.code = f"{1000 + i}"
            company.company_name = f"テスト企業{i}"
            company.company_name_english = f"Test Company {i}"
            company.sector17_code = "01"
            company.sector33_code = "050"
            company.scale_category = "TOPIX Large70"
            company.market_code = "0111"
            company.margin_code = "1"
            company.reference_date = date(2024, 12, 26)
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
        history.total_companies = 100
        history.new_companies = 10
        history.updated_companies = 5
        history.deleted_companies = 2
        history.started_at = datetime(2024, 12, 26, 9, 0, 0)
        history.completed_at = datetime(2024, 12, 26, 9, 30, 0)
        history.error_message = None
        return history

    @pytest.mark.asyncio
    async def test_get_companies_success(self, client: AsyncClient, sample_companies):
        """企業一覧取得の成功テスト"""
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        # クエリ結果をモック
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(sample_companies)
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = sample_companies
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行
        response = await client.get("/api/v1/companies/")
        
        # クリーンアップ
        app.dependency_overrides.clear()
        
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
        assert data["per_page"] == 50

    @pytest.mark.asyncio
    async def test_get_companies_with_filters(self, client: AsyncClient, sample_companies):
        """フィルタ付き企業一覧取得のテスト"""
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        # フィルタされた結果をモック
        filtered_companies = sample_companies[:2]
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(filtered_companies)
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = filtered_companies
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行（フィルタパラメータ付き）
        response = await client.get(
            "/api/v1/companies/",
            params={
                "code": "1001",
                "company_name": "テスト",
                "sector17_code": "01",
                "is_active": True,
                "page": 1,
                "per_page": 10
            }
        )
        
        # クリーンアップ
        app.dependency_overrides.clear()
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(filtered_companies)
        assert data["per_page"] == 10

    @pytest.mark.asyncio
    async def test_get_company_by_code_success(self, client: AsyncClient, sample_companies):
        """特定企業取得の成功テスト"""
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        # 特定の企業を返すモック
        target_company = sample_companies[0]
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = target_company
        mock_db.execute.return_value = mock_result
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行
        response = await client.get("/api/v1/companies/1001")
        
        # クリーンアップ
        app.dependency_overrides.clear()
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "1001"
        assert data["company_name"] == "テスト企業1"

    @pytest.mark.asyncio
    async def test_get_company_by_code_not_found(self, client: AsyncClient):
        """企業が見つからない場合のテスト"""
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        # 企業が見つからない場合
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行
        response = await client.get("/api/v1/companies/9999")
        
        # クリーンアップ
        app.dependency_overrides.clear()
        
        # 結果検証
        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_sync_companies_success(self, client: AsyncClient, sample_sync_history):
        """企業データ同期の成功テスト"""
        # 同期サービスをモック
        with patch('app.api.v1.endpoints.companies.get_company_sync_service') as mock_get_sync_service:
            mock_sync_service = Mock()
            mock_sync_service.sync_companies = AsyncMock(return_value=sample_sync_history)
            mock_get_sync_service.return_value = mock_sync_service
            
            # テスト実行
            response = await client.post(
                "/api/v1/companies/sync",
                json={
                    "data_source_id": 1,
                    "sync_date": "2024-12-26",
                    "sync_type": "full"
                }
            )
            
            # デバッグ用：エラー内容を出力
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.text}")
                try:
                    print(f"Response JSON: {response.json()}")
                except:
                    pass
            
            # 結果検証
            assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["sync_type"] == "full"
        assert data["status"] == "completed"
        assert data["total_companies"] == 100

    @pytest.mark.asyncio
    async def test_sync_companies_error(self, client: AsyncClient):
        """企業データ同期のエラーテスト"""
        # 同期サービスでエラーが発生
        with patch('app.api.v1.endpoints.companies.get_company_sync_service') as mock_get_sync_service:
            mock_sync_service = Mock()
            mock_sync_service.sync_companies = AsyncMock(side_effect=Exception("Sync failed"))
            mock_get_sync_service.return_value = mock_sync_service
            
            # テスト実行
            response = await client.post(
            "/api/v1/companies/sync",
            json={
                "data_source_id": 1,
                "sync_type": "full"
            }
        )
        
        # 結果検証
        assert response.status_code == 400
        assert "Sync failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_sync_history_success(self, client: AsyncClient):
        """同期履歴取得の成功テスト"""
        # 履歴データを作成
        histories = []
        for i in range(3):
            history = Mock(spec=CompanySyncHistory)
            history.id = i + 1
            history.sync_date = date(2024, 12, 26 - i)
            history.sync_type = "full"
            history.status = "completed"
            history.total_companies = 100 - i * 10
            history.new_companies = 5 - i
            history.updated_companies = 3 - i
            history.deleted_companies = 1
            history.started_at = datetime(2024, 12, 26 - i, 9, 0, 0)
            history.completed_at = datetime(2024, 12, 26 - i, 9, 30, 0)
            history.error_message = None
            histories.append(history)
        
        # 同期サービスをモック
        with patch('app.api.v1.endpoints.companies.get_company_sync_service') as mock_get_sync_service:
            mock_sync_service = Mock()
            mock_sync_service.get_sync_history = AsyncMock(return_value=(histories, len(histories)))
            mock_get_sync_service.return_value = mock_sync_service
            
            # テスト実行
            response = await client.get("/api/v1/companies/sync/history")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == len(histories)
        assert len(data["items"]) == len(histories)

    @pytest.mark.asyncio
    async def test_get_sync_history_with_status_filter(self, client: AsyncClient):
        """ステータスフィルタ付き同期履歴取得のテスト"""
        # 失敗した履歴のみを作成
        failed_history = Mock(spec=CompanySyncHistory)
        failed_history.id = 1
        failed_history.sync_date = date(2024, 12, 26)
        failed_history.sync_type = "full"
        failed_history.status = "failed"
        failed_history.error_message = "API Error"
        
        # 同期サービスをモック
        with patch('app.api.v1.endpoints.companies.get_company_sync_service') as mock_get_sync_service:
            mock_sync_service = Mock()
            mock_sync_service.get_sync_history = AsyncMock(return_value=([failed_history], 1))
            mock_get_sync_service.return_value = mock_sync_service
            
            # テスト実行
            response = await client.get(
            "/api/v1/companies/sync/history",
            params={"status": "failed"}
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "failed"
        
        # サービスが正しいパラメータで呼ばれたことを確認
        mock_sync_service.get_sync_history.assert_called_once()
        call_args = mock_sync_service.get_sync_history.call_args
        assert call_args[1]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_get_latest_sync_status_success(self, client: AsyncClient, sample_sync_history):
        """最新同期ステータス取得の成功テスト"""
        # 同期サービスをモック
        with patch('app.api.v1.endpoints.companies.get_company_sync_service') as mock_get_sync_service:
            mock_sync_service = Mock()
            mock_sync_service.get_latest_sync_status = AsyncMock(return_value=sample_sync_history)
            mock_get_sync_service.return_value = mock_sync_service
            
            # テスト実行
            response = await client.get("/api/v1/companies/sync/status")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_latest_sync_status_none(self, client: AsyncClient):
        """同期履歴がない場合のテスト"""
        # 同期サービスをモック
        with patch('app.api.v1.endpoints.companies.get_company_sync_service') as mock_get_sync_service:
            mock_sync_service = Mock()
            mock_sync_service.get_latest_sync_status = AsyncMock(return_value=None)
            mock_get_sync_service.return_value = mock_sync_service
            
            # テスト実行
            response = await client.get("/api/v1/companies/sync/status")
        
        # 結果検証
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_get_sector17_masters(self, client: AsyncClient):
        """17業種区分マスター取得のテスト"""
        # サンプルマスターデータ
        masters = []
        for i in range(3):
            master = Mock(spec=Sector17Master)
            master.id = i + 1
            master.code = f"0{i + 1}"
            master.name = f"業種{i + 1}"
            master.name_english = f"Sector {i + 1}"
            master.display_order = i + 1
            master.is_active = True
            master.created_at = datetime.now()
            master.updated_at = datetime.now()
            # Pydanticモデル変換用のdict属性
            master.__dict__ = {
                "id": master.id,
                "code": master.code,
                "name": master.name,
                "name_english": master.name_english,
                "display_order": master.display_order,
                "is_active": master.is_active,
                "created_at": master.created_at,
                "updated_at": master.updated_at
            }
            masters.append(master)
        
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = masters
        mock_db.execute.return_value = mock_result
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行
        response = await client.get("/api/v1/companies/masters/sectors17")
        
        # クリーンアップ
        app.dependency_overrides.clear()
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["code"] == "01"
        assert data[0]["name"] == "業種1"

    @pytest.mark.asyncio
    async def test_get_sector33_masters_with_filter(self, client: AsyncClient):
        """17業種フィルタ付き33業種区分マスター取得のテスト"""
        # サンプルマスターデータ
        masters = []
        for i in range(2):
            master = Mock(spec=Sector33Master)
            master.id = i + 1
            master.code = f"10{i}"
            master.name = f"詳細業種{i + 1}"
            master.sector17_code = "01"
            master.display_order = i + 1
            master.is_active = True
            master.created_at = datetime.now()
            master.updated_at = datetime.now()
            # Pydanticモデル変換用のdict属性
            master.__dict__ = {
                "id": master.id,
                "code": master.code,
                "name": master.name,
                "name_english": None,
                "sector17_code": master.sector17_code,
                "display_order": master.display_order,
                "is_active": master.is_active,
                "created_at": master.created_at,
                "updated_at": master.updated_at
            }
            masters.append(master)
        
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = masters
        mock_db.execute.return_value = mock_result
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行
        response = await client.get(
            "/api/v1/companies/masters/sectors33",
            params={"sector17_code": "01"}
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(item["sector17_code"] == "01" for item in data)

    @pytest.mark.asyncio
    async def test_get_market_masters(self, client: AsyncClient):
        """市場区分マスター取得のテスト"""
        # サンプルマスターデータ
        masters = []
        market_names = ["プライム", "スタンダード", "グロース"]
        for i, name in enumerate(market_names):
            master = Mock(spec=MarketMaster)
            master.id = i + 1
            master.code = f"011{i + 1}"
            master.name = name
            master.name_english = f"Market {i + 1}"
            master.description = None  # descriptionフィールドを追加
            master.display_order = i + 1
            master.is_active = True
            master.created_at = datetime.now()
            master.updated_at = datetime.now()
            # Pydanticモデル変換用のdict属性
            master.__dict__ = {
                "id": master.id,
                "code": master.code,
                "name": master.name,
                "name_english": master.name_english,
                "description": master.description,
                "display_order": master.display_order,
                "is_active": master.is_active,
                "created_at": master.created_at,
                "updated_at": master.updated_at
            }
            masters.append(master)
        
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = masters
        mock_db.execute.return_value = mock_result
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行
        response = await client.get("/api/v1/companies/masters/markets")
        
        # クリーンアップ
        app.dependency_overrides.clear()
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "プライム"
        assert data[1]["name"] == "スタンダード"
        assert data[2]["name"] == "グロース"

    @pytest.mark.asyncio
    async def test_search_companies_post(self, client: AsyncClient, sample_companies):
        """POST形式での企業検索テスト"""
        # データベースセッションをモック
        mock_db = AsyncMock(spec=AsyncSession)
        
        # 検索結果をモック
        search_results = sample_companies[:2]
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(search_results)
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = search_results
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # get_sessionのオーバーライド
        async def mock_get_session():
            yield mock_db
        
        app.dependency_overrides[get_session] = mock_get_session
        
        # テスト実行
        response = await client.post(
            "/api/v1/companies/search",
            json={
                "code": "1001",
                "company_name": "テスト",
                "sector17_code": "01",
                "is_active": True,
                "page": 1,
                "per_page": 20
            }
        )
        
        # クリーンアップ
        app.dependency_overrides.clear()
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == len(search_results)
        assert data["per_page"] == 20

    @pytest.mark.asyncio
    async def test_validation_errors(self, client: AsyncClient):
        """バリデーションエラーのテスト"""
        # 無効なページ番号
        response = await client.get("/api/v1/companies/", params={"page": 0})
        assert response.status_code == 422
        
        # 無効なper_page
        response = await client.get("/api/v1/companies/", params={"per_page": 0})
        assert response.status_code == 422
        
        # 無効な同期リクエスト
        response = await client.post(
            "/api/v1/companies/sync",
            json={"data_source_id": "invalid"}
        )
        assert response.status_code == 422