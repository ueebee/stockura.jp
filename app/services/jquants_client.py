"""
J-Quants API クライアント

J-Quants APIとの通信を担当するクライアントクラス
"""

import httpx
import logging
from datetime import datetime
import datetime as dt
from typing import Dict, List, Optional, Any, Union
from app.services.data_source_service import DataSourceService

logger = logging.getLogger(__name__)


class JQuantsListedInfoClient:
    """J-Quants上場情報APIクライアント"""
    
    def __init__(
        self, 
        data_source_service: DataSourceService,
        data_source_id: int,
        base_url: str = "https://api.jquants.com"
    ):
        """
        初期化
        
        Args:
            data_source_service: データソースサービス
            data_source_id: J-QuantsデータソースのID
            base_url: APIのベースURL
        """
        self.data_source_service = data_source_service
        self.data_source_id = data_source_id
        self.base_url = base_url
        self.endpoint = f"{base_url}/v1/listed/info"
    
    async def get_listed_info(
        self, 
        code: Optional[str] = None,
        date: Optional[Union[str, datetime, dt.date]] = None
    ) -> List[Dict[str, Any]]:
        """
        上場情報を取得
        
        Args:
            code: 銘柄コード（4桁）
            date: 基準日（YYYYMMDD形式の文字列、datetimeオブジェクト、またはdateオブジェクト）
            
        Returns:
            List[Dict[str, Any]]: 上場情報のリスト
            
        Raises:
            Exception: API呼び出しに失敗した場合
        """
        try:
            # 有効なIDトークンを取得
            id_token = await self.data_source_service.get_valid_api_token(self.data_source_id)
            if not id_token:
                raise Exception(f"Failed to get valid API token for data_source_id: {self.data_source_id}")
            
            # リクエストパラメータを構築
            params = {}
            if code:
                params["code"] = str(code)
            if date:
                if isinstance(date, datetime):
                    params["date"] = date.strftime("%Y%m%d")
                elif isinstance(date, dt.date):
                    params["date"] = date.strftime("%Y%m%d")
                else:
                    # 文字列の場合はそのまま使用
                    params["date"] = str(date)
            
            # HTTPクライアントでAPIを呼び出し
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {id_token}",
                    "Content-Type": "application/json"
                }
                
                logger.info(f"Requesting listed info from J-Quants API: {self.endpoint}")
                logger.debug(f"Request params: {params}")
                
                response = await client.get(
                    self.endpoint,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                # HTTPステータスをチェック
                response.raise_for_status()
                
                # JSONレスポンスを取得
                data = response.json()
                
                # J-Quants APIのレスポンス形式に応じて処理
                if "info" in data:
                    listed_info = data["info"]
                    logger.info(f"Successfully retrieved {len(listed_info)} listed companies")
                    return listed_info
                else:
                    logger.warning("Unexpected response format from J-Quants API")
                    return []
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when calling J-Quants API: {e.response.status_code} - {e.response.text}")
            raise Exception(f"J-Quants API HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error when calling J-Quants API: {e}")
            raise Exception(f"J-Quants API request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error when calling J-Quants API: {e}")
            raise
    
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
        try:
            # 軽量なテストとして、1件だけ取得してみる
            # 実際のAPI仕様に応じて調整が必要な場合があります
            await self.get_listed_info()
            logger.info("J-Quants API connection test successful")
            return True
        except Exception as e:
            logger.error(f"J-Quants API connection test failed: {e}")
            return False


class JQuantsClientManager:
    """J-Quantsクライアント管理クラス"""
    
    def __init__(self, data_source_service: DataSourceService):
        """
        初期化
        
        Args:
            data_source_service: データソースサービス
        """
        self.data_source_service = data_source_service
        self._clients: Dict[int, JQuantsListedInfoClient] = {}
    
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
        if data_source_id not in self._clients:
            # データソース情報を取得
            data_source = await self.data_source_service.get_data_source(data_source_id)
            if not data_source:
                raise Exception(f"Data source not found: {data_source_id}")
            
            if data_source.provider_type != "jquants":
                raise Exception(f"Data source {data_source_id} is not a J-Quants provider")
            
            # クライアントを作成してキャッシュ
            client = JQuantsListedInfoClient(
                data_source_service=self.data_source_service,
                data_source_id=data_source_id,
                base_url=data_source.base_url or "https://api.jquants.com"
            )
            self._clients[data_source_id] = client
        
        return self._clients[data_source_id]
    
    def clear_client_cache(self, data_source_id: Optional[int] = None):
        """
        クライアントキャッシュをクリア
        
        Args:
            data_source_id: 特定のデータソースIDのみクリアする場合
        """
        if data_source_id is not None:
            self._clients.pop(data_source_id, None)
            logger.info(f"Cleared client cache for data_source_id: {data_source_id}")
        else:
            self._clients.clear()
            logger.info("Cleared all client cache")