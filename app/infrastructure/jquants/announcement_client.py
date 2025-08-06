"""J-Quants 決算発表予定 API クライアント"""

from typing import Any, Dict, List, Optional

from app.application.interfaces.external.announcement_client import AnnouncementClientInterface
from app.core.logger import get_logger
from app.infrastructure.jquants.base_client import JQuantsBaseClient

logger = get_logger(__name__)


class JQuantsAnnouncementClient(AnnouncementClientInterface):
    """J-Quants 決算発表予定 API クライアント"""

    def __init__(self, base_client: JQuantsBaseClient) -> None:
        """Initialize announcement client.

        Args:
            base_client: Base J-Quants client instance
        """
        self._client = base_client

    async def get_announcements(
        self, pagination_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """決算発表予定を取得

        Args:
            pagination_key: ページネーションキー

        Returns:
            Dict[str, Any]: API レスポンス

        Raises:
            NetworkError: ネットワークエラーが発生した場合
            RateLimitError: レート制限に達した場合
            ValidationError: データ形式エラーが発生した場合
        """
        params = {}
        if pagination_key:
            params["pagination_key"] = pagination_key

        logger.info(f"Fetching announcements with params: {params}")

        try:
            response = await self._client.get("/fins/announcement", params=params)
            announcement_list = response.get("announcement", [])

            logger.info(f"Successfully fetched {len(announcement_list)} announcement records")
            return response

        except Exception as e:
            logger.error(f"Failed to fetch announcements: {str(e)}")
            raise

    async def get_all_announcements(self) -> List[Dict[str, Any]]:
        """全決算発表予定を取得（ページネーション対応）

        Returns:
            List[Dict[str, Any]]: 全決算発表予定のリスト

        Raises:
            NetworkError: ネットワークエラーが発生した場合
            RateLimitError: レート制限に達した場合
            ValidationError: データ形式エラーが発生した場合
        """
        logger.info("Fetching all announcements")

        all_announcements = []
        pagination_key = None

        while True:
            params = {}
            if pagination_key:
                params["pagination_key"] = pagination_key

            response = await self._client.get("/fins/announcement", params=params)
            announcement_list = response.get("announcement", [])
            all_announcements.extend(announcement_list)

            # ページネーションキーがない場合は終了
            pagination_key = response.get("pagination_key")
            if not pagination_key:
                break

            logger.debug(f"Fetched {len(announcement_list)} records, continuing with pagination")

        logger.info(f"Successfully fetched total {len(all_announcements)} announcement records")
        return all_announcements