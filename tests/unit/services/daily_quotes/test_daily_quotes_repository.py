"""
DailyQuotesRepositoryの単体テスト
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.daily_quotes.daily_quotes_repository import DailyQuotesRepository
from app.models.daily_quote import DailyQuote
from app.models.company import Company


class TestDailyQuotesRepository:
    """DailyQuotesRepositoryのテストクラス"""
    
    @pytest_asyncio.fixture
    async def mock_session(self):
        """モックセッションを作成"""
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest_asyncio.fixture
    async def repository(self, mock_session):
        """リポジトリインスタンスを作成"""
        return DailyQuotesRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_find_by_code_and_date_found(self, repository, mock_session):
        """銘柄コードと日付で検索（見つかる場合）"""
        # モックデータ
        mock_quote = DailyQuote(
            code="1234",
            trade_date=date(2024, 1, 15),
            open_price=Decimal("1000")
        )
        
        # モックの設定
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_quote
        mock_session.execute.return_value = mock_result
        
        # テスト実行
        result = await repository.find_by_code_and_date("1234", date(2024, 1, 15))
        
        assert result == mock_quote
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_code_and_date_not_found(self, repository, mock_session):
        """銘柄コードと日付で検索（見つからない場合）"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # テスト実行
        result = await repository.find_by_code_and_date("9999", date(2024, 1, 15))
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_company_exists_true(self, repository, mock_session):
        """企業存在確認（存在する場合）"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "1234"
        mock_session.execute.return_value = mock_result
        
        # テスト実行
        result = await repository.check_company_exists("1234")
        
        assert result is True
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_company_exists_false(self, repository, mock_session):
        """企業存在確認（存在しない場合）"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # テスト実行
        result = await repository.check_company_exists("9999")
        
        assert result is False
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_company_codes(self, repository, mock_session):
        """アクティブな企業コードリスト取得"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.all.return_value = [("1234",), ("5678",), ("9012",)]
        mock_session.execute.return_value = mock_result
        
        # テスト実行
        result = await repository.get_active_company_codes()
        
        assert result == ["1234", "5678", "9012"]
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_latest_date_by_code(self, repository, mock_session):
        """銘柄の最新取引日取得"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = date(2024, 1, 15)
        mock_session.execute.return_value = mock_result
        
        # テスト実行
        result = await repository.find_latest_date_by_code("1234")
        
        assert result == date(2024, 1, 15)
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_commit_batch(self, repository, mock_session):
        """バッチコミット"""
        # テスト実行
        await repository.commit_batch()
        
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback(self, repository, mock_session):
        """ロールバック"""
        # テスト実行
        await repository.rollback()
        
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_new_records(self, repository, mock_session):
        """一括更新（新規レコード）"""
        # キャッシュを初期化
        repository._company_cache = {"1234": True, "5678": True}
        
        # テストデータ
        quotes_data = [
            {
                "code": "1234",
                "trade_date": date(2024, 1, 15),
                "open_price": Decimal("1000"),
                "close_price": Decimal("1050")
            },
            {
                "code": "5678",
                "trade_date": date(2024, 1, 15),
                "open_price": Decimal("2000"),
                "close_price": Decimal("2100")
            }
        ]
        
        # find_by_code_and_dateのモック（全て新規）
        with patch.object(repository, 'find_by_code_and_date', return_value=None):
            result = await repository.bulk_upsert(quotes_data)
        
        new_count, updated_count, skipped_count = result
        assert new_count == 2
        assert updated_count == 0
        assert skipped_count == 0
        
        # add が2回呼ばれることを確認
        assert mock_session.add.call_count == 2
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_updated_records(self, repository, mock_session):
        """一括更新（既存レコード更新）"""
        # キャッシュを初期化
        repository._company_cache = {"1234": True}
        
        # 既存レコードのモック
        existing_quote = DailyQuote(
            code="1234",
            trade_date=date(2024, 1, 15),
            open_price=Decimal("1000")
        )
        
        # テストデータ
        quotes_data = [
            {
                "code": "1234",
                "trade_date": date(2024, 1, 15),
                "open_price": Decimal("1100"),
                "close_price": Decimal("1150")
            }
        ]
        
        # find_by_code_and_dateのモック（既存レコードあり）
        with patch.object(repository, 'find_by_code_and_date', return_value=existing_quote):
            result = await repository.bulk_upsert(quotes_data)
        
        new_count, updated_count, skipped_count = result
        assert new_count == 0
        assert updated_count == 1
        assert skipped_count == 0
        
        # 既存レコードが更新されたことを確認
        assert existing_quote.open_price == Decimal("1100")
        assert existing_quote.close_price == Decimal("1150")
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_skipped_records(self, repository, mock_session):
        """一括更新（企業マスタに存在しない）"""
        # キャッシュを初期化（9999は存在しない）
        repository._company_cache = {"1234": True}
        
        # テストデータ
        quotes_data = [
            {
                "code": "9999",  # 存在しない企業
                "trade_date": date(2024, 1, 15),
                "open_price": Decimal("1000")
            }
        ]
        
        result = await repository.bulk_upsert(quotes_data)
        
        new_count, updated_count, skipped_count = result
        assert new_count == 0
        assert updated_count == 0
        assert skipped_count == 1
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_batch_commit(self, repository, mock_session):
        """一括更新（100件ごとのバッチコミット）"""
        # キャッシュを初期化
        repository._company_cache = {str(i): True for i in range(150)}
        
        # 150件のテストデータ
        quotes_data = [
            {
                "code": str(i),
                "trade_date": date(2024, 1, 15),
                "open_price": Decimal("1000")
            }
            for i in range(150)
        ]
        
        # find_by_code_and_dateのモック（全て新規）
        with patch.object(repository, 'find_by_code_and_date', return_value=None):
            await repository.bulk_upsert(quotes_data)
        
        # 100件で1回 + 最後に1回 = 合計2回のコミット
        assert mock_session.commit.call_count == 2
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, repository):
        """キャッシュクリア"""
        # キャッシュを設定
        repository._company_cache = {"1234": True}
        
        # クリア実行
        repository.clear_cache()
        
        assert repository._company_cache is None