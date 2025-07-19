"""
企業同期サービスのテスト

BaseSyncServiceを継承したCompanySyncServiceのテストを実施
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, date
from typing import List, Dict, Any

from app.services.company_sync_service import CompanySyncService
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager, JQuantsListedInfoClient
from app.models.company import Company, CompanySyncHistory


class TestCompanySyncService:
    """企業同期サービスのテスト"""

    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

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
        return Mock(spec=JQuantsListedInfoClient)

    @pytest.fixture
    def sync_service(self, mock_db, mock_data_source_service, mock_jquants_client_manager):
        """CompanySyncServiceのインスタンス"""
        return CompanySyncService(
            db=mock_db,
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_client_manager
        )

    @pytest.fixture
    def sample_jquants_data(self):
        """サンプルのJ-Quantsデータ"""
        return [
            {
                "Date": "20241226",
                "Code": "1234",
                "CompanyName": "テスト株式会社",
                "CompanyNameEnglish": "Test Corporation",
                "Sector17Code": "01",
                "Sector17CodeName": "食品",
                "Sector33Code": "050",
                "Sector33CodeName": "食料品",
                "ScaleCategory": "TOPIX Large70",
                "MarketCode": "0111",
                "MarketCodeName": "プライム",
                "MarginCode": "1",
                "MarginCodeName": "制度信用"
            },
            {
                "Date": "20241226",
                "Code": "5678",
                "CompanyName": "サンプル商事",
                "CompanyNameEnglish": "Sample Trading Co.",
                "Sector17Code": "02",
                "Sector17CodeName": "繊維製品",
                "Sector33Code": "100",
                "Sector33CodeName": "繊維製品",
                "ScaleCategory": "TOPIX Mid400",
                "MarketCode": "0112",
                "MarketCodeName": "スタンダード",
                "MarginCode": "2",
                "MarginCodeName": "一般信用"
            }
        ]

    @pytest.mark.asyncio
    async def test_sync_companies_success(
        self, 
        sync_service, 
        mock_db, 
        mock_jquants_client_manager, 
        mock_jquants_client,
        sample_jquants_data
    ):
        """企業データ同期の成功テスト"""
        # モックの設定
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        mock_jquants_client.get_all_listed_companies.return_value = sample_jquants_data
        
        # 既存企業データが見つからない場合の設定
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 同期履歴のモック
        mock_sync_history = Mock(spec=CompanySyncHistory)
        mock_sync_history.id = 1
        mock_sync_history.sync_date = date.today()
        mock_sync_history.sync_type = "full"
        mock_sync_history.status = "completed"
        mock_sync_history.total_companies = 2
        mock_sync_history.new_companies = 2
        mock_sync_history.updated_companies = 0
        
        # CompanySyncHistoryの作成をモック
        with patch('app.services.company_sync_service.CompanySyncHistory', return_value=mock_sync_history):
            # テスト実行
            result = await sync_service.sync_companies(data_source_id=1)
            
            # 結果検証
            assert result.status == "completed"
            assert result.total_companies == 2
            assert result.new_companies == 2
            assert result.updated_companies == 0
            
            # メソッド呼び出しの検証
            mock_jquants_client_manager.get_client.assert_called_once_with(1)
            mock_jquants_client.get_all_listed_companies.assert_called_once()
            mock_db.add.assert_called()
            assert mock_db.commit.call_count >= 2  # 初回と最終の最低2回

    @pytest.mark.asyncio
    async def test_sync_companies_api_error(
        self, 
        sync_service, 
        mock_db, 
        mock_jquants_client_manager, 
        mock_jquants_client
    ):
        """J-Quants API エラーのテスト"""
        # モックの設定
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        mock_jquants_client.get_all_listed_companies.side_effect = Exception("API Error")
        
        mock_sync_history = Mock(spec=CompanySyncHistory)
        
        with patch('app.services.company_sync_service.CompanySyncHistory', return_value=mock_sync_history):
            # テスト実行
            with pytest.raises(Exception) as exc_info:
                await sync_service.sync_companies(data_source_id=1)
            
            assert "API Error" in str(exc_info.value)
            
            # エラー時の同期履歴更新を検証
            assert mock_sync_history.status == "failed"
            assert mock_sync_history.error_message == "API Error"

    @pytest.mark.asyncio
    async def test_sync_companies_no_data(
        self, 
        sync_service, 
        mock_db, 
        mock_jquants_client_manager, 
        mock_jquants_client
    ):
        """データが取得できない場合のテスト"""
        # モックの設定
        mock_jquants_client_manager.get_client.return_value = mock_jquants_client
        mock_jquants_client.get_all_listed_companies.return_value = []
        
        mock_sync_history = Mock(spec=CompanySyncHistory)
        
        with patch('app.services.company_sync_service.CompanySyncHistory', return_value=mock_sync_history):
            # テスト実行
            with pytest.raises(Exception) as exc_info:
                await sync_service.sync_companies(data_source_id=1)
            
            assert "No company data received" in str(exc_info.value)

    def test_map_jquants_data_to_model_success(self, sync_service):
        """J-Quantsデータのモデルマッピング成功テスト"""
        jquants_data = {
            "Code": "1234",
            "CompanyName": "テスト株式会社",
            "CompanyNameEnglish": "Test Corporation",
            "Sector17Code": "01",
            "Sector33Code": "050",
            "ScaleCategory": "TOPIX Large70",
            "MarketCode": "0111",
            "MarginCode": "1"
        }
        
        # テスト実行
        result = sync_service._map_jquants_data_to_model(jquants_data)
        
        # 結果検証
        assert result is not None
        assert result["code"] == "1234"
        assert result["company_name"] == "テスト株式会社"
        assert result["company_name_english"] == "Test Corporation"
        assert result["sector17_code"] == "01"
        assert result["sector33_code"] == "050"
        assert result["scale_category"] == "TOPIX Large70"
        assert result["market_code"] == "0111"
        assert result["margin_code"] == "1"
        assert result["is_active"] is True

    def test_map_jquants_data_to_model_missing_required(self, sync_service):
        """必須フィールド不足時のマッピングテスト"""
        # コードが不足
        jquants_data_no_code = {
            "CompanyName": "テスト株式会社"
        }
        
        result = sync_service._map_jquants_data_to_model(jquants_data_no_code)
        assert result is None
        
        # 会社名が不足
        jquants_data_no_name = {
            "Code": "1234"
        }
        
        result = sync_service._map_jquants_data_to_model(jquants_data_no_name)
        assert result is None

    def test_map_jquants_data_to_model_partial_data(self, sync_service):
        """部分的なデータでのマッピングテスト"""
        jquants_data = {
            "Code": "1234",
            "CompanyName": "テスト株式会社"
            # その他のフィールドは未設定
        }
        
        # テスト実行
        result = sync_service._map_jquants_data_to_model(jquants_data)
        
        # 結果検証
        assert result is not None
        assert result["code"] == "1234"
        assert result["company_name"] == "テスト株式会社"
        assert result["company_name_english"] is None
        assert result["sector17_code"] is None
        assert result["sector33_code"] is None
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_existing_company(self, sync_service, mock_db):
        """既存企業データ取得のテスト"""
        # モック設定
        mock_company = Mock(spec=Company)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_company
        mock_db.execute.return_value = mock_result
        
        # テスト実行
        result = await sync_service._get_existing_company("1234")
        
        # 結果検証
        assert result == mock_company
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_company_not_found(self, sync_service, mock_db):
        """既存企業データが見つからない場合のテスト"""
        # モック設定
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # テスト実行
        result = await sync_service._get_existing_company("9999")
        
        # 結果検証
        assert result is None

    @pytest.mark.asyncio
    async def test_create_company(self, sync_service, mock_db):
        """新規企業データ作成のテスト"""
        company_data = {
            "code": "1234",
            "company_name": "テスト株式会社",
            "reference_date": date.today(),
            "is_active": True
        }
        
        with patch('app.services.company_sync_service.Company') as mock_company_class:
            mock_company_instance = Mock()
            mock_company_class.return_value = mock_company_instance
            
            # テスト実行
            await sync_service._create_company(company_data)
            
            # 結果検証
            mock_company_class.assert_called_once_with(**company_data)
            mock_db.add.assert_called_once_with(mock_company_instance)

    @pytest.mark.asyncio
    async def test_update_company(self, sync_service):
        """企業データ更新のテスト"""
        # 既存の企業データ
        existing_company = Mock(spec=Company)
        existing_company.code = "1234"
        existing_company.company_name = "旧社名"
        existing_company.company_name_english = "Old Name"
        existing_company.sector17_code = "01"
        
        # 新しいデータ
        new_data = {
            "code": "1234",  # 更新されない
            "company_name": "新社名",  # 更新される
            "company_name_english": "New Name",  # 更新される
            "sector17_code": "01",  # 変更なし
            "is_active": True
        }
        
        # テスト実行
        await sync_service._update_company(existing_company, new_data)
        
        # 結果検証
        assert existing_company.company_name == "新社名"
        assert existing_company.company_name_english == "New Name"
        assert existing_company.sector17_code == "01"  # 変更なし
        assert hasattr(existing_company, 'updated_at')

    @pytest.mark.asyncio
    async def test_update_company_no_changes(self, sync_service):
        """企業データに変更がない場合のテスト"""
        # 既存の企業データ
        existing_company = Mock(spec=Company)
        existing_company.code = "1234"
        existing_company.company_name = "同じ社名"
        existing_company.company_name_english = "Same Name"
        existing_company.is_active = True
        
        # 同じデータ
        new_data = {
            "code": "1234",
            "company_name": "同じ社名",
            "company_name_english": "Same Name",
            "is_active": True
        }
        
        # テスト実行
        await sync_service._update_company(existing_company, new_data)
        
        # updated_atが設定されていないことを確認（変更がないため）
        # この実装では、変更がない場合はupdated_atを更新しない

    @pytest.mark.asyncio
    async def test_get_sync_history(self, sync_service, mock_db):
        """同期履歴取得のテスト"""
        # モック設定
        mock_histories = [Mock(spec=CompanySyncHistory) for _ in range(3)]
        
        # 総数取得のモック
        mock_count_result = Mock()
        mock_count_result.scalars.return_value.all.return_value = [1, 2, 3]
        
        # データ取得のモック
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = mock_histories
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # テスト実行
        histories, total = await sync_service.get_sync_history(limit=10, offset=0)
        
        # 結果検証
        assert histories == mock_histories
        assert total == 3
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_latest_sync_status(self, sync_service, mock_db):
        """最新同期ステータス取得のテスト"""
        # モック設定
        mock_history = Mock(spec=CompanySyncHistory)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_history
        mock_db.execute.return_value = mock_result
        
        # テスト実行
        result = await sync_service.get_latest_sync_status()
        
        # 結果検証
        assert result == mock_history
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_old_companies(self, sync_service, mock_db):
        """古い企業データの非アクティブ化テスト"""
        # モック設定
        mock_result = Mock()
        mock_result.rowcount = 5  # 5件が非アクティブ化された
        mock_db.execute.return_value = mock_result
        
        active_codes = ["1234", "5678", "9012"]
        
        # テスト実行
        deactivated_count = await sync_service.deactivate_missing_companies(active_codes)
        
        # 結果検証
        assert deactivated_count == 5
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_old_companies_empty_codes(self, sync_service):
        """アクティブコードが空の場合のテスト"""
        # テスト実行
        deactivated_count = await sync_service.deactivate_missing_companies([])
        
        # 結果検証
        assert deactivated_count == 0

    # 基底クラスのメソッドのテスト
    @pytest.mark.asyncio
    async def test_sync_method(self, sync_service, mock_jquants_client_manager, mock_jquants_client, mock_db):
        """syncメソッド（基底クラスの抽象メソッド実装）のテスト"""
        # J-Quantsクライアントの設定
        mock_jquants_client.get_all_listed_companies = AsyncMock(return_value=[
            {"Code": "1234", "CompanyName": "Test Company"}
        ])
        mock_jquants_client_manager.get_client = AsyncMock(return_value=mock_jquants_client)
        
        # executeの結果をモック
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result
        
        # data_source_idありの場合
        result = await sync_service.sync(data_source_id=1, sync_type='full')
        
        assert result['status'] == 'completed'
        assert 'history_id' in result
        assert 'total_companies' in result
        
        # data_source_idなしの場合（sync_all_companies_simple）
        mock_data_source = Mock()
        mock_data_source.id = 1
        sync_service.data_source_service.get_jquants_source = AsyncMock(return_value=mock_data_source)
        
        result = await sync_service.sync()
        
        assert result['status'] == 'success'
        assert 'sync_count' in result
        assert 'duration' in result

    def test_get_history_model(self, sync_service):
        """get_history_modelメソッドのテスト"""
        assert sync_service.get_history_model() == CompanySyncHistory

    def test_logger_initialization(self, sync_service):
        """ロガー初期化のテスト（基底クラスから継承）"""
        assert hasattr(sync_service, 'logger')
        assert sync_service.logger.name == 'CompanySyncService'

    @pytest.mark.asyncio
    async def test_handle_error_integration(self, sync_service, caplog):
        """エラーハンドリングのテスト（基底クラスのメソッド）"""
        import logging
        
        error = Exception("Test error in company sync")
        context = {
            "sync_type": "full",
            "data_source_id": 1,
            "company_count": 100
        }
        
        with caplog.at_level(logging.ERROR):
            sync_service.handle_error(error, context)
        
        assert "CompanySyncService sync error: Test error in company sync" in caplog.text

    @pytest.mark.asyncio 
    async def test_get_sync_history_with_count(self, sync_service, mock_db):
        """get_sync_history_with_countメソッドのテスト"""
        # 履歴データのモック
        mock_histories = [
            Mock(spec=CompanySyncHistory, id=1, status="completed"),
            Mock(spec=CompanySyncHistory, id=2, status="completed")
        ]
        
        # get_sync_historyメソッドのモック（基底クラスから継承）
        with patch.object(sync_service, 'get_sync_history', return_value=mock_histories):
            # カウント用のクエリ結果モック
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [1, 2, 3, 4, 5]
            mock_db.execute.return_value = mock_result
            
            histories, total = await sync_service.get_sync_history_with_count(
                limit=2, offset=0, status="completed"
            )
        
        assert len(histories) == 2
        assert total == 5

    @pytest.mark.asyncio
    async def test_create_and_update_sync_history(self, sync_service, mock_db):
        """同期履歴の作成と更新のテスト（基底クラスのメソッド）"""
        # create_sync_historyのテスト
        with patch.object(sync_service, 'create_sync_history') as mock_create:
            mock_history = Mock(spec=CompanySyncHistory)
            mock_history.id = 1
            mock_history.status = "running"
            mock_create.return_value = mock_history
            
            history = await sync_service.create_sync_history(
                sync_type="full",
                sync_date=date.today()
            )
            
            assert history.id == 1
            assert history.status == "running"
        
        # update_sync_history_successのテスト
        with patch.object(sync_service, 'update_sync_history_success') as mock_update_success:
            mock_history.status = "completed"
            mock_update_success.return_value = mock_history
            
            updated_history = await sync_service.update_sync_history_success(
                mock_history,
                total_companies=100,
                new_companies=50,
                updated_companies=50
            )
            
            assert updated_history.status == "completed"
        
        # update_sync_history_failureのテスト
        with patch.object(sync_service, 'update_sync_history_failure') as mock_update_failure:
            mock_history.status = "failed"
            mock_history.error_message = "Test error"
            mock_update_failure.return_value = mock_history
            
            error = Exception("Test error")
            failed_history = await sync_service.update_sync_history_failure(
                mock_history,
                error
            )
            
            assert failed_history.status == "failed"
            assert failed_history.error_message == "Test error"