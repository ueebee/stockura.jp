"""決算発表予定取得ユースケース"""

from datetime import date
from typing import Optional

from app.application.dtos.announcement_dto import AnnouncementDTO, AnnouncementListDTO
from app.application.interfaces.external.announcement_client import AnnouncementClientInterface
from app.core.logger import get_logger
from app.domain.entities.announcement import Announcement
from app.domain.repositories.announcement_repository import AnnouncementRepository

logger = get_logger(__name__)


class FetchAnnouncementUseCase:
    """決算発表予定取得ユースケース"""

    def __init__(
        self,
        announcement_client: AnnouncementClientInterface,
        announcement_repository: AnnouncementRepository,
    ) -> None:
        self._client = announcement_client
        self._repository = announcement_repository

    async def fetch_and_save_announcements(self) -> AnnouncementListDTO:
        """API から決算発表予定を取得してデータベースに保存

        Returns:
            AnnouncementListDTO: 保存した決算発表予定リスト
        """
        logger.info("Fetching announcements from J-Quants API")

        # API から全データを取得
        raw_announcements = await self._client.get_all_announcements()
        
        if not raw_announcements:
            logger.warning("No announcements found")
            return AnnouncementListDTO(announcements=[], total_count=0)

        # エンティティに変換
        announcements = []
        for raw_data in raw_announcements:
            try:
                announcement = Announcement.from_dict(raw_data)
                announcements.append(announcement)
            except Exception as e:
                logger.error(f"Failed to parse announcement data: {raw_data}, error: {str(e)}")
                continue

        if announcements:
            # データベースに一括保存
            await self._repository.save_bulk(announcements)
            logger.info(f"Saved {len(announcements)} announcements to database")

        # DTO に変換して返却
        dto_list = AnnouncementDTO.from_entities(announcements)
        return AnnouncementListDTO(announcements=dto_list, total_count=len(dto_list))

    async def get_announcements_by_date(
        self, announcement_date: date
    ) -> AnnouncementListDTO:
        """指定日の決算発表予定を取得

        Args:
            announcement_date: 発表日

        Returns:
            AnnouncementListDTO: 決算発表予定リスト
        """
        logger.info(f"Getting announcements for date: {announcement_date}")

        announcements = await self._repository.find_by_date(announcement_date)
        dto_list = AnnouncementDTO.from_entities(announcements)
        
        return AnnouncementListDTO(announcements=dto_list, total_count=len(dto_list))

    async def get_announcements_by_code(self, code: str) -> AnnouncementListDTO:
        """指定銘柄の決算発表予定を取得

        Args:
            code: 銘柄コード

        Returns:
            AnnouncementListDTO: 決算発表予定リスト
        """
        logger.info(f"Getting announcements for code: {code}")

        announcements = await self._repository.find_by_code(code)
        dto_list = AnnouncementDTO.from_entities(announcements)
        
        return AnnouncementListDTO(announcements=dto_list, total_count=len(dto_list))

    async def get_latest_announcements(self) -> AnnouncementListDTO:
        """最新の決算発表予定を取得

        Returns:
            AnnouncementListDTO: 最新の決算発表予定リスト
        """
        logger.info("Getting latest announcements")

        announcements = await self._repository.find_latest()
        dto_list = AnnouncementDTO.from_entities(announcements)
        
        return AnnouncementListDTO(announcements=dto_list, total_count=len(dto_list))

    async def get_announcement(
        self, announcement_date: date, code: str
    ) -> Optional[AnnouncementDTO]:
        """特定の決算発表予定を取得

        Args:
            announcement_date: 発表日
            code: 銘柄コード

        Returns:
            AnnouncementDTO: 決算発表予定（存在しない場合は None）
        """
        logger.info(f"Getting announcement for code: {code} on date: {announcement_date}")

        announcement = await self._repository.find_by_date_and_code(announcement_date, code)
        
        return AnnouncementDTO.from_entity(announcement) if announcement else None