"""Listed info repository implementation."""
from datetime import date
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domain.entities.listed_info import ListedInfo
from app.domain.entities.stock import StockCode
from app.domain.repositories.listed_info_repository import ListedInfoRepository
from app.infrastructure.database.models.listed_info_model import ListedInfoModel

logger = get_logger(__name__)


class ListedInfoRepositoryImpl(ListedInfoRepository):
    """Listed info repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: AsyncSession instance
        """
        self._session = session

    async def save_all(self, listed_infos: List[ListedInfo]) -> None:
        """複数の上場銘柄情報を保存（UPSERT）"""
        if not listed_infos:
            return

        # エンティティをモデルに変換
        models = [self._to_model(info) for info in listed_infos]

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
    ) -> Optional[ListedInfo]:
        """銘柄コードと日付で検索"""
        result = await self._session.execute(
            select(ListedInfoModel).where(
                ListedInfoModel.code == code.value,
                ListedInfoModel.date == target_date,
            )
        )
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def find_all_by_date(self, target_date: date) -> List[ListedInfo]:
        """日付で全銘柄を検索"""
        result = await self._session.execute(
            select(ListedInfoModel)
            .where(ListedInfoModel.date == target_date)
            .order_by(ListedInfoModel.code)
        )
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def find_latest_by_code(self, code: StockCode) -> Optional[ListedInfo]:
        """銘柄コードで最新の情報を検索"""
        result = await self._session.execute(
            select(ListedInfoModel)
            .where(ListedInfoModel.code == code.value)
            .order_by(ListedInfoModel.date.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
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

    def _to_entity(self, model: ListedInfoModel) -> ListedInfo:
        """Convert model to entity.

        Args:
            model: ListedInfo model

        Returns:
            ListedInfo entity
        """
        return ListedInfo(
            date=model.date,
            code=StockCode(model.code),
            company_name=model.company_name,
            company_name_english=model.company_name_english,
            sector_17_code=model.sector_17_code,
            sector_17_code_name=model.sector_17_code_name,
            sector_33_code=model.sector_33_code,
            sector_33_code_name=model.sector_33_code_name,
            scale_category=model.scale_category,
            market_code=model.market_code,
            market_code_name=model.market_code_name,
            margin_code=model.margin_code,
            margin_code_name=model.margin_code_name,
        )

    def _to_model(self, entity: ListedInfo) -> ListedInfoModel:
        """Convert entity to model.

        Args:
            entity: ListedInfo entity

        Returns:
            ListedInfo model
        """
        return ListedInfoModel(
            date=entity.date,
            code=entity.code.value,
            company_name=entity.company_name,
            company_name_english=entity.company_name_english,
            sector_17_code=entity.sector_17_code,
            sector_17_code_name=entity.sector_17_code_name,
            sector_33_code=entity.sector_33_code,
            sector_33_code_name=entity.sector_33_code_name,
            scale_category=entity.scale_category,
            market_code=entity.market_code,
            market_code_name=entity.market_code_name,
            margin_code=entity.margin_code,
            margin_code_name=entity.margin_code_name,
        )