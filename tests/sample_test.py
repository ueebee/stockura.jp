"""
テスト環境動作確認用のサンプルテスト

新しいテスト環境が正しく動作することを確認するためのテストです。
"""

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.auth import JQuantsCredentials
from app.domain.entities.stock import Stock, StockCode
from tests.fixtures.factories.auth import JQuantsCredentialsFactory
from tests.fixtures.factories.stock import StockFactory, StockListFactory


class TestSampleEnvironment:
    """テスト環境の動作確認"""

    def test_factories_basic(self):
        """ファクトリーの基本動作確認"""
        # 認証情報ファクトリー
        credentials = JQuantsCredentialsFactory.build()
        assert credentials.email
        assert credentials.password
        assert credentials.refresh_token
        assert credentials.id_token

        # 株式情報ファクトリー
        stock = StockFactory.build()
        assert isinstance(stock.code, StockCode)
        assert stock.company_name
        assert stock.market_code

    def test_factories_with_traits(self):
        """ファクトリーのトレイト機能確認"""
        # テストユーザートレイト
        test_creds = JQuantsCredentialsFactory.build(test_user=True)
        assert test_creds.email == "test@example.com"
        assert test_creds.password == "test_password_123"

        # トヨタ自動車トレイト
        toyota = StockFactory.build(toyota=True)
        assert toyota.code.value == "7203"
        assert toyota.company_name == "トヨタ自動車"
        assert toyota.is_prime_market()

    def test_basic_client(self, test_client: TestClient):
        """基本的なテストクライアントの動作確認"""
        # ヘルスチェックエンドポイントへのアクセス
        response = test_client.get("/health")
        assert response.status_code in [200, 404]  # エンドポイントが存在しない場合も考慮

    def test_auth_client(self, auth_client: TestClient):
        """認証付きテストクライアントの動作確認"""
        # Authorization ヘッダーが設定されていることを確認
        assert "Authorization" in auth_client.headers
        assert auth_client.headers["Authorization"].startswith("Bearer ")

    def test_test_settings(self, app_settings):
        """テスト設定の動作確認"""
        assert app_settings.test_mode is True
        assert app_settings.env == "test"
        assert "test" in app_settings.database_url

    def test_mock_env_vars(self, mock_env_vars):
        """環境変数モックの動作確認"""
        import os
        
        # 環境変数をモック
        mock_env_vars("TEST_VAR", "test_value")
        assert os.getenv("TEST_VAR") == "test_value"

    def test_stock_list_factory(self):
        """株式リストファクトリーの動作確認"""
        stock_list = StockListFactory.build()
        assert len(stock_list.stocks) >= 3
        assert stock_list.updated_date

        # 追加の銘柄を生成
        additional_stocks = [StockFactory.build() for _ in range(2)]
        stock_list_with_extra = StockListFactory.build(add_stocks=additional_stocks)
        assert len(stock_list_with_extra.stocks) >= 5


@pytest.mark.unit
class TestSampleUnit:
    """単体テストのサンプル"""

    def test_credentials_validation(self):
        """認証情報のバリデーション"""
        # 正常なケース
        creds = JQuantsCredentialsFactory.build()
        assert creds.email
        assert creds.password

        # 期限切れトークンのケース
        expired_creds = JQuantsCredentialsFactory.build(with_expired_token=True)
        assert not expired_creds.has_valid_id_token()
        assert expired_creds.needs_refresh()

    def test_stock_filtering(self):
        """株式フィルタリング機能"""
        # プライム市場の銘柄を作成
        prime_stocks = [StockFactory.build(prime=True) for _ in range(3)]
        # スタンダード市場の銘柄を作成
        standard_stocks = [StockFactory.build(standard=True) for _ in range(2)]
        
        stock_list = StockListFactory.build(
            stocks=prime_stocks + standard_stocks
        )
        
        # プライム市場でフィルタリング
        from app.domain.entities.stock import MarketCode
        prime_filtered = stock_list.filter_by_market(MarketCode.PRIME)
        assert len(prime_filtered) == 3


@pytest.mark.integration
class TestSampleIntegration:
    """統合テストのサンプル（データベース接続が必要）"""

    @pytest.mark.skip(reason="データベース接続が必要")
    @pytest.mark.asyncio
    async def test_database_connection(self, db_session):
        """データベース接続の確認"""
        # このテストは実際のデータベース接続が必要
        from sqlalchemy import text
        
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1