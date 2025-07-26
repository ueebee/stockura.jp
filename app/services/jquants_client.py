"""
J-Quants API クライアント

クリーンアーキテクチャ版のJ-Quantsクライアント
"""

import logging
from typing import Dict, Optional, List, Any, Union
from datetime import datetime, date
import datetime as dt

from app.services.data_source_service import DataSourceService
from app.domain.interfaces import IAPIClient
from app.infrastructure.jquants import JQuantsClientFactory

logger = logging.getLogger(__name__)


class JQuantsListedInfoClient:
    """J-Quants上場情報APIクライアント"""
    
    def __init__(self, api_client: IAPIClient):
        """
        初期化
        
        Args:
            api_client: APIクライアントインターフェース
        """
        self.api_client = api_client

    async def get_listed_info(
        self,
        code: Optional[str] = None,
        date: Optional[Union[str, datetime, dt.date]] = None
    ) -> List[Dict[str, Any]]:
        """
        上場情報を取得

        Args:
            code: 銘柄コード（4桁）
            date: 基準日

        Returns:
            List[Dict[str, Any]]: 上場情報のリスト
        """
        # 日付の変換
        target_date = None
        if date:
            if isinstance(date, str):
                # YYYYMMDD形式の文字列をdateオブジェクトに変換
                target_date = dt.date(
                    int(date[:4]),
                    int(date[4:6]),
                    int(date[6:8])
                )
            elif isinstance(date, datetime):
                target_date = date.date()
            elif isinstance(date, dt.date):
                target_date = date
        
        # 新しいAPIクライアントを使用
        return await self.api_client.get_listed_companies(
            code=code,
            target_date=target_date
        )

    async def get_all_listed_companies(
        self,
        date: Optional[Union[str, datetime, dt.date]] = None
    ) -> List[Dict[str, Any]]:
        """
        全上場企業の情報を取得

        Args:
            date: 基準日（YYYYMMDD形式の文字列、datetimeオブジェクト、またはdateオブジェクト）

        Returns:
            List[Dict[str, Any]]: 全上場企業情報のリスト
        """
        logger.info("Fetching all listed companies from J-Quants API")
        return await self.get_listed_info(date=date)

    async def get_company_info(
        self,
        code: str,
        date: Optional[Union[str, datetime, dt.date]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        特定企業の上場情報を取得

        Args:
            code: 銘柄コード（4桁）
            date: 基準日（YYYYMMDD形式の文字列、datetimeオブジェクト、またはdateオブジェクト）

        Returns:
            Optional[Dict[str, Any]]: 企業情報（見つからない場合はNone）
        """
        logger.info(f"Fetching company info for code: {code}")
        companies = await self.get_listed_info(code=code, date=date)

        if companies:
            return companies[0]  # 特定の銘柄コードは1件のみ返される
        else:
            logger.warning(f"No company found for code: {code}")
            return None

    async def test_connection(self) -> bool:
        """
        J-Quants APIへの接続をテスト

        Returns:
            bool: 接続成功時はTrue
        """
        return await self.api_client.test_connection()


class JQuantsDailyQuotesClient:
    """J-Quants株価データAPIクライアント"""
    
    def __init__(self, api_client: IAPIClient):
        """
        初期化
        
        Args:
            api_client: APIクライアントインターフェース
        """
        self.api_client = api_client

    async def get_daily_quotes(
        self,
        code: Optional[str] = None,
        date: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        pagination_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        株価データを取得

        Args:
            code: 銘柄コード（5桁）
            date: 取得日付（YYYY-MM-DD形式）
            from_date: 取得開始日（YYYY-MM-DD形式）
            to_date: 取得終了日（YYYY-MM-DD形式）
            pagination_key: ページネーションキー

        Returns:
            Dict[str, Any]: 株価データとページネーション情報
        """
        # 日付の変換
        target_date = None
        start_date = None
        end_date = None
        
        if date:
            target_date = dt.date.fromisoformat(date)
        if from_date:
            start_date = dt.date.fromisoformat(from_date)
        if to_date:
            end_date = dt.date.fromisoformat(to_date)
        
        # 新しいAPIクライアントを使用
        quotes = await self.api_client.get_daily_quotes(
            code=code,
            target_date=target_date,
            from_date=start_date,
            to_date=end_date
        )
        
        # ページネーション対応のレスポンス形式に変換
        return {
            "daily_quotes": quotes,
            "pagination_key": None  # 新実装ではページネーションは内部で処理
        }

    async def get_stock_prices_by_code(
        self,
        code: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        特定銘柄の株価データを取得（全期間）

        Args:
            code: 銘柄コード（5桁）
            from_date: 取得開始日（YYYY-MM-DD形式）
            to_date: 取得終了日（YYYY-MM-DD形式）

        Returns:
            List[Dict[str, Any]]: 株価データのリスト
        """
        logger.info(f"Fetching stock prices for code: {code}")
        
        response = await self.get_daily_quotes(
            code=code,
            from_date=from_date,
            to_date=to_date
        )
        
        return response.get("daily_quotes", [])

    async def get_stock_prices_by_date(
        self,
        date: str,
        codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        特定日の株価データを取得

        Args:
            date: 取得日付（YYYY-MM-DD形式）
            codes: 取得対象の銘柄コードリスト（指定しない場合は全銘柄）

        Returns:
            List[Dict[str, Any]]: 株価データのリスト
        """
        logger.info(f"Fetching stock prices for date: {date}")

        target_date = dt.date.fromisoformat(date)
        
        # 新しいAPIクライアントを使用
        return await self.api_client.get_daily_quotes(
            target_date=target_date,
            specific_codes=codes
        )

    async def test_connection(self) -> bool:
        """
        J-Quants daily quotes APIへの接続をテスト

        Returns:
            bool: 接続成功時はTrue
        """
        return await self.api_client.test_connection()


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
        self._listed_clients: Dict[int, JQuantsListedInfoClient] = {}
        self._daily_quotes_clients: Dict[int, JQuantsDailyQuotesClient] = {}

    async def get_client(self, data_source_id: int) -> JQuantsListedInfoClient:
        """
        データソースIDに対応するクライアントを取得

        Args:
            data_source_id: データソースID

        Returns:
            JQuantsListedInfoClient: J-Quantsクライアント

        Raises:
            Exception: データソースが見つからない場合
        """
        if data_source_id not in self._listed_clients:
            # APIクライアントを取得または作成
            api_client = await self._get_or_create_api_client(data_source_id)
            
            # ラッパークライアントを作成
            client = JQuantsListedInfoClient(api_client)
            self._listed_clients[data_source_id] = client

        return self._listed_clients[data_source_id]

    async def get_daily_quotes_client(self, data_source_id: int) -> JQuantsDailyQuotesClient:
        """
        データソースIDに対応するDailyQuotesクライアントを取得

        Args:
            data_source_id: データソースID

        Returns:
            JQuantsDailyQuotesClient: J-Quants DailyQuotesクライアント

        Raises:
            Exception: データソースが見つからない場合
        """
        if data_source_id not in self._daily_quotes_clients:
            # APIクライアントを取得または作成
            api_client = await self._get_or_create_api_client(data_source_id)
            
            # ラッパークライアントを作成
            client = JQuantsDailyQuotesClient(api_client)
            self._daily_quotes_clients[data_source_id] = client

        return self._daily_quotes_clients[data_source_id]

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
            self._listed_clients.pop(data_source_id, None)
            self._daily_quotes_clients.pop(data_source_id, None)
            logger.info(f"Cleared client cache for data_source_id: {data_source_id}")
        else:
            self._api_clients.clear()
            self._listed_clients.clear()
            self._daily_quotes_clients.clear()
            logger.info("Cleared all client cache")
