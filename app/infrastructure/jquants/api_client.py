"""
J-Quants APIクライアント実装

J-Quants APIとの通信を行う具体的な実装
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import date

from app.domain.interfaces import IAPIClient, IAuthenticationService
from app.domain.dto import CompanyInfoDTO, DailyQuoteDTO
from app.domain.exceptions import (
    JQuantsAPIException,
    DataValidationError,
    NetworkError,
    AuthenticationError,
    RateLimitError
)
from app.infrastructure.http import HTTPClient
from .request_builder import JQuantsRequestBuilder
from .response_parser import JQuantsResponseParser

logger = logging.getLogger(__name__)


class JQuantsAPIClient(IAPIClient):
    """
    J-Quants API実装
    
    J-Quants APIとの通信を行う具体的な実装クラス
    """
    
    def __init__(
        self,
        http_client: HTTPClient,
        auth_service: IAuthenticationService,
        request_builder: Optional[JQuantsRequestBuilder] = None,
        response_parser: Optional[JQuantsResponseParser] = None
    ):
        """
        初期化
        
        Args:
            http_client: HTTPクライアント
            auth_service: 認証サービス
            request_builder: リクエストビルダー（オプション）
            response_parser: レスポンスパーサー（オプション）
        """
        self.http_client = http_client
        self.auth_service = auth_service
        self.request_builder = request_builder or JQuantsRequestBuilder()
        self.response_parser = response_parser or JQuantsResponseParser()
    
    async def get_listed_companies(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        上場企業情報を取得
        
        Args:
            code: 銘柄コード（4桁）
            target_date: 基準日
            
        Returns:
            List[Dict[str, Any]]: 上場企業情報のリスト
            
        Raises:
            AuthenticationError: 認証エラー
            NetworkError: ネットワークエラー
            DataValidationError: データ検証エラー
        """
        try:
            # 認証トークン取得
            access_token = await self.auth_service.get_access_token()
            
            # リクエスト構築
            endpoint, params, headers = self.request_builder.build_listed_info_request(
                code=code,
                target_date=target_date,
                access_token=access_token
            )
            
            # APIリクエスト
            logger.info(f"Fetching listed companies info - code: {code}, date: {target_date}")
            response = await self.http_client.get(
                endpoint=endpoint,
                params=params,
                headers=headers
            )
            
            # レスポンス処理
            response_data = response.json()
            return self._handle_response(response_data, "listed_info")
            
        except (AuthenticationError, NetworkError, DataValidationError):
            # 既知の例外はそのまま再発生
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_listed_companies: {e}")
            raise JQuantsAPIException(
                message=f"Failed to get listed companies: {str(e)}",
                error_code="API_ERROR"
            )
    
    async def get_daily_quotes(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        specific_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        日次株価データを取得
        
        Args:
            code: 銘柄コード（5桁）
            target_date: 取得日付
            from_date: 取得開始日
            to_date: 取得終了日
            specific_codes: 特定銘柄コードリスト
            
        Returns:
            List[Dict[str, Any]]: 株価データのリスト
            
        Raises:
            AuthenticationError: 認証エラー
            NetworkError: ネットワークエラー
            DataValidationError: データ検証エラー
        """
        try:
            # 認証トークン取得
            access_token = await self.auth_service.get_access_token()
            
            # 複数銘柄の場合は個別にリクエスト
            if specific_codes and len(specific_codes) > 1:
                all_quotes = []
                for stock_code in specific_codes:
                    quotes = await self._get_single_stock_quotes(
                        code=stock_code,
                        target_date=target_date,
                        from_date=from_date,
                        to_date=to_date,
                        access_token=access_token
                    )
                    all_quotes.extend(quotes)
                return all_quotes
            
            # 単一銘柄または全銘柄のリクエスト
            return await self._get_quotes_with_pagination(
                code=code or (specific_codes[0] if specific_codes else None),
                target_date=target_date,
                from_date=from_date,
                to_date=to_date,
                access_token=access_token
            )
            
        except (AuthenticationError, NetworkError, DataValidationError):
            # 既知の例外はそのまま再発生
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_daily_quotes: {e}")
            raise JQuantsAPIException(
                message=f"Failed to get daily quotes: {str(e)}",
                error_code="API_ERROR"
            )
    
    async def test_connection(self) -> bool:
        """
        API接続をテスト
        
        Returns:
            bool: 接続成功時はTrue
            
        Raises:
            AuthenticationError: 認証エラー
            NetworkError: ネットワークエラー
        """
        try:
            # 最小限のリクエストで接続確認
            companies = await self.get_listed_companies(code="7203")  # トヨタ自動車
            return len(companies) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def _get_single_stock_quotes(
        self,
        code: str,
        target_date: Optional[date],
        from_date: Optional[date],
        to_date: Optional[date],
        access_token: str
    ) -> List[Dict[str, Any]]:
        """
        単一銘柄の株価データを取得
        
        Args:
            code: 銘柄コード
            target_date: 取得日付
            from_date: 取得開始日
            to_date: 取得終了日
            access_token: アクセストークン
            
        Returns:
            List[Dict[str, Any]]: 株価データのリスト
        """
        return await self._get_quotes_with_pagination(
            code=code,
            target_date=target_date,
            from_date=from_date,
            to_date=to_date,
            access_token=access_token
        )
    
    async def _get_quotes_with_pagination(
        self,
        code: Optional[str],
        target_date: Optional[date],
        from_date: Optional[date],
        to_date: Optional[date],
        access_token: str
    ) -> List[Dict[str, Any]]:
        """
        ページネーション対応で株価データを取得
        
        Args:
            code: 銘柄コード
            target_date: 取得日付
            from_date: 取得開始日
            to_date: 取得終了日
            access_token: アクセストークン
            
        Returns:
            List[Dict[str, Any]]: 株価データのリスト
        """
        all_quotes = []
        pagination_key = None
        
        while True:
            # リクエスト構築
            endpoint, params, headers = self.request_builder.build_daily_quotes_request(
                code=code,
                date=target_date,
                from_date=from_date,
                to_date=to_date,
                pagination_key=pagination_key,
                access_token=access_token
            )
            
            # APIリクエスト
            logger.debug(f"Fetching daily quotes - page: {pagination_key or 'first'}")
            response = await self.http_client.get(
                endpoint=endpoint,
                params=params,
                headers=headers
            )
            
            # レスポンス処理
            response_data = response.json()
            data = self._handle_response(response_data, "daily_quotes")
            
            # ページネーション処理
            if isinstance(data, dict):
                quotes = data.get("daily_quotes", [])
                all_quotes.extend(quotes)
                
                # 次のページがあるかチェック
                pagination_key = data.get("pagination_key")
                if not pagination_key:
                    break
            else:
                # ページネーションなしの場合
                all_quotes.extend(data)
                break
        
        return all_quotes
    
    def _handle_response(self, response: Dict[str, Any], response_type: str) -> Any:
        """
        レスポンスを処理
        
        Args:
            response: レスポンスデータ（辞書）
            response_type: レスポンスタイプ（"listed_info" or "daily_quotes"）
            
        Returns:
            Any: パースされたレスポンスデータ
            
        Raises:
            DataValidationError: レスポンスの検証エラー
            JQuantsAPIException: APIエラー
        """
        try:
            # データは既に辞書形式
            data = response
            
            # エラーレスポンスのチェック
            if "error" in data:
                error_code = data.get("error_code", "UNKNOWN_ERROR")
                error_message = data.get("error_description", data.get("error"))
                
                # レート制限エラーの特別処理
                if error_code == "RATE_LIMIT_EXCEEDED":
                    retry_after = data.get("retry_after")
                    raise RateLimitError(
                        message=error_message,
                        retry_after=retry_after,
                        details=data
                    )
                
                raise JQuantsAPIException(
                    message=error_message,
                    error_code=error_code,
                    details=data
                )
            
            # レスポンスの検証とパース
            return self.response_parser.parse_response(data, response_type)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to parse response: {e}")
            raise DataValidationError(
                message=f"Invalid response format: {str(e)}",
                error_code="INVALID_RESPONSE"
            )