"""
株価データAPIエンドポイントのテスト
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date
from fastapi.testclient import TestClient
from decimal import Decimal

from app.main import app
from app.models.daily_quote import DailyQuote, DailyQuotesSyncHistory


class TestDailyQuotesAPI:
    """株価データAPIエンドポイントのテスト"""

    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)

    @pytest.fixture
    def sample_daily_quotes(self):
        """サンプル株価データ"""
        quotes = []
        for i in range(1, 6):
            quote = Mock(spec=DailyQuote)
            quote.id = i
            quote.code = f"123{i}"
            quote.trade_date = date(2024, 12, 26)
            quote.open_price = Decimal(f"{1000 + i * 10}.00")
            quote.high_price = Decimal(f"{1100 + i * 10}.00")
            quote.low_price = Decimal(f"{950 + i * 10}.00")
            quote.close_price = Decimal(f"{1050 + i * 10}.00")
            quote.volume = 1000000 + i * 100000
            quote.turnover_value = None
            quote.adjustment_factor = Decimal("1.0")
            quote.adjustment_open = None
            quote.adjustment_high = None
            quote.adjustment_low = None
            quote.adjustment_close = None
            quote.adjustment_volume = None
            quote.upper_limit_flag = False
            quote.lower_limit_flag = False
            quote.morning_open = None
            quote.morning_high = None
            quote.morning_low = None
            quote.morning_close = None
            quote.morning_volume = None
            quote.morning_turnover_value = None
            quote.afternoon_open = None
            quote.afternoon_high = None
            quote.afternoon_low = None
            quote.afternoon_close = None
            quote.afternoon_volume = None
            quote.afternoon_turnover_value = None
            quote.created_at = datetime(2024, 12, 26, 10, 0, 0)
            quote.updated_at = datetime(2024, 12, 26, 10, 0, 0)
            quotes.append(quote)
        return quotes

    @pytest.fixture
    def sample_sync_history(self):
        """サンプル同期履歴"""
        history = Mock(spec=DailyQuotesSyncHistory)
        history.id = 1
        history.sync_date = date(2024, 12, 26)
        history.sync_type = "full"
        history.status = "completed"
        history.target_companies = 100
        history.total_records = 5000
        history.new_records = 4000
        history.updated_records = 800
        history.skipped_records = 200
        history.started_at = datetime(2024, 12, 26, 9, 0, 0)
        history.completed_at = datetime(2024, 12, 26, 9, 30, 0)
        history.error_message = None
        history.from_date = date(2024, 12, 25)
        history.to_date = date(2024, 12, 26)
        history.specific_codes = None
        return history

    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_get_daily_quotes_by_code_success(self, mock_get_session, client, sample_daily_quotes):
        """特定銘柄の株価データ取得の成功テスト"""
        # データベースセッションをモック
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        # 総件数をモック
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(sample_daily_quotes)
        
        # データ取得をモック
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = sample_daily_quotes[:3]
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/1234")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["total"] == len(sample_daily_quotes)
        assert len(data["data"]) == 3

    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_get_daily_quotes_by_code_with_date_range(self, mock_get_session, client, sample_daily_quotes):
        """期間指定での特定銘柄株価データ取得テスト"""
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = sample_daily_quotes[:2]
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # テスト実行
        response = client.get(
            "/api/v1/daily-quotes/1234",
            params={
                "from_date": "2024-12-01",
                "to_date": "2024-12-26",
                "limit": 10,
                "offset": 0
            }
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total"] == 2
        assert data["pagination"]["limit"] == 10

    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_get_daily_quotes_multiple_codes(self, mock_get_session, client, sample_daily_quotes):
        """複数銘柄の株価データ取得テスト"""
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 3
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = sample_daily_quotes[:3]
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # テスト実行
        response = client.get(
            "/api/v1/daily-quotes/",
            params={
                "codes": "1234,5678,9012",
                "limit": 50
            }
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total"] == 3
        assert len(data["data"]) == 3

    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_get_daily_quotes_by_date(self, mock_get_session, client, sample_daily_quotes):
        """特定日の全銘柄株価データ取得テスト"""
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(sample_daily_quotes)
        
        mock_data_result = Mock()
        mock_data_result.scalars.return_value.all.return_value = sample_daily_quotes
        
        mock_db.execute.side_effect = [mock_count_result, mock_data_result]
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/by-date/2024-12-26")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total"] == len(sample_daily_quotes)
        assert len(data["data"]) == len(sample_daily_quotes)

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    def test_sync_daily_quotes_success(self, mock_get_sync_service, client):
        """株価データ同期の成功テスト"""
        # 同期サービスをモック
        mock_sync_service = Mock()
        mock_get_sync_service.return_value = mock_sync_service
        
        # テスト実行
        response = client.post(
            "/api/v1/daily-quotes/sync",
            json={
                "data_source_id": 1,
                "sync_type": "incremental",
                "target_date": "2024-12-26"
            }
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert "sync_id" in data
        assert "message" in data
        assert "status" in data
        assert data["status"] == "queued"
        assert "incremental" in data["message"]

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    def test_sync_daily_quotes_full_sync(self, mock_get_sync_service, client):
        """全データ同期のテスト"""
        mock_sync_service = Mock()
        mock_get_sync_service.return_value = mock_sync_service
        
        # テスト実行
        response = client.post(
            "/api/v1/daily-quotes/sync",
            json={
                "data_source_id": 1,
                "sync_type": "full",
                "from_date": "2024-12-01",
                "to_date": "2024-12-26"
            }
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "full" in data["message"]

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    def test_sync_daily_quotes_single_stock(self, mock_get_sync_service, client):
        """特定銘柄同期のテスト"""
        mock_sync_service = Mock()
        mock_get_sync_service.return_value = mock_sync_service
        
        # テスト実行
        response = client.post(
            "/api/v1/daily-quotes/sync",
            json={
                "data_source_id": 1,
                "sync_type": "single_stock",
                "codes": ["1234", "5678"],
                "target_date": "2024-12-26"
            }
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "single_stock" in data["message"]

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_get_sync_history_success(self, mock_get_session, mock_get_sync_service, client):
        """同期履歴取得の成功テスト"""
        # 同期サービスをモック
        mock_sync_service = Mock()
        mock_sync_service.get_sync_history = AsyncMock(return_value=[])
        mock_get_sync_service.return_value = mock_sync_service
        
        # データベースセッションをモック
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 3
        mock_db.execute.return_value = mock_count_result
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/sync/history")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_get_sync_history_with_status_filter(self, mock_get_session, mock_get_sync_service, client):
        """ステータスフィルタ付き同期履歴取得のテスト"""
        mock_sync_service = Mock()
        mock_sync_service.get_sync_history = AsyncMock(return_value=[])
        mock_get_sync_service.return_value = mock_sync_service
        
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1
        mock_db.execute.return_value = mock_count_result
        
        # テスト実行
        response = client.get(
            "/api/v1/daily-quotes/sync/history",
            params={"status": "failed"}
        )
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    def test_get_sync_status_success(self, mock_get_sync_service, client, sample_sync_history):
        """同期ステータス取得の成功テスト"""
        mock_sync_service = Mock()
        mock_sync_service.get_sync_status = AsyncMock(return_value=sample_sync_history)
        mock_get_sync_service.return_value = mock_sync_service
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/sync/status/1")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert "sync_history" in data
        assert "is_running" in data
        assert "progress_percentage" in data
        assert data["is_running"] is False
        assert data["progress_percentage"] == 100.0

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    def test_get_sync_status_not_found(self, mock_get_sync_service, client):
        """同期履歴が見つからない場合のテスト"""
        mock_sync_service = Mock()
        mock_sync_service.get_sync_status = AsyncMock(return_value=None)
        mock_get_sync_service.return_value = mock_sync_service
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/sync/status/999")
        
        # 結果検証
        assert response.status_code == 404
        assert "同期履歴が見つかりません" in response.json()["detail"]

    @patch('app.api.v1.endpoints.daily_quotes.get_daily_quotes_sync_service')
    def test_get_sync_status_running(self, mock_get_sync_service, client, sample_sync_history):
        """実行中の同期ステータステスト"""
        # 実行中の履歴に変更
        sample_sync_history.status = "running"
        sample_sync_history.total_records = 1000
        sample_sync_history.new_records = 300
        sample_sync_history.updated_records = 200
        sample_sync_history.skipped_records = 100
        sample_sync_history.completed_at = None
        
        mock_sync_service = Mock()
        mock_sync_service.get_sync_status = AsyncMock(return_value=sample_sync_history)
        mock_get_sync_service.return_value = mock_sync_service
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/sync/status/1")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is True
        assert data["progress_percentage"] == 60.0  # (300+200+100)/1000 * 100

    def test_health_check(self, client):
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/api/v1/daily-quotes/health")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "daily_quotes"
        assert "timestamp" in data

    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_get_daily_quotes_stats(self, mock_get_session, client):
        """統計情報取得エンドポイントのテスト"""
        mock_db = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        # 各統計情報のモック
        mock_results = [
            Mock(scalar=Mock(return_value=10000)),  # total_records
            Mock(scalar=Mock(return_value=100)),    # unique_codes
            Mock(scalar=Mock(return_value=date(2024, 12, 26))),  # latest_date
            Mock(scalar=Mock(return_value=date(2024, 1, 1)))     # earliest_date
        ]
        
        mock_db.execute.side_effect = mock_results
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/stats")
        
        # 結果検証
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 10000
        assert data["unique_codes"] == 100
        assert data["latest_date"] == "2024-12-26"
        assert data["earliest_date"] == "2024-01-01"
        assert "last_updated" in data

    def test_validation_errors(self, client):
        """バリデーションエラーのテスト"""
        # 無効な日付形式
        response = client.get("/api/v1/daily-quotes/by-date/invalid-date")
        assert response.status_code == 422
        
        # 無効なlimit値
        response = client.get("/api/v1/daily-quotes/1234", params={"limit": 0})
        assert response.status_code == 422
        
        # 無効なoffset値
        response = client.get("/api/v1/daily-quotes/1234", params={"offset": -1})
        assert response.status_code == 422
        
        # 無効な同期リクエスト
        response = client.post(
            "/api/v1/daily-quotes/sync",
            json={"data_source_id": "invalid"}
        )
        assert response.status_code == 422

    @patch('app.api.v1.endpoints.daily_quotes.get_session')
    def test_database_error_handling(self, mock_get_session, client):
        """データベースエラーハンドリングのテスト"""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection failed")
        mock_get_session.return_value.__aenter__.return_value = mock_db
        
        # テスト実行
        response = client.get("/api/v1/daily-quotes/stats")
        
        # 結果検証
        assert response.status_code == 500
        assert "統計情報の取得に失敗しました" in response.json()["detail"]