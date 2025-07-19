"""
同期サービスの統合テスト

BaseSyncServiceを継承した各同期サービスの統合的な動作確認
"""

import pytest
from datetime import datetime, date, timedelta
from typing import List
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.company import Company, CompanySyncHistory
from app.models.daily_quote import DailyQuote, DailyQuotesSyncHistory
from app.services.company_sync_service import CompanySyncService
from app.services.daily_quotes_sync_service import DailyQuotesSyncService
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.db.base import Base


@pytest.mark.integration
class TestSyncServicesIntegration:
    """同期サービスの統合テスト"""
    
    @pytest.fixture
    async def test_db_engine(self):
        """テスト用データベースエンジン"""
        # SQLiteインメモリデータベースを使用
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        
        # テーブル作成
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        
        # クリーンアップ
        await engine.dispose()
    
    @pytest.fixture
    async def test_db_session(self, test_db_engine):
        """テスト用データベースセッション"""
        async_session_maker = sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            yield session
    
    @pytest.fixture
    def mock_data_source_service(self):
        """モックデータソースサービス"""
        from unittest.mock import Mock, AsyncMock
        service = Mock(spec=DataSourceService)
        mock_source = Mock()
        mock_source.id = 1
        service.get_jquants_source = AsyncMock(return_value=mock_source)
        return service
    
    @pytest.fixture
    def mock_jquants_manager(self):
        """モックJ-Quantsマネージャー"""
        from unittest.mock import Mock, AsyncMock
        
        manager = Mock(spec=JQuantsClientManager)
        
        # 企業データクライアント
        company_client = Mock()
        company_client.get_all_listed_companies = AsyncMock(return_value=[
            {"Code": "1234", "CompanyName": "Test Company 1"},
            {"Code": "5678", "CompanyName": "Test Company 2"},
            {"Code": "9012", "CompanyName": "Test Company 3"}
        ])
        manager.get_client = AsyncMock(return_value=company_client)
        
        # 株価データクライアント
        quotes_client = Mock()
        quotes_client.get_stock_prices_by_date = AsyncMock(side_effect=lambda date_str, codes=None: [
            {
                "Code": "1234",
                "Date": date_str,
                "Open": 1000,
                "High": 1100,
                "Low": 900,
                "Close": 1050,
                "Volume": 10000
            },
            {
                "Code": "5678",
                "Date": date_str,
                "Open": 2000,
                "High": 2200,
                "Low": 1900,
                "Close": 2100,
                "Volume": 20000
            }
        ])
        manager.get_daily_quotes_client = AsyncMock(return_value=quotes_client)
        
        return manager
    
    @pytest.mark.asyncio
    async def test_company_sync_service_integration(
        self,
        test_db_session,
        mock_data_source_service,
        mock_jquants_manager
    ):
        """CompanySyncServiceの統合テスト"""
        # サービスインスタンス作成
        service = CompanySyncService(
            db=test_db_session,
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_manager
        )
        
        # 同期実行
        result = await service.sync(data_source_id=1, sync_type='full')
        
        # 結果検証
        assert result['status'] == 'completed'
        assert result['total_companies'] == 3
        assert result['new_companies'] == 3
        
        # データベース確認
        companies = await test_db_session.execute(
            select(Company).order_by(Company.code)
        )
        company_list = companies.scalars().all()
        
        assert len(company_list) == 3
        assert company_list[0].code == "1234"
        assert company_list[0].company_name == "Test Company 1"
        
        # 履歴確認
        histories = await service.get_sync_history(limit=10)
        assert len(histories) == 1
        assert histories[0].status == "completed"
        assert histories[0].total_companies == 3
        
        # 最新ステータス確認
        latest = await service.get_latest_sync_status()
        assert latest is not None
        assert latest.status == "completed"
    
    @pytest.mark.asyncio
    async def test_daily_quotes_sync_service_integration(
        self,
        test_db_session,
        mock_data_source_service,
        mock_jquants_manager
    ):
        """DailyQuotesSyncServiceの統合テスト"""
        # 先に企業データを準備
        companies = [
            Company(code="1234", company_name="Test Company 1"),
            Company(code="5678", company_name="Test Company 2")
        ]
        for company in companies:
            test_db_session.add(company)
        await test_db_session.commit()
        
        # サービスインスタンス作成
        service = DailyQuotesSyncService(
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_manager,
            db=test_db_session
        )
        
        # 同期実行（2日分）
        from_date = date(2025, 7, 17)
        to_date = date(2025, 7, 18)
        
        result = await service.sync(
            data_source_id=1,
            sync_type='full',
            from_date=from_date,
            to_date=to_date
        )
        
        # 結果検証
        assert result['status'] == 'completed'
        assert result['total_records'] == 4  # 2銘柄 × 2日
        assert result['new_records'] == 4
        
        # データベース確認
        quotes = await test_db_session.execute(
            select(DailyQuote).order_by(DailyQuote.code, DailyQuote.trade_date)
        )
        quote_list = quotes.scalars().all()
        
        assert len(quote_list) == 4
        assert quote_list[0].code == "1234"
        assert quote_list[0].trade_date == from_date
        assert quote_list[0].close_price == 1050
        
        # 履歴確認（DBセッションがある場合）
        histories = await service.get_sync_history(limit=10)
        assert len(histories) == 1
        assert histories[0].status == "completed"
        assert histories[0].total_records == 4
    
    @pytest.mark.asyncio
    async def test_both_services_sequential(
        self,
        test_db_session,
        mock_data_source_service,
        mock_jquants_manager
    ):
        """両サービスの連続実行テスト"""
        # 1. 企業データ同期
        company_service = CompanySyncService(
            db=test_db_session,
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_manager
        )
        
        company_result = await company_service.sync(data_source_id=1)
        assert company_result['status'] == 'completed'
        
        # 2. 株価データ同期
        quotes_service = DailyQuotesSyncService(
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_manager,
            db=test_db_session
        )
        
        quotes_result = await quotes_service.sync(
            data_source_id=1,
            sync_type='incremental',
            target_date=date(2025, 7, 18)
        )
        assert quotes_result['status'] == 'completed'
        
        # 統合確認
        companies = await test_db_session.execute(select(Company))
        assert len(companies.scalars().all()) == 3
        
        quotes = await test_db_session.execute(select(DailyQuote))
        assert len(quotes.scalars().all()) == 2  # 2銘柄 × 1日
        
        # 統計情報の確認
        company_stats = await company_service.get_sync_statistics()
        assert company_stats['total_syncs'] == 1
        assert company_stats['status_breakdown']['completed'] == 1
        
        quotes_stats = await quotes_service.get_sync_statistics()
        assert quotes_stats['total_syncs'] == 1
        assert quotes_stats['latest_sync']['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(
        self,
        test_db_session,
        mock_data_source_service,
        mock_jquants_manager
    ):
        """エラーハンドリングの統合テスト"""
        # エラーを発生させるモックを設定
        mock_jquants_manager.get_client.side_effect = Exception("API Connection Error")
        
        service = CompanySyncService(
            db=test_db_session,
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_manager
        )
        
        # エラーが適切に処理されることを確認
        with pytest.raises(Exception) as exc_info:
            await service.sync(data_source_id=1)
        
        assert "API Connection Error" in str(exc_info.value)
        
        # 履歴が失敗として記録されていることを確認
        histories = await service.get_sync_history()
        assert len(histories) == 1
        assert histories[0].status == "failed"
        assert "API Connection Error" in histories[0].error_message
        
        # 統計情報にも反映されていることを確認
        stats = await service.get_sync_statistics()
        assert stats['status_breakdown']['failed'] == 1
        assert stats['latest_sync']['status'] == 'failed'
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_services(
        self,
        test_db_session,
        mock_data_source_service,
        mock_jquants_manager
    ):
        """複数サービスの並行実行テスト"""
        # 両サービスのインスタンス作成
        company_service = CompanySyncService(
            db=test_db_session,
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_manager
        )
        
        quotes_service = DailyQuotesSyncService(
            data_source_service=mock_data_source_service,
            jquants_client_manager=mock_jquants_manager,
            db=test_db_session
        )
        
        # 先に企業データを準備（株価同期のため）
        await company_service.sync(data_source_id=1)
        
        # 並行実行
        results = await asyncio.gather(
            company_service.sync(data_source_id=1),  # 2回目の企業同期
            quotes_service.sync(
                data_source_id=1,
                sync_type='incremental',
                target_date=date(2025, 7, 18)
            ),
            return_exceptions=True
        )
        
        # 両方とも成功していることを確認
        assert all(
            isinstance(result, dict) and result.get('status') == 'completed'
            for result in results
        )
        
        # 履歴が正しく記録されていることを確認
        company_histories = await company_service.get_sync_history()
        quotes_histories = await quotes_service.get_sync_history()
        
        assert len(company_histories) == 2  # 準備と並行実行の2回
        assert len(quotes_histories) == 1
        
        # すべて成功していることを確認
        assert all(h.status == "completed" for h in company_histories)
        assert all(h.status == "completed" for h in quotes_histories)