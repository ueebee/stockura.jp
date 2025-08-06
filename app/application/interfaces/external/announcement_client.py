"""決算発表予定クライアントインターフェース"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class AnnouncementClientInterface(ABC):
    """決算発表予定クライアントのインターフェース"""

    @abstractmethod
    async def get_announcements(
        self, pagination_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """決算発表予定を取得

        Args:
            pagination_key: ページネーションキー

        Returns:
            Dict[str, Any]: API レスポンス
        """
        pass

    @abstractmethod
    async def get_all_announcements(self) -> List[Dict[str, Any]]:
        """全決算発表予定を取得（ページネーション対応）

        Returns:
            List[Dict[str, Any]]: 全決算発表予定のリスト
        """
        pass