"""
CompanyRepositoryの単体テスト
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.company.company_repository import CompanyRepository
from app.services.interfaces.company_sync_interfaces import RepositoryError
from app.models.company import Company


class TestCompanyRepository:
    """CompanyRepositoryのテストクラス"""
    
    @pytest.fixture
    def mock_db_session(self):
        """モックのデータベースセッション"""
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = Mock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_db_session):
        """テスト用のリポジトリインスタンス"""
        return CompanyRepository(db=mock_db_session)
    
    @pytest.fixture
    def sample_company(self):
        """サンプルの企業エンティティ"""
        company = Company(
            code="1234",
            company_name="テスト株式会社",
            company_name_english="Test Corp",
            is_active=True
        )
        return company
    
    @pytest.fixture
    def sample_company_data(self):
        """サンプルの企業データ（辞書形式）"""
        return {
            "code": "1234",
            "company_name": "テスト株式会社",
            "company_name_english": "Test Corp",
            "sector17_code": "1",
            "is_active": True
        }
    
    @pytest.mark.asyncio
    async def test_find_by_code_success(self, repository, mock_db_session, sample_company):
        """銘柄コードでの検索成功テスト"""
        # モックの設定
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_company
        mock_db_session.execute.return_value = mock_result
        
        # 実行
        result = await repository.find_by_code("1234")
        
        # 検証
        assert result == sample_company
        assert result.code == "1234"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_code_not_found(self, repository, mock_db_session):
        """企業が見つからない場合のテスト"""
        # モックの設定
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # 実行
        result = await repository.find_by_code("9999")
        
        # 検証
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_by_code_error(self, repository, mock_db_session):
        """検索エラーのテスト"""
        # モックの設定
        mock_db_session.execute.side_effect = Exception("Database error")
        
        # 実行と検証
        with pytest.raises(RepositoryError) as exc_info:
            await repository.find_by_code("1234")
        
        assert "Failed to find company by code" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_find_all_active_success(self, repository, mock_db_session):
        """アクティブな企業全取得の成功テスト"""
        # モックの設定
        companies = [
            Company(code="1234", company_name="企業1", is_active=True),
            Company(code="5678", company_name="企業2", is_active=True)
        ]
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = companies
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result
        
        # 実行
        result = await repository.find_all_active()
        
        # 検証
        assert len(result) == 2
        assert all(c.is_active for c in result)
    
    @pytest.mark.asyncio
    async def test_save_success(self, repository, mock_db_session, sample_company_data):
        """企業データ保存の成功テスト"""
        # 実行
        result = await repository.save(sample_company_data)
        
        # 検証
        assert isinstance(result, Company)
        assert result.code == sample_company_data["code"]
        assert result.company_name == sample_company_data["company_name"]
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_error(self, repository, mock_db_session, sample_company_data):
        """保存エラーのテスト"""
        # モックの設定
        mock_db_session.flush.side_effect = Exception("Save error")
        
        # 実行と検証
        with pytest.raises(RepositoryError) as exc_info:
            await repository.save(sample_company_data)
        
        assert "Failed to save company" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_db_session, sample_company):
        """企業データ更新の成功テスト"""
        # 更新データ
        update_data = {
            "company_name": "更新後株式会社",
            "sector17_code": "2"
        }
        
        # 実行
        result = await repository.update(sample_company, update_data)
        
        # 検証
        assert result.company_name == "更新後株式会社"
        assert result.sector17_code == "2"
        assert result.updated_at is not None
        mock_db_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_no_changes(self, repository, mock_db_session, sample_company):
        """変更がない場合の更新テスト"""
        # 現在の値と同じデータ
        update_data = {
            "company_name": sample_company.company_name
        }
        
        # 実行
        result = await repository.update(sample_company, update_data)
        
        # 検証
        assert result == sample_company
        # flushは呼ばれない（変更がないため）
        mock_db_session.flush.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_skip_code_field(self, repository, mock_db_session, sample_company):
        """codeフィールドの更新スキップテスト"""
        # codeフィールドを含む更新データ
        update_data = {
            "code": "9999",  # これはスキップされる
            "company_name": "更新後株式会社"
        }
        
        # 実行
        result = await repository.update(sample_company, update_data)
        
        # 検証
        assert result.code == "1234"  # 変更されない
        assert result.company_name == "更新後株式会社"
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_success(self, repository, mock_db_session):
        """一括更新の成功テスト"""
        # モックの設定
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = ["1234"]  # 既存のコード
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result
        
        # テストデータ
        companies_data = [
            {"code": "1234", "company_name": "既存企業（更新）"},
            {"code": "5678", "company_name": "新規企業"},
            {"code": "9012", "company_name": "新規企業2"}
        ]
        
        # 実行
        result = await repository.bulk_upsert(companies_data)
        
        # 検証
        assert result["new_count"] == 2
        assert result["updated_count"] == 1
        assert mock_db_session.execute.call_count >= 4  # SELECT + 3 UPSERTs
        assert mock_db_session.flush.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_list(self, repository, mock_db_session):
        """空のリストでの一括更新テスト"""
        # 実行
        result = await repository.bulk_upsert([])
        
        # 検証
        assert result["new_count"] == 0
        assert result["updated_count"] == 0
        mock_db_session.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_bulk_upsert_large_batch(self, repository, mock_db_session):
        """大量データのバッチ処理テスト"""
        # モックの設定
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []  # 全て新規
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result
        
        # 150件のテストデータ（バッチサイズ100を超える）
        companies_data = [
            {"code": f"{i:04d}", "company_name": f"企業{i}"}
            for i in range(150)
        ]
        
        # 実行
        result = await repository.bulk_upsert(companies_data)
        
        # 検証
        assert result["new_count"] == 150
        assert result["updated_count"] == 0
        # バッチ処理のため、flushは2回呼ばれる
        assert mock_db_session.flush.call_count == 2
    
    @pytest.mark.asyncio
    async def test_deactivate_companies_exclude_codes(self, repository, mock_db_session):
        """特定コード除外での非アクティブ化テスト"""
        # モックの設定
        mock_result = Mock()
        mock_result.rowcount = 5
        mock_db_session.execute.return_value = mock_result
        
        # 実行
        result = await repository.deactivate_companies(["1234", "5678"])
        
        # 検証
        assert result == 5
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_companies_all(self, repository, mock_db_session):
        """全企業非アクティブ化テスト"""
        # モックの設定
        mock_result = Mock()
        mock_result.rowcount = 10
        mock_db_session.execute.return_value = mock_result
        
        # 実行
        result = await repository.deactivate_companies([])
        
        # 検証
        assert result == 10
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_commit_success(self, repository, mock_db_session):
        """コミット成功テスト"""
        # 実行
        await repository.commit()
        
        # 検証
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_commit_error(self, repository, mock_db_session):
        """コミットエラーテスト"""
        # モックの設定
        mock_db_session.commit.side_effect = Exception("Commit error")
        
        # 実行と検証
        with pytest.raises(RepositoryError) as exc_info:
            await repository.commit()
        
        assert "Failed to commit transaction" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_rollback_success(self, repository, mock_db_session):
        """ロールバック成功テスト"""
        # 実行
        await repository.rollback()
        
        # 検証
        mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_error(self, repository, mock_db_session):
        """ロールバックエラーテスト"""
        # モックの設定
        mock_db_session.rollback.side_effect = Exception("Rollback error")
        
        # 実行と検証
        with pytest.raises(RepositoryError) as exc_info:
            await repository.rollback()
        
        assert "Failed to rollback transaction" in str(exc_info.value)