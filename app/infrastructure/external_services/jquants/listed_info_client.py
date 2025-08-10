"""J-Quants Listed Info API client."""
from typing import Any, Dict, List, Optional, cast

from app.application.interfaces.external.listed_info_client import ListedInfoClientInterface
from app.core.logger import get_logger
from app.infrastructure.external_services.jquants.base_client import JQuantsBaseClient
from app.infrastructure.external_services.jquants.types.responses import JQuantsListedInfoResponse

logger = get_logger(__name__)


class JQuantsListedInfoClient(ListedInfoClientInterface):
    """J-Quants 上場銘柄情報 API クライアント"""

    def __init__(self, base_client: JQuantsBaseClient) -> None:
        """Initialize listed info client.

        Args:
            base_client: Base J-Quants client instance
        """
        self._client = base_client

    async def get_listed_info(
        self,
        code: Optional[str] = None,
        date: Optional[str] = None,
    ) -> List[JQuantsListedInfoResponse]:
        """上場銘柄情報を取得

        Args:
            code: 銘柄コード（4 桁の数字）
            date: 基準日（YYYYMMDD または YYYY-MM-DD 形式）

        Returns:
            List[JQuantsListedInfoResponse]: 上場銘柄情報のリスト

        Raises:
            NetworkError: ネットワークエラーが発生した場合
            RateLimitError: レート制限に達した場合
            ValidationError: データ形式エラーが発生した場合
        """
        params = {}
        if code:
            params["code"] = code
        if date:
            params["date"] = date

        logger.info(f"Fetching listed info with params: {params}")

        try:
            response = await self._client.get("/listed/info", params=params)
            info_list = response.get("info", [])
            
            # 型安全性のためにキャスト
            typed_info_list = cast(List[JQuantsListedInfoResponse], info_list)

            logger.info(f"Successfully fetched {len(typed_info_list)} listed info records")
            return typed_info_list

        except Exception as e:
            logger.error(f"Failed to fetch listed info: {str(e)}")
            raise

    async def get_all_listed_info(
        self, date: Optional[str] = None
    ) -> List[JQuantsListedInfoResponse]:
        """全銘柄の上場情報を取得（ページネーション対応）

        Args:
            date: 基準日（YYYYMMDD または YYYY-MM-DD 形式）

        Returns:
            List[JQuantsListedInfoResponse]: 全上場銘柄情報のリスト

        Raises:
            NetworkError: ネットワークエラーが発生した場合
            RateLimitError: レート制限に達した場合
            ValidationError: データ形式エラーが発生した場合
        """
        params = {}
        if date:
            params["date"] = date

        logger.info(f"Fetching all listed info for date: {date}")

        all_info: List[JQuantsListedInfoResponse] = []
        pagination_key = None

        while True:
            if pagination_key:
                params["pagination_key"] = pagination_key

            response = await self._client.get("/listed/info", params=params)
            info_list = response.get("info", [])
            
            # 型安全性のためにキャスト
            typed_info_list = cast(List[JQuantsListedInfoResponse], info_list)
            all_info.extend(typed_info_list)

            # ページネーションキーがない場合は終了
            pagination_key = response.get("pagination_key")
            if not pagination_key:
                break

            logger.debug(f"Fetched {len(typed_info_list)} records, continuing with pagination")

        logger.info(f"Successfully fetched total {len(all_info)} listed info records")
        return all_info