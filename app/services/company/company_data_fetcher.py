"""
企業データ取得サービス

J-Quants APIから企業データを取得する責務に特化したクラス
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date

from app.services.interfaces.company_sync_interfaces import ICompanyDataFetcher, DataFetchError
from app.services.jquants_client import JQuantsClientManager
from app.core.exceptions import APIError, DataSourceNotFoundError

logger = logging.getLogger(__name__)


class CompanyDataFetcher(ICompanyDataFetcher):
    """企業データ取得サービスの実装"""
    
    def __init__(self, jquants_client_manager: JQuantsClientManager, data_source_id: int):
        """
        初期化
        
        Args:
            jquants_client_manager: J-Quantsクライアント管理
            data_source_id: データソースID
        """
        self.jquants_client_manager = jquants_client_manager
        self.data_source_id = data_source_id
        self._client = None
    
    async def _get_client(self):
        """J-Quantsクライアントを取得（遅延初期化）"""
        if self._client is None:
            try:
                self._client = await self.jquants_client_manager.get_client(self.data_source_id)
            except Exception as e:
                logger.error(f"Failed to get J-Quants client: {e}")
                raise DataFetchError(f"Failed to initialize J-Quants client: {str(e)}")
        return self._client
    
    async def fetch_all_companies(self, target_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        全企業データを取得
        
        Args:
            target_date: 取得対象日（Noneの場合は最新）
            
        Returns:
            List[Dict[str, Any]]: J-Quants APIレスポンスの企業データリスト
            
        Raises:
            DataFetchError: データ取得に失敗した場合
        """
        logger.info(f"Fetching all companies data for date: {target_date or 'latest'}")
        
        try:
            client = await self._get_client()
            companies_data = await client.get_listed_companies(target_date=target_date)
            
            if not companies_data:
                logger.warning("No company data received from J-Quants API")
                return []
            
            logger.info(f"Successfully fetched {len(companies_data)} companies from J-Quants API")
            return companies_data
            
        except DataSourceNotFoundError as e:
            error_msg = f"Data source not found: {self.data_source_id}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
            
        except APIError as e:
            # APIエラーをDataFetchErrorに変換
            error_msg = f"J-Quants API error: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
            
        except Exception as e:
            # 予期しないエラーの処理
            error_msg = f"Unexpected error fetching companies data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataFetchError(error_msg)
    
    async def fetch_company_by_code(self, code: str, target_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        特定企業データを取得
        
        Args:
            code: 銘柄コード
            target_date: 取得対象日（Noneの場合は最新）
            
        Returns:
            Optional[Dict[str, Any]]: J-Quants APIレスポンスの企業データ（見つからない場合はNone）
            
        Raises:
            DataFetchError: データ取得に失敗した場合
        """
        logger.info(f"Fetching company data for code: {code}, date: {target_date or 'latest'}")
        
        try:
            client = await self._get_client()
            companies = await client.get_listed_companies(code=code, target_date=target_date)
            company_data = companies[0] if companies else None
            
            if company_data:
                logger.info(f"Successfully fetched company data for code: {code}")
            else:
                logger.warning(f"No company data found for code: {code}")
                
            return company_data
            
        except DataSourceNotFoundError as e:
            error_msg = f"Data source not found: {self.data_source_id}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
            
        except APIError as e:
            # APIエラーをDataFetchErrorに変換
            error_msg = f"J-Quants API error for code {code}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
            
        except Exception as e:
            # 予期しないエラーの処理
            error_msg = f"Unexpected error fetching company {code}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataFetchError(error_msg)