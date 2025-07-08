"""
Companyモデルの包括的な単体テスト

このテストでは以下を検証します：
1. モデルの基本的なCRUD操作
2. バリデーション
3. インデックスの動作
4. タイムスタンプの自動更新
5. リレーションシップ
6. エッジケース
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, Sector17Master, Sector33Master, MarketMaster
from tests.fixtures import company_factory, assert_model_fields


class TestCompanyModel:
    """Companyモデルのテストクラス"""
    
    @pytest.mark.asyncio
    async def test_create_company_with_required_fields(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """必須フィールドのみで企業を作成できることを検証"""
        # Arrange
        company_data = {
            "code": "12345",
            "company_name": "テスト株式会社"
        }
        company = company_factory(**company_data)
        
        # Act
        async_session.add(company)
        await async_session.commit()
        await async_session.refresh(company)
        
        # Assert
        assert company.id is not None
        assert company.code == "12345"
        assert company.company_name == "テスト株式会社"
        assert company.is_active is True  # デフォルト値
        assert company.created_at is not None
        assert company.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_create_company_with_all_fields(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """すべてのフィールドを指定して企業を作成できることを検証"""
        # Arrange
        company_data = {
            "code": "67890",
            "company_name": "フル情報株式会社",
            "company_name_english": "Full Info Corporation",
            "sector17_code": "10",
            "sector33_code": "1050",
            "scale_category": "TOPIX Core30",
            "market_code": "0111",
            "margin_code": "01",
            "is_active": True
        }
        company = company_factory(**company_data)
        
        # Act
        async_session.add(company)
        await async_session.commit()
        await async_session.refresh(company)
        
        # Assert
        for field, expected_value in company_data.items():
            assert getattr(company, field) == expected_value
    
    @pytest.mark.asyncio
    async def test_unique_code_constraint(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """銘柄コードのユニーク制約が機能することを検証"""
        # Arrange
        code = "99999"
        company1 = company_factory(code=code, company_name="会社1")
        company2 = company_factory(code=code, company_name="会社2")
        
        # Act & Assert
        async_session.add(company1)
        await async_session.commit()
        
        async_session.add(company2)
        with pytest.raises(IntegrityError):
            await async_session.commit()
    
    @pytest.mark.asyncio
    async def test_update_company(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """企業情報の更新とupdated_atの自動更新を検証"""
        # Arrange
        company = company_factory(code="11111", company_name="更新前")
        async_session.add(company)
        await async_session.commit()
        await async_session.refresh(company)
        
        original_created_at = company.created_at
        original_updated_at = company.updated_at
        
        # 少し待つ（タイムスタンプの差を確認するため）
        await asyncio.sleep(0.1)
        
        # Act
        company.company_name = "更新後"
        company.sector17_code = "5"
        await async_session.commit()
        await async_session.refresh(company)
        
        # Assert
        assert company.company_name == "更新後"
        assert company.sector17_code == "5"
        assert company.created_at == original_created_at  # created_atは変わらない
        assert company.updated_at > original_updated_at  # updated_atは更新される
    
    @pytest.mark.asyncio
    async def test_soft_delete_with_is_active(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """is_activeフラグによる論理削除を検証"""
        # Arrange
        active_company = company_factory(code="22222", is_active=True)
        inactive_company = company_factory(code="33333", is_active=False)
        
        async_session.add_all([active_company, inactive_company])
        await async_session.commit()
        
        # Act
        active_stmt = select(Company).where(Company.is_active == True)
        active_results = await async_session.execute(active_stmt)
        active_companies = active_results.scalars().all()
        
        # Assert
        assert len(active_companies) == 1
        assert active_companies[0].code == "22222"
    
    @pytest.mark.asyncio
    async def test_company_search_by_name(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """企業名での検索機能を検証"""
        # Arrange
        companies = [
            company_factory(code="44444", company_name="トヨタ自動車"),
            company_factory(code="55555", company_name="本田技研工業"),
            company_factory(code="66666", company_name="日産自動車"),
        ]
        async_session.add_all(companies)
        await async_session.commit()
        
        # Act
        search_term = "自動車"
        stmt = select(Company).where(Company.company_name.contains(search_term))
        results = await async_session.execute(stmt)
        found_companies = results.scalars().all()
        
        # Assert
        assert len(found_companies) == 2
        found_codes = {c.code for c in found_companies}
        assert found_codes == {"44444", "66666"}
    
    @pytest.mark.asyncio
    async def test_company_filter_by_market_and_sector(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """市場区分と業種での複合フィルタリングを検証"""
        # Arrange
        companies = [
            company_factory(code="77777", market_code="0111", sector17_code="10"),
            company_factory(code="88888", market_code="0111", sector17_code="20"),
            company_factory(code="99999", market_code="0112", sector17_code="10"),
        ]
        async_session.add_all(companies)
        await async_session.commit()
        
        # Act
        stmt = select(Company).where(
            Company.market_code == "0111",
            Company.sector17_code == "10"
        )
        results = await async_session.execute(stmt)
        filtered_companies = results.scalars().all()
        
        # Assert
        assert len(filtered_companies) == 1
        assert filtered_companies[0].code == "77777"
    
    @pytest.mark.asyncio
    async def test_company_repr(self, company_factory):
        """__repr__メソッドの出力を検証"""
        # Arrange
        company = company_factory(code="REPR1", company_name="表示テスト株式会社")
        
        # Act
        repr_str = repr(company)
        
        # Assert
        assert repr_str == "<Company(code='REPR1', name='表示テスト株式会社')>"
    
    @pytest.mark.asyncio
    async def test_batch_insert_companies(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """大量の企業データの一括挿入を検証"""
        # Arrange
        companies = [
            company_factory(code=f"{10000 + i}", company_name=f"企業{i}")
            for i in range(100)
        ]
        
        # Act
        async_session.add_all(companies)
        await async_session.commit()
        
        # Assert
        count_stmt = select(func.count()).select_from(Company)
        result = await async_session.execute(count_stmt)
        count = result.scalar()
        assert count == 100
    
    @pytest.mark.asyncio
    async def test_company_with_null_optional_fields(
        self,
        async_session: AsyncSession
    ):
        """オプショナルフィールドがNULLの場合の動作を検証"""
        # Arrange
        company = Company(
            code="NULL1",
            company_name="NULL許可フィールドテスト"
            # 他のフィールドはNULL
        )
        
        # Act
        async_session.add(company)
        await async_session.commit()
        await async_session.refresh(company)
        
        # Assert
        assert company.company_name_english is None
        assert company.sector17_code is None
        assert company.sector33_code is None
        assert company.scale_category is None
        assert company.market_code is None
        assert company.margin_code is None
    
    @pytest.mark.asyncio
    async def test_company_field_lengths(
        self,
        async_session: AsyncSession,
        company_factory
    ):
        """フィールドの最大長を検証"""
        # Arrange
        company = company_factory(
            code="1" * 10,  # 最大10文字
            company_name="あ" * 200,  # 最大200文字
            company_name_english="A" * 200,  # 最大200文字
            scale_category="B" * 50  # 最大50文字
        )
        
        # Act
        async_session.add(company)
        await async_session.commit()
        await async_session.refresh(company)
        
        # Assert
        assert len(company.code) == 10
        assert len(company.company_name) == 200
        assert len(company.company_name_english) == 200
        assert len(company.scale_category) == 50
    
    @pytest.mark.asyncio
    async def test_company_query_performance_with_indexes(
        self,
        async_session: AsyncSession,
        company_factory,
        benchmark_timer
    ):
        """インデックスを使用したクエリのパフォーマンスを検証"""
        # Arrange
        # 1000件のテストデータを作成
        companies = []
        for i in range(1000):
            companies.append(
                company_factory(
                    code=f"{20000 + i}",
                    market_code=f"01{(i % 4) + 1:02d}",
                    sector17_code=str((i % 17) + 1),
                    is_active=i % 2 == 0
                )
            )
        
        async_session.add_all(companies)
        await async_session.commit()
        
        # Act & Assert
        # インデックスが効いているクエリ
        with benchmark_timer("indexed_query", max_seconds=0.1):
            stmt = select(Company).where(
                Company.is_active == True,
                Company.market_code == "0101"
            )
            result = await async_session.execute(stmt)
            _ = result.scalars().all()


class TestSector17Master:
    """Sector17Masterモデルのテストクラス"""
    
    @pytest.mark.asyncio
    async def test_create_sector17(self, async_session: AsyncSession):
        """17業種マスターの作成を検証"""
        # Arrange
        sector = Sector17Master(
            code="1",
            name="食品",
            name_english="Foods",
            description="食料品の製造・販売",
            display_order=1
        )
        
        # Act
        async_session.add(sector)
        await async_session.commit()
        await async_session.refresh(sector)
        
        # Assert
        assert sector.id is not None
        assert sector.code == "1"
        assert sector.name == "食品"
        assert sector.is_active is True
    
    @pytest.mark.asyncio
    async def test_sector17_unique_code(self, async_session: AsyncSession):
        """17業種コードのユニーク制約を検証"""
        # Arrange
        sector1 = Sector17Master(code="99", name="業種1")
        sector2 = Sector17Master(code="99", name="業種2")
        
        # Act & Assert
        async_session.add(sector1)
        await async_session.commit()
        
        async_session.add(sector2)
        with pytest.raises(IntegrityError):
            await async_session.commit()


class TestSector33Master:
    """Sector33Masterモデルのテストクラス"""
    
    @pytest.mark.asyncio
    async def test_create_sector33_with_sector17_relation(
        self,
        async_session: AsyncSession
    ):
        """33業種マスターの作成と17業種との関連を検証"""
        # Arrange
        sector33 = Sector33Master(
            code="1050",
            name="水産",
            sector17_code="1",  # 食品に属する
            display_order=1
        )
        
        # Act
        async_session.add(sector33)
        await async_session.commit()
        await async_session.refresh(sector33)
        
        # Assert
        assert sector33.id is not None
        assert sector33.code == "1050"
        assert sector33.sector17_code == "1"
        assert sector33.is_active is True


class TestMarketMaster:
    """MarketMasterモデルのテストクラス"""
    
    @pytest.mark.asyncio
    async def test_create_market_master(self, async_session: AsyncSession):
        """市場マスターの作成を検証"""
        # Arrange
        market = MarketMaster(
            code="0111",
            name="東証プライム",
            name_english="TSE Prime",
            description="東京証券取引所プライム市場",
            display_order=1
        )
        
        # Act
        async_session.add(market)
        await async_session.commit()
        await async_session.refresh(market)
        
        # Assert
        assert market.id is not None
        assert market.code == "0111"
        assert market.name == "東証プライム"
        assert market.is_active is True
    
    @pytest.mark.asyncio
    async def test_market_active_order_index(
        self,
        async_session: AsyncSession
    ):
        """市場マスターのアクティブ・表示順インデックスを検証"""
        # Arrange
        markets = [
            MarketMaster(code="M1", name="市場1", display_order=2, is_active=True),
            MarketMaster(code="M2", name="市場2", display_order=1, is_active=True),
            MarketMaster(code="M3", name="市場3", display_order=3, is_active=False),
        ]
        async_session.add_all(markets)
        await async_session.commit()
        
        # Act
        stmt = select(MarketMaster).where(
            MarketMaster.is_active == True
        ).order_by(MarketMaster.display_order)
        
        result = await async_session.execute(stmt)
        active_markets = result.scalars().all()
        
        # Assert
        assert len(active_markets) == 2
        assert active_markets[0].code == "M2"
        assert active_markets[1].code == "M1"


# 非同期処理のためのインポート
import asyncio