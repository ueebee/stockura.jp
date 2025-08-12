"""Listed info repository implementation."""
from datetime import date
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domain.entities.jquants_listed_info import JQuantsListedInfo
from app.domain.value_objects.stock_code import StockCode
from app.domain.repositories.jquants_listed_info_repository_interface import JQuantsListedInfoRepositoryInterface
from app.infrastructure.database.models.jquants_listed_info import ListedInfoModel
from app.infrastructure.database.mappers.jquants_listed_info_mapper import ListedInfoMapper

logger = get_logger(__name__)


class ListedInfoRepositoryImpl(JQuantsListedInfoRepositoryInterface):
    """Listed info repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession, mapper: Optional[ListedInfoMapper] = None) -> None:
        """Initialize repository.

        Args:
            session: AsyncSession instance
            mapper: Optional mapper instance for entity-model conversion
        """
        self._session = session
        self._mapper = mapper or ListedInfoMapper()

    async def save_all(self, listed_infos: List[JQuantsListedInfo]) -> None:
        """複数の上場銘柄情報を保存（UPSERT）"""
        if not listed_infos:
            return

        # エンティティをモデルに変換（Mapper を使用）
        models = self._mapper.to_models(listed_infos)

        # バルク UPSERT 用のデータ準備
        values = [
            {
                "date": model.date,
                "code": model.code,
                "company_name": model.company_name,
                "company_name_english": model.company_name_english,
                "sector_17_code": model.sector_17_code,
                "sector_17_code_name": model.sector_17_code_name,
                "sector_33_code": model.sector_33_code,
                "sector_33_code_name": model.sector_33_code_name,
                "scale_category": model.scale_category,
                "market_code": model.market_code,
                "market_code_name": model.market_code_name,
                "margin_code": model.margin_code,
                "margin_code_name": model.margin_code_name,
            }
            for model in models
        ]

        # PostgreSQL の ON CONFLICT を使用した UPSERT
        stmt = insert(ListedInfoModel).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["date", "code"],
            set_={
                "company_name": stmt.excluded.company_name,
                "company_name_english": stmt.excluded.company_name_english,
                "sector_17_code": stmt.excluded.sector_17_code,
                "sector_17_code_name": stmt.excluded.sector_17_code_name,
                "sector_33_code": stmt.excluded.sector_33_code,
                "sector_33_code_name": stmt.excluded.sector_33_code_name,
                "scale_category": stmt.excluded.scale_category,
                "market_code": stmt.excluded.market_code,
                "market_code_name": stmt.excluded.market_code_name,
                "margin_code": stmt.excluded.margin_code,
                "margin_code_name": stmt.excluded.margin_code_name,
                "updated_at": stmt.excluded.updated_at,
            },
        )

        await self._session.execute(stmt)
        await self._session.flush()

        logger.info(f"Saved {len(listed_infos)} listed info records")

    async def find_by_code_and_date(
        self, code: StockCode, target_date: date
    ) -> Optional[JQuantsListedInfo]:
        """銘柄コードと日付で検索"""
        result = await self._session.execute(
            select(ListedInfoModel).where(
                ListedInfoModel.code == code.value,
                ListedInfoModel.date == target_date,
            )
        )
        model = result.scalar_one_or_none()

        if model:
            return self._mapper.to_entity(model)
        return None

    async def find_all_by_date(self, target_date: date) -> List[JQuantsListedInfo]:
        """日付で全銘柄を検索"""
        result = await self._session.execute(
            select(ListedInfoModel)
            .where(ListedInfoModel.date == target_date)
            .order_by(ListedInfoModel.code)
        )
        models = result.scalars().all()

        return self._mapper.to_entities(models)

    async def find_latest_by_code(self, code: StockCode) -> Optional[JQuantsListedInfo]:
        """銘柄コードで最新の情報を検索"""
        result = await self._session.execute(
            select(ListedInfoModel)
            .where(ListedInfoModel.code == code.value)
            .order_by(ListedInfoModel.date.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()

        if model:
            return self._mapper.to_entity(model)
        return None

    async def delete_by_date(self, target_date: date) -> int:
        """指定日付のデータを削除"""
        result = await self._session.execute(
            delete(ListedInfoModel).where(ListedInfoModel.date == target_date)
        )
        await self._session.flush()

        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} records for date {target_date}")
        return deleted_count

