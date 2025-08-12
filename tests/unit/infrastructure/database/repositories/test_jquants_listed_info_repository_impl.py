"""Tests for JQuantsListedInfoRepositoryImpl."""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.jquants_listed_info import JQuantsListedInfo
from app.domain.value_objects.stock_code import StockCode
from app.infrastructure.database.models.jquants_listed_info import ListedInfoModel
from app.infrastructure.repositories.database.jquants_listed_info_repository_impl import (
    JQuantsListedInfoRepositoryImpl,
)
from app.infrastructure.database.mappers.jquants_listed_info_mapper import JQuantsListedInfoMapper


class TestJQuantsListedInfoRepositoryImpl:
    """JQuantsListedInfoRepositoryImpl tests."""

    def setup_method(self):
        """テストのセットアップ"""
        self.session = AsyncMock(spec=AsyncSession)
        self.mapper = JQuantsListedInfoMapper()
        self.repository = JQuantsListedInfoRepositoryImpl(self.session, self.mapper)

    def _create_test_entity(
        self, date_value: date = date(2024, 1, 4), code: str = "7203"
    ) -> JQuantsListedInfo:
        """テスト用エンティティを作成"""
        return JQuantsListedInfo(
            date=date_value,
            code=StockCode(code),
            company_name="トヨタ自動車",
            company_name_english="TOYOTA MOTOR CORPORATION",
            sector_17_code="6",
            sector_17_code_name="自動車・輸送機",
            sector_33_code="3700",
            sector_33_code_name="輸送用機器",
            scale_category="TOPIX Large70",
            market_code="0111",
            market_code_name="プライム",
            margin_code="1",
            margin_code_name="信用",
        )

    def _create_test_model(
        self, date_value: date = date(2024, 1, 4), code: str = "7203"
    ) -> ListedInfoModel:
        """テスト用モデルを作成"""
        return ListedInfoModel(
            date=date_value,
            code=code,
            company_name="トヨタ自動車",
            company_name_english="TOYOTA MOTOR CORPORATION",
            sector_17_code="6",
            sector_17_code_name="自動車・輸送機",
            sector_33_code="3700",
            sector_33_code_name="輸送用機器",
            scale_category="TOPIX Large70",
            market_code="0111",
            market_code_name="プライム",
            margin_code="1",
            margin_code_name="信用",
        )

    @pytest.mark.asyncio
    async def test_save_all_single_entity(self):
        """単一エンティティの保存が正しく動作することを確認"""
        # テストデータ
        entity = self._create_test_entity()
        entities = [entity]

        # execute のモック設定
        self.session.execute.return_value = AsyncMock()

        # 実行
        await self.repository.save_all(entities)

        # 検証
        self.session.execute.assert_called_once()
        self.session.flush.assert_called_once()
        
        # execute に渡された引数を確認
        call_args = self.session.execute.call_args[0][0]
        # PostgreSQL の insert 文が作成されていることを確認
        assert hasattr(call_args, 'table')

    @pytest.mark.asyncio
    async def test_save_all_multiple_entities(self):
        """複数エンティティの保存が正しく動作することを確認"""
        # テストデータ
        entities = [
            self._create_test_entity(date(2024, 1, 4), "7203"),
            self._create_test_entity(date(2024, 1, 4), "9984"),
            self._create_test_entity(date(2024, 1, 4), "6758"),
        ]

        # execute のモック設定
        self.session.execute.return_value = AsyncMock()

        # 実行
        await self.repository.save_all(entities)

        # 検証
        self.session.execute.assert_called_once()
        self.session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_all_empty_list(self):
        """空のリストを渡した場合、何も実行されないことを確認"""
        # 実行
        await self.repository.save_all([])

        # 検証
        self.session.execute.assert_not_called()
        self.session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_by_code_and_date_found(self):
        """コードと日付で検索して見つかる場合のテスト"""
        # モックの設定
        model = self._create_test_model()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = model
        self.session.execute.return_value = result_mock

        # 実行
        result = await self.repository.find_by_code_and_date(
            StockCode("7203"), date(2024, 1, 4)
        )

        # 検証
        assert result is not None
        assert result.code.value == "7203"
        assert result.date == date(2024, 1, 4)
        assert result.company_name == "トヨタ自動車"
        self.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_code_and_date_not_found(self):
        """コードと日付で検索して見つからない場合のテスト"""
        # モックの設定
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute.return_value = result_mock

        # 実行
        result = await self.repository.find_by_code_and_date(
            StockCode("9999"), date(2024, 1, 4)
        )

        # 検証
        assert result is None
        self.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_all_by_date(self):
        """日付で全件検索のテスト"""
        # モックの設定
        models = [
            self._create_test_model(date(2024, 1, 4), "7203"),
            self._create_test_model(date(2024, 1, 4), "9984"),
            self._create_test_model(date(2024, 1, 4), "6758"),
        ]
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = models
        result_mock.scalars.return_value = scalars_mock
        self.session.execute.return_value = result_mock

        # 実行
        results = await self.repository.find_all_by_date(date(2024, 1, 4))

        # 検証
        assert len(results) == 3
        assert all(isinstance(r, JQuantsListedInfo) for r in results)
        assert results[0].code.value == "7203"
        assert results[1].code.value == "9984"
        assert results[2].code.value == "6758"
        self.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_all_by_date_empty(self):
        """日付で検索して結果が空の場合のテスト"""
        # モックの設定
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock.scalars.return_value = scalars_mock
        self.session.execute.return_value = result_mock

        # 実行
        results = await self.repository.find_all_by_date(date(2024, 1, 4))

        # 検証
        assert len(results) == 0
        self.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_latest_by_code_found(self):
        """コードで最新情報を検索して見つかる場合のテスト"""
        # モックの設定
        model = self._create_test_model(date(2024, 1, 5), "7203")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = model
        self.session.execute.return_value = result_mock

        # 実行
        result = await self.repository.find_latest_by_code(StockCode("7203"))

        # 検証
        assert result is not None
        assert result.code.value == "7203"
        assert result.date == date(2024, 1, 5)
        self.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_latest_by_code_not_found(self):
        """コードで最新情報を検索して見つからない場合のテスト"""
        # モックの設定
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute.return_value = result_mock

        # 実行
        result = await self.repository.find_latest_by_code(StockCode("9999"))

        # 検証
        assert result is None
        self.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_date(self):
        """日付でデータを削除するテスト"""
        # モックの設定
        result_mock = MagicMock()
        result_mock.rowcount = 5
        self.session.execute.return_value = result_mock

        # 実行
        deleted_count = await self.repository.delete_by_date(date(2024, 1, 4))

        # 検証
        assert deleted_count == 5
        self.session.execute.assert_called_once()
        self.session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_date_no_records(self):
        """削除対象のレコードがない場合のテスト"""
        # モックの設定
        result_mock = MagicMock()
        result_mock.rowcount = 0
        self.session.execute.return_value = result_mock

        # 実行
        deleted_count = await self.repository.delete_by_date(date(2024, 1, 4))

        # 検証
        assert deleted_count == 0
        self.session.execute.assert_called_once()
        self.session.flush.assert_called_once()

    def test_mapper_integration(self):
        """Mapper が正しく統合されていることを確認"""
        # テストデータ
        model = self._create_test_model()
        entity = self._create_test_entity()

        # モデルからエンティティへの変換
        converted_entity = self.repository._mapper.to_entity(model)
        assert isinstance(converted_entity, JQuantsListedInfo)
        assert converted_entity.date == model.date
        assert converted_entity.code.value == model.code

        # エンティティからモデルへの変換
        converted_model = self.repository._mapper.to_model(entity)
        assert isinstance(converted_model, ListedInfoModel)
        assert converted_model.date == entity.date
        assert converted_model.code == entity.code.value