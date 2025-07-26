"""
J-Quants認証サービス

J-Quants APIの認証を管理する実装
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.domain.interfaces import IAuthenticationService
from app.domain.exceptions import AuthenticationError
from app.services.data_source_service import DataSourceService
from app.services.token_manager import TokenManager

logger = logging.getLogger(__name__)


class JQuantsAuthenticationService(IAuthenticationService):
    """
    J-Quants認証サービス
    
    J-Quants APIのトークン管理と自動更新を提供
    """
    
    def __init__(
        self,
        data_source_service: DataSourceService,
        data_source_id: int,
        token_manager: TokenManager,
        token_refresh_buffer: timedelta = timedelta(minutes=5)
    ):
        """
        初期化
        
        Args:
            data_source_service: データソースサービス
            data_source_id: データソースID
            token_manager: トークン管理サービス
            token_refresh_buffer: トークン更新の余裕時間
        """
        self.data_source_service = data_source_service
        self.data_source_id = data_source_id
        self.token_manager = token_manager
        self.token_refresh_buffer = token_refresh_buffer
    
    async def get_access_token(self) -> str:
        """
        有効なアクセストークンを取得
        
        必要に応じて自動的にトークンをリフレッシュする
        
        Returns:
            str: 有効なアクセストークン（IDトークン）
            
        Raises:
            AuthenticationError: 認証に失敗した場合
        """
        try:
            # 既存の有効なIDトークンを確認
            id_token = await self.token_manager.get_valid_id_token(self.data_source_id)
            if id_token:
                logger.debug("Using existing valid ID token")
                return id_token
            
            # IDトークンが無効または存在しない場合、リフレッシュトークンを確認
            refresh_token = await self.token_manager.get_valid_refresh_token(self.data_source_id)
            if not refresh_token:
                # リフレッシュトークンも無効な場合、新規取得
                logger.info("No valid refresh token found, obtaining new one")
                refresh_token, _ = await self._get_new_refresh_token()
            
            # リフレッシュトークンを使用してIDトークンを取得
            logger.info("Obtaining new ID token using refresh token")
            id_token, _ = await self._get_id_token_from_refresh(refresh_token)
            
            return id_token
            
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise AuthenticationError(
                message=f"Failed to obtain valid access token: {str(e)}",
                error_code="AUTH_TOKEN_ERROR",
                details={"data_source_id": self.data_source_id}
            )
    
    async def refresh_token(self) -> Tuple[str, datetime]:
        """
        トークンをリフレッシュ
        
        Returns:
            Tuple[str, datetime]: (新しいIDトークン, 有効期限)
            
        Raises:
            AuthenticationError: リフレッシュに失敗した場合
        """
        try:
            # 現在のリフレッシュトークンを取得
            refresh_token = await self.token_manager.get_valid_refresh_token(self.data_source_id)
            if not refresh_token:
                # リフレッシュトークンがない場合は新規取得
                refresh_token, _ = await self._get_new_refresh_token()
            
            # IDトークンを取得
            return await self._get_id_token_from_refresh(refresh_token)
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise AuthenticationError(
                message=f"Failed to refresh token: {str(e)}",
                error_code="AUTH_REFRESH_ERROR",
                details={"data_source_id": self.data_source_id}
            )
    
    async def is_token_valid(self) -> bool:
        """
        現在のトークンが有効かチェック
        
        Returns:
            bool: トークンが有効な場合True
        """
        try:
            # バッファを考慮して有効期限をチェック
            token_status = await self.token_manager.get_token_status(self.data_source_id)
            id_token_info = token_status.get("id_token", {})
            
            if not id_token_info.get("exists"):
                return False
            
            # 有効期限の確認（バッファを考慮）
            if id_token_info.get("expired_at"):
                expired_at = datetime.fromisoformat(id_token_info["expired_at"])
                return datetime.utcnow() + self.token_refresh_buffer < expired_at
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking token validity: {e}")
            return False
    
    async def clear_tokens(self) -> None:
        """
        保存されているトークンをクリア
        """
        await self.token_manager.clear_tokens(self.data_source_id)
        logger.info(f"Cleared tokens for data_source_id: {self.data_source_id}")
    
    async def _get_new_refresh_token(self) -> Tuple[str, datetime]:
        """
        新しいリフレッシュトークンを取得
        
        Returns:
            Tuple[str, datetime]: (リフレッシュトークン, 有効期限)
            
        Raises:
            AuthenticationError: 取得に失敗した場合
        """
        try:
            # データソースサービスを使用してリフレッシュトークンを取得
            token_response = await self.data_source_service.get_refresh_token(self.data_source_id)
            
            if not token_response:
                raise AuthenticationError(
                    message="Failed to obtain refresh token from data source",
                    error_code="REFRESH_TOKEN_ERROR"
                )
            
            # トークンマネージャーに保存
            await self.token_manager.store_refresh_token(
                self.data_source_id,
                token_response.token,
                token_response.expired_at
            )
            
            return token_response.token, token_response.expired_at
            
        except Exception as e:
            logger.error(f"Failed to get new refresh token: {e}")
            raise AuthenticationError(
                message=f"Failed to obtain new refresh token: {str(e)}",
                error_code="REFRESH_TOKEN_ERROR"
            )
    
    async def _get_id_token_from_refresh(self, refresh_token: str) -> Tuple[str, datetime]:
        """
        リフレッシュトークンからIDトークンを取得
        
        Args:
            refresh_token: リフレッシュトークン
            
        Returns:
            Tuple[str, datetime]: (IDトークン, 有効期限)
            
        Raises:
            AuthenticationError: 取得に失敗した場合
        """
        try:
            # データソースサービスを使用してIDトークンを取得
            token_response = await self.data_source_service.get_id_token(
                self.data_source_id,
                refresh_token
            )
            
            if not token_response:
                raise AuthenticationError(
                    message="Failed to obtain ID token from refresh token",
                    error_code="ID_TOKEN_ERROR"
                )
            
            # トークンマネージャーに保存
            await self.token_manager.store_id_token(
                self.data_source_id,
                token_response.token,
                token_response.expired_at
            )
            
            return token_response.token, token_response.expired_at
            
        except Exception as e:
            logger.error(f"Failed to get ID token from refresh token: {e}")
            raise AuthenticationError(
                message=f"Failed to obtain ID token: {str(e)}",
                error_code="ID_TOKEN_ERROR"
            )