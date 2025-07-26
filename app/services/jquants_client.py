"""
J-Quants API クライアントマネージャー

J-Quants APIクライアントの管理とキャッシュを担当
"""

import logging
from typing import Dict, Optional

from app.services.data_source_service import DataSourceService
from app.domain.interfaces import IAPIClient
from app.infrastructure.jquants import JQuantsClientFactory

logger = logging.getLogger(__name__)


class JQuantsClientManager:
    """J-Quantsクライアント管理クラス"""

    def __init__(self, data_source_service: DataSourceService):
        """
        初期化

        Args:
            data_source_service: データソースサービス
        """
        self.data_source_service = data_source_service
        self._api_clients: Dict[int, IAPIClient] = {}

    async def get_client(self, data_source_id: int) -> IAPIClient:
        """
        データソースIDに対応するAPIクライアントを取得

        Args:
            data_source_id: データソースID

        Returns:
            IAPIClient: J-Quants APIクライアント

        Raises:
            Exception: データソースが見つからない場合
        """
        return await self._get_or_create_api_client(data_source_id)

    async def get_daily_quotes_client(self, data_source_id: int) -> IAPIClient:
        """
        データソースIDに対応するAPIクライアントを取得（後方互換性のため維持）

        Args:
            data_source_id: データソースID

        Returns:
            IAPIClient: J-Quants APIクライアント

        Raises:
            Exception: データソースが見つからない場合
        """
        return await self.get_client(data_source_id)

    async def _get_or_create_api_client(self, data_source_id: int) -> IAPIClient:
        """
        APIクライアントを取得または作成
        
        Args:
            data_source_id: データソースID
            
        Returns:
            IAPIClient: APIクライアント
        """
        if data_source_id not in self._api_clients:
            # ファクトリーを使用してクライアントを作成
            api_client = await JQuantsClientFactory.create(
                data_source_service=self.data_source_service,
                data_source_id=data_source_id
            )
            self._api_clients[data_source_id] = api_client
        
        return self._api_clients[data_source_id]
    
    def clear_client_cache(self, data_source_id: Optional[int] = None):
        """
        クライアントキャッシュをクリア

        Args:
            data_source_id: 特定のデータソースIDのみクリアする場合
        """
        if data_source_id is not None:
            self._api_clients.pop(data_source_id, None)
            logger.info(f"Cleared client cache for data_source_id: {data_source_id}")
        else:
            self._api_clients.clear()
            logger.info("Cleared all client cache")