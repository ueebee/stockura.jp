"""決算発表予定リポジトリ実装"""

from datetime import date
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.logger import get_logger
from app.domain.entities.announcement import Announcement
from app.domain.repositories.announcement_repository import AnnouncementRepository
from app.infrastructure.database.models.announcement import AnnouncementModel

logger = get_logger(__name__)


class AnnouncementRepositoryImpl(AnnouncementRepository):
    """決算発表予定リポジトリの実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, announcement: Announcement) -> None:
        """決算発表予定を保存"""
        try:
            model = AnnouncementModel.from_entity(announcement)
            self._session.add(model)
            await self._session.commit()
            logger.info(f"Saved announcement: {announcement.code.value} on {announcement.date}")
        except IntegrityError:
            await self._session.rollback()
            # 既存のレコードを更新
            stmt = select(AnnouncementModel).where(
                AnnouncementModel.date == announcement.date,
                AnnouncementModel.code == announcement.code.value,
                AnnouncementModel.fiscal_quarter == announcement.fiscal_quarter,
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.company_name = announcement.company_name
                existing.fiscal_year = announcement.fiscal_year
                existing.sector_name = announcement.sector_name
                existing.section = announcement.section
                await self._session.commit()
                logger.info(f"Updated announcement: {announcement.code.value} on {announcement.date}")
            else:
                raise

    async def save_bulk(self, announcements: List[Announcement]) -> None:
        """決算発表予定を一括保存"""
        if not announcements:
            return

        try:
            # 既存のデータを削除（同じ日付のもの）
            dates = {announcement.date for announcement in announcements}
            for announcement_date in dates:
                await self.delete_by_date(announcement_date)

            # 新しいデータを一括挿入
            models = [AnnouncementModel.from_entity(announcement) for announcement in announcements]
            self._session.add_all(models)
            await self._session.commit()
            logger.info(f"Bulk saved {len(announcements)} announcements")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to bulk save announcements: {str(e)}")
            raise

    async def find_by_date(self, announcement_date: date) -> List[Announcement]:
        """発表日で決算発表予定を検索"""
        stmt = select(AnnouncementModel).where(
            AnnouncementModel.date == announcement_date
        ).order_by(AnnouncementModel.code)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [model.to_entity() for model in models]

    async def find_by_code(self, code: str) -> List[Announcement]:
        """銘柄コードで決算発表予定を検索"""
        stmt = select(AnnouncementModel).where(
            AnnouncementModel.code == code
        ).order_by(AnnouncementModel.date.desc())
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [model.to_entity() for model in models]

    async def find_by_date_and_code(
        self, announcement_date: date, code: str
    ) -> Optional[Announcement]:
        """発表日と銘柄コードで決算発表予定を検索"""
        stmt = select(AnnouncementModel).where(
            AnnouncementModel.date == announcement_date,
            AnnouncementModel.code == code,
        )
        
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return model.to_entity() if model else None

    async def find_latest(self) -> List[Announcement]:
        """最新の決算発表予定を取得"""
        # 最新の日付を取得
        latest_date_stmt = select(AnnouncementModel.date).order_by(
            AnnouncementModel.date.desc()
        ).limit(1)
        
        result = await self._session.execute(latest_date_stmt)
        latest_date = result.scalar_one_or_none()
        
        if not latest_date:
            return []
        
        return await self.find_by_date(latest_date)

    async def delete_by_date(self, announcement_date: date) -> int:
        """発表日で決算発表予定を削除"""
        stmt = delete(AnnouncementModel).where(
            AnnouncementModel.date == announcement_date
        )
        
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} announcements for date {announcement_date}")
        
        return deleted_count