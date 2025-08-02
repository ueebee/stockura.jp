"""
J-Quantsクライアントファクトリー

J-Quantsクライアントのインスタンスを生成するファクトリークラス
"""

import logging
from typing import Optional

from app.domain.interfaces import IAPIClient
from app.services.data_source_service import DataSourceService
from app.services.token_manager import TokenManager, get_token_manager
from app.infrastructure.http import HTTPClient, RetryConfig
from app.infrastructure.rate_limiting import RateLimitedHTTPClient, RateLimiterFactory
from app.infrastructure.auth import JQuantsAuthenticationService
from .api_client import JQuantsAPIClient
from .request_builder import JQuantsRequestBuilder
from .response_parser import JQuantsResponseParser

logger = logging.getLogger(__name__)


class JQuantsClientFactory:
    """
    J-Quantsクライアントファクトリー
    
    依存関係を解決してクライアントインスタンスを生成
    """
    
    @staticmethod
    async def create(
        data_source_service: DataSourceService,
        data_source_id: int,
        token_manager: Optional[TokenManager] = None,
        retry_config: Optional[RetryConfig] = None
    ) -> IAPIClient:
        """
        J-Quantsクライアントインスタンスを生成
        
        Args:
            data_source_service: データソースサービス
            data_source_id: データソースID
            token_manager: トークンマネージャー（オプション）
            retry_config: リトライ設定（オプション）
            
        Returns:
            IAPIClient: J-Quantsクライアントインスタンス
            
        Raises:
            Exception: クライアント生成に失敗した場合
        """
        try:
            logger.info(f"Creating J-Quants client for data_source_id: {data_source_id}")
            
            # データソース情報を取得
            data_source = await data_source_service.get_data_source(data_source_id)
            if not data_source:
                raise ValueError(f"Data source not found: {data_source_id}")
            
            if data_source.provider_type != "jquants":
                raise ValueError(
                    f"Invalid provider type for J-Quants client: {data_source.provider_type}"
                )
            
            # トークンマネージャーを取得
            if token_manager is None:
                token_manager = await get_token_manager()
            
            # レートリミッターを作成
            rate_limiter = await RateLimiterFactory.create_for_data_source(data_source)
            
            # レート制限付きHTTPクライアントを生成
            http_client = RateLimitedHTTPClient(
                rate_limiter=rate_limiter,
                base_url=data_source.base_url or "https://api.jquants.com",
                timeout=30.0,
                retry_config=retry_config or RetryConfig(
                    max_retries=3,
                    initial_delay=1.0,
                    max_delay=30.0,
                    exponential_base=2.0,
                    jitter=True
                )
            )
            
            # 認証サービスを生成
            auth_service = JQuantsAuthenticationService(
                data_source_service=data_source_service,
                data_source_id=data_source_id,
                token_manager=token_manager
            )
            
            # リクエストビルダーとレスポンスパーサーを生成
            request_builder = JQuantsRequestBuilder()
            response_parser = JQuantsResponseParser()
            
            # J-Quantsクライアントを生成
            client = JQuantsAPIClient(
                http_client=http_client,
                auth_service=auth_service,
                request_builder=request_builder,
                response_parser=response_parser
            )
            
            logger.info("J-Quants client created successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create J-Quants client: {e}")
            raise
    
    @staticmethod
    async def create_with_config(
        data_source_service: DataSourceService,
        data_source_id: int,
        config: dict
    ) -> IAPIClient:
        """
        設定付きでJ-Quantsクライアントインスタンスを生成
        
        Args:
            data_source_service: データソースサービス
            data_source_id: データソースID
            config: クライアント設定
                - token_manager: トークンマネージャー
                - retry_config: リトライ設定
                - timeout: タイムアウト設定
                
        Returns:
            IAPIClient: J-Quantsクライアントインスタンス
        """
        # 設定から各パラメータを取得
        token_manager = config.get("token_manager")
        
        # リトライ設定を構築
        retry_config_dict = config.get("retry_config", {})
        retry_config = RetryConfig(
            max_retries=retry_config_dict.get("max_retries", 3),
            initial_delay=retry_config_dict.get("initial_delay", 1.0),
            max_delay=retry_config_dict.get("max_delay", 30.0),
            exponential_base=retry_config_dict.get("exponential_base", 2.0),
            jitter=retry_config_dict.get("jitter", True)
        )
        
        return await JQuantsClientFactory.create(
            data_source_service=data_source_service,
            data_source_id=data_source_id,
            token_manager=token_manager,
            retry_config=retry_config
        )