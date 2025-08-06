"""週次信用取引残高リポジトリ実装"""

from datetime import date
from typing import List, Optional

from sqlalchemy import delete, select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.domain.entities import WeeklyMarginInterest
from app.domain.repositories import WeeklyMarginInterestRepository
from app.infrastructure.database.models import WeeklyMarginInterestModel

logger = get_logger()


class WeeklyMarginInterestRepositoryImpl(WeeklyMarginInterestRepository):
    """週次信用取引残高リポジトリの実装"""

    def __init__(self, session: AsyncSession) -> None:
        """リポジトリを初期化

        Args:
            session: AsyncSession インスタンス
        """
        self._session = session

    async def save(self, weekly_margin_interest: WeeklyMarginInterest) -> None:
        """週次信用取引残高を保存する"""
        model = self._to_model(weekly_margin_interest)

        # UPSERT 処理
        stmt = insert(WeeklyMarginInterestModel).values(
            code=model.code,
            date=model.date,
            short_margin_trade_volume=model.short_margin_trade_volume,
            long_margin_trade_volume=model.long_margin_trade_volume,
            short_negotiable_margin_trade_volume=model.short_negotiable_margin_trade_volume,
            long_negotiable_margin_trade_volume=model.long_negotiable_margin_trade_volume,
            short_standardized_margin_trade_volume=model.short_standardized_margin_trade_volume,
            long_standardized_margin_trade_volume=model.long_standardized_margin_trade_volume,
            issue_type=model.issue_type,
        )

        # 既存レコードがある場合は更新
        stmt = stmt.on_conflict_do_update(
            index_elements=["code", "date"],
            set_={
                "short_margin_trade_volume": stmt.excluded.short_margin_trade_volume,
                "long_margin_trade_volume": stmt.excluded.long_margin_trade_volume,
                "short_negotiable_margin_trade_volume": stmt.excluded.short_negotiable_margin_trade_volume,
                "long_negotiable_margin_trade_volume": stmt.excluded.long_negotiable_margin_trade_volume,
                "short_standardized_margin_trade_volume": stmt.excluded.short_standardized_margin_trade_volume,
                "long_standardized_margin_trade_volume": stmt.excluded.long_standardized_margin_trade_volume,
                "issue_type": stmt.excluded.issue_type,
                "updated_at": func.now(),
            },
        )

        await self._session.execute(stmt)
        await self._session.flush()

        logger.info(
            "週次信用取引残高を保存しました",
            code=weekly_margin_interest.code,
            date=str(weekly_margin_interest.date),
        )

    async def save_bulk(
        self, weekly_margin_interests: List[WeeklyMarginInterest]
    ) -> None:
        """複数の週次信用取引残高を一括保存する"""
        if not weekly_margin_interests:
            return

        models = [self._to_model(wmi) for wmi in weekly_margin_interests]

        # バルク UPSERT 用のデータ
        values = [
            {
                "code": model.code,
                "date": model.date,
                "short_margin_trade_volume": model.short_margin_trade_volume,
                "long_margin_trade_volume": model.long_margin_trade_volume,
                "short_negotiable_margin_trade_volume": model.short_negotiable_margin_trade_volume,
                "long_negotiable_margin_trade_volume": model.long_negotiable_margin_trade_volume,
                "short_standardized_margin_trade_volume": model.short_standardized_margin_trade_volume,
                "long_standardized_margin_trade_volume": model.long_standardized_margin_trade_volume,
                "issue_type": model.issue_type,
            }
            for model in models
        ]

        stmt = insert(WeeklyMarginInterestModel).values(values)

        # 既存レコードがある場合は更新
        stmt = stmt.on_conflict_do_update(
            index_elements=["code", "date"],
            set_={
                "short_margin_trade_volume": stmt.excluded.short_margin_trade_volume,
                "long_margin_trade_volume": stmt.excluded.long_margin_trade_volume,
                "short_negotiable_margin_trade_volume": stmt.excluded.short_negotiable_margin_trade_volume,
                "long_negotiable_margin_trade_volume": stmt.excluded.long_negotiable_margin_trade_volume,
                "short_standardized_margin_trade_volume": stmt.excluded.short_standardized_margin_trade_volume,
                "long_standardized_margin_trade_volume": stmt.excluded.long_standardized_margin_trade_volume,
                "issue_type": stmt.excluded.issue_type,
                "updated_at": func.now(),
            },
        )

        await self._session.execute(stmt)
        await self._session.flush()

        logger.info(
            "週次信用取引残高を一括保存しました",
            count=len(weekly_margin_interests),
        )

    async def find_by_code_and_date(
        self, code: str, date: date
    ) -> Optional[WeeklyMarginInterest]:
        """銘柄コードと日付で週次信用取引残高を検索する"""
        stmt = select(WeeklyMarginInterestModel).where(
            WeeklyMarginInterestModel.code == code,
            WeeklyMarginInterestModel.date == date,
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def find_by_code_and_date_range(
        self, code: str, start_date: date, end_date: date
    ) -> List[WeeklyMarginInterest]:
        """銘柄コードと日付範囲で週次信用取引残高を検索する"""
        stmt = (
            select(WeeklyMarginInterestModel)
            .where(
                WeeklyMarginInterestModel.code == code,
                WeeklyMarginInterestModel.date >= start_date,
                WeeklyMarginInterestModel.date <= end_date,
            )
            .order_by(WeeklyMarginInterestModel.date)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def find_by_date(self, date: date) -> List[WeeklyMarginInterest]:
        """日付で週次信用取引残高を検索する"""
        stmt = (
            select(WeeklyMarginInterestModel)
            .where(WeeklyMarginInterestModel.date == date)
            .order_by(WeeklyMarginInterestModel.code)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def find_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[WeeklyMarginInterest]:
        """日付範囲で週次信用取引残高を検索する"""
        stmt = (
            select(WeeklyMarginInterestModel)
            .where(
                WeeklyMarginInterestModel.date >= start_date,
                WeeklyMarginInterestModel.date <= end_date,
            )
            .order_by(WeeklyMarginInterestModel.date, WeeklyMarginInterestModel.code)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def find_by_issue_type(
        self,
        issue_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WeeklyMarginInterest]:
        """銘柄種別で週次信用取引残高を検索する"""
        stmt = select(WeeklyMarginInterestModel).where(
            WeeklyMarginInterestModel.issue_type == issue_type
        )

        if start_date:
            stmt = stmt.where(WeeklyMarginInterestModel.date >= start_date)
        if end_date:
            stmt = stmt.where(WeeklyMarginInterestModel.date <= end_date)

        stmt = stmt.order_by(
            WeeklyMarginInterestModel.date, WeeklyMarginInterestModel.code
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def delete_by_date_range(self, start_date: date, end_date: date) -> int:
        """日付範囲で週次信用取引残高を削除する"""
        stmt = delete(WeeklyMarginInterestModel).where(
            WeeklyMarginInterestModel.date >= start_date,
            WeeklyMarginInterestModel.date <= end_date,
        )

        result = await self._session.execute(stmt)
        await self._session.flush()

        deleted_count = result.rowcount
        logger.info(
            "週次信用取引残高を削除しました",
            start_date=str(start_date),
            end_date=str(end_date),
            deleted_count=deleted_count,
        )

        return deleted_count

    @staticmethod
    def _to_entity(model: WeeklyMarginInterestModel) -> WeeklyMarginInterest:
        """モデルをエンティティに変換する"""
        return WeeklyMarginInterest(
            code=model.code,
            date=model.date,
            short_margin_trade_volume=model.short_margin_trade_volume,
            long_margin_trade_volume=model.long_margin_trade_volume,
            short_negotiable_margin_trade_volume=model.short_negotiable_margin_trade_volume,
            long_negotiable_margin_trade_volume=model.long_negotiable_margin_trade_volume,
            short_standardized_margin_trade_volume=model.short_standardized_margin_trade_volume,
            long_standardized_margin_trade_volume=model.long_standardized_margin_trade_volume,
            issue_type=model.issue_type,
        )

    @staticmethod
    def _to_model(entity: WeeklyMarginInterest) -> WeeklyMarginInterestModel:
        """エンティティをモデルに変換する"""
        return WeeklyMarginInterestModel(
            code=entity.code,
            date=entity.date,
            short_margin_trade_volume=entity.short_margin_trade_volume,
            long_margin_trade_volume=entity.long_margin_trade_volume,
            short_negotiable_margin_trade_volume=entity.short_negotiable_margin_trade_volume,
            long_negotiable_margin_trade_volume=entity.long_negotiable_margin_trade_volume,
            short_standardized_margin_trade_volume=entity.short_standardized_margin_trade_volume,
            long_standardized_margin_trade_volume=entity.long_standardized_margin_trade_volume,
            issue_type=entity.issue_type,
        )
