"""
トークン管理システム

J-QuantsのリフレッシュトークンとIDトークンを安全に管理するためのシステム
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import logging

from app.services.auth import StrategyRegistry


logger = logging.getLogger(__name__)


class TokenManager:
    """トークンの管理を行うクラス"""
    
    def __init__(self):
        self.refresh_tokens: Dict[int, Tuple[str, datetime]] = {}
        self.id_tokens: Dict[int, Tuple[str, datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def get_valid_refresh_token(self, data_source_id: int) -> Optional[str]:
        """
        有効なリフレッシュトークンを取得
        
        Args:
            data_source_id: データソースID
            
        Returns:
            Optional[str]: 有効なリフレッシュトークン（期限切れの場合はNone）
        """
        async with self._lock:
            if data_source_id in self.refresh_tokens:
                token, expired_at = self.refresh_tokens[data_source_id]
                if datetime.utcnow() < expired_at:
                    logger.debug(f"Valid refresh token found for data_source_id: {data_source_id}")
                    return token
                else:
                    logger.info(f"Refresh token expired for data_source_id: {data_source_id}")
                    # 期限切れトークンを削除
                    del self.refresh_tokens[data_source_id]
            
            logger.debug(f"No valid refresh token for data_source_id: {data_source_id}")
            return None
    
    async def get_valid_id_token(self, data_source_id: int) -> Optional[str]:
        """
        有効なIDトークンを取得
        
        Args:
            data_source_id: データソースID
            
        Returns:
            Optional[str]: 有効なIDトークン（期限切れの場合はNone）
        """
        async with self._lock:
            if data_source_id in self.id_tokens:
                token, expired_at = self.id_tokens[data_source_id]
                if datetime.utcnow() < expired_at:
                    logger.debug(f"Valid ID token found for data_source_id: {data_source_id}")
                    return token
                else:
                    logger.info(f"ID token expired for data_source_id: {data_source_id}")
                    # 期限切れトークンを削除
                    del self.id_tokens[data_source_id]
            
            logger.debug(f"No valid ID token for data_source_id: {data_source_id}")
            return None
    
    async def store_refresh_token(self, data_source_id: int, token: str, expired_at: datetime):
        """
        リフレッシュトークンを保存
        
        Args:
            data_source_id: データソースID
            token: リフレッシュトークン
            expired_at: 有効期限
        """
        async with self._lock:
            self.refresh_tokens[data_source_id] = (token, expired_at)
            logger.info(f"Refresh token stored for data_source_id: {data_source_id}, expires at: {expired_at}")
    
    async def store_id_token(self, data_source_id: int, token: str, expired_at: datetime):
        """
        IDトークンを保存
        
        Args:
            data_source_id: データソースID
            token: IDトークン
            expired_at: 有効期限
        """
        async with self._lock:
            self.id_tokens[data_source_id] = (token, expired_at)
            logger.info(f"ID token stored for data_source_id: {data_source_id}, expires at: {expired_at}")
    
    async def clear_tokens(self, data_source_id: int):
        """
        指定されたデータソースのトークンを削除
        
        Args:
            data_source_id: データソースID
        """
        async with self._lock:
            removed_refresh = self.refresh_tokens.pop(data_source_id, None)
            removed_id = self.id_tokens.pop(data_source_id, None)
            
            if removed_refresh or removed_id:
                logger.info(f"Tokens cleared for data_source_id: {data_source_id}")
    
    async def clear_expired_tokens(self):
        """期限切れトークンを一括削除"""
        async with self._lock:
            now = datetime.utcnow()
            
            # 期限切れリフレッシュトークンを削除
            expired_refresh = [
                data_source_id for data_source_id, (_, expired_at) 
                in self.refresh_tokens.items() if now >= expired_at
            ]
            for data_source_id in expired_refresh:
                del self.refresh_tokens[data_source_id]
            
            # 期限切れIDトークンを削除
            expired_id = [
                data_source_id for data_source_id, (_, expired_at) 
                in self.id_tokens.items() if now >= expired_at
            ]
            for data_source_id in expired_id:
                del self.id_tokens[data_source_id]
            
            if expired_refresh or expired_id:
                logger.info(f"Cleared {len(expired_refresh)} expired refresh tokens and {len(expired_id)} expired ID tokens")
    
    async def get_token_status(self, data_source_id: int) -> Dict[str, Any]:
        """
        トークンの状態を取得
        
        Args:
            data_source_id: データソースID
            
        Returns:
            Dict[str, Any]: トークンの状態情報
        """
        async with self._lock:
            refresh_info = None
            id_info = None
            
            if data_source_id in self.refresh_tokens:
                _, expired_at = self.refresh_tokens[data_source_id]
                refresh_info = {
                    "exists": True,
                    "expired_at": expired_at.isoformat(),
                    "is_valid": datetime.utcnow() < expired_at
                }
            else:
                refresh_info = {"exists": False}
            
            if data_source_id in self.id_tokens:
                _, expired_at = self.id_tokens[data_source_id]
                id_info = {
                    "exists": True,
                    "expired_at": expired_at.isoformat(),
                    "is_valid": datetime.utcnow() < expired_at
                }
            else:
                id_info = {"exists": False}
            
            return {
                "data_source_id": data_source_id,
                "refresh_token": refresh_info,
                "id_token": id_info
            }


class AutoTokenRefresh:
    """トークンの自動更新を行うクラス"""
    
    def __init__(self, token_manager: TokenManager, data_source_service):
        self.token_manager = token_manager
        self.data_source_service = data_source_service
    
    async def ensure_valid_id_token(self, data_source_id: int) -> Optional[str]:
        """
        有効なIDトークンを保証（必要に応じて更新）
        
        Args:
            data_source_id: データソースID
            
        Returns:
            Optional[str]: 有効なIDトークン
        """
        # 既存のIDトークンをチェック
        id_token = await self.token_manager.get_valid_id_token(data_source_id)
        if id_token:
            return id_token
        
        # IDトークンが無効または期限切れの場合、リフレッシュトークンから取得
        refresh_token = await self.token_manager.get_valid_refresh_token(data_source_id)
        if not refresh_token:
            # リフレッシュトークンも無効な場合、新しく取得
            refresh_token = await self._get_new_refresh_token(data_source_id)
            if not refresh_token:
                logger.error(f"Failed to get refresh token for data_source_id: {data_source_id}")
                return None
        
        # リフレッシュトークンからIDトークンを取得
        id_token = await self._get_new_id_token(data_source_id, refresh_token)
        return id_token
    
    async def _get_new_refresh_token(self, data_source_id: int) -> Optional[str]:
        """
        新しいリフレッシュトークンを取得
        
        Args:
            data_source_id: データソースID
            
        Returns:
            Optional[str]: 新しいリフレッシュトークン
        """
        try:
            data_source = await self.data_source_service.get_data_source(data_source_id)
            if not data_source:
                logger.error(f"Data source not found: {data_source_id}")
                return None
            
            strategy_class = StrategyRegistry.get_strategy(data_source.provider_type)
            if not strategy_class:
                logger.error(f"Unsupported provider type: {data_source.provider_type}")
                return None
            
            strategy = strategy_class(base_url=data_source.base_url)
            credentials = data_source.get_credentials()
            
            if not credentials:
                logger.error(f"No credentials found for data_source_id: {data_source_id}")
                return None
            
            token, expired_at = strategy.get_refresh_token(credentials)
            if token and expired_at:
                await self.token_manager.store_refresh_token(data_source_id, token, expired_at)
                logger.info(f"New refresh token obtained for data_source_id: {data_source_id}")
                return token
            else:
                logger.error(f"Failed to get refresh token from strategy for data_source_id: {data_source_id}")
        except Exception as e:
            logger.error(f"Error getting new refresh token for data_source_id {data_source_id}: {e}")
        
        return None
    
    async def _get_new_id_token(self, data_source_id: int, refresh_token: str) -> Optional[str]:
        """
        新しいIDトークンを取得
        
        Args:
            data_source_id: データソースID
            refresh_token: リフレッシュトークン
            
        Returns:
            Optional[str]: 新しいIDトークン
        """
        try:
            data_source = await self.data_source_service.get_data_source(data_source_id)
            if not data_source:
                logger.error(f"Data source not found: {data_source_id}")
                return None
            
            strategy_class = StrategyRegistry.get_strategy(data_source.provider_type)
            if not strategy_class:
                logger.error(f"Unsupported provider type: {data_source.provider_type}")
                return None
            
            strategy = strategy_class(base_url=data_source.base_url)
            token, expired_at = strategy.get_id_token(refresh_token)
            
            if token and expired_at:
                await self.token_manager.store_id_token(data_source_id, token, expired_at)
                logger.info(f"New ID token obtained for data_source_id: {data_source_id}")
                return token
            else:
                logger.error(f"Failed to get ID token from strategy for data_source_id: {data_source_id}")
        except Exception as e:
            logger.error(f"Error getting new ID token for data_source_id {data_source_id}: {e}")
        
        return None


# グローバルインスタンス
token_manager = TokenManager()


async def get_token_manager() -> TokenManager:
    """トークンマネージャーのインスタンスを取得"""
    return token_manager


async def cleanup_expired_tokens():
    """期限切れトークンのクリーンアップタスク"""
    while True:
        try:
            await token_manager.clear_expired_tokens()
            # 1時間ごとにクリーンアップ
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in token cleanup task: {e}")
            await asyncio.sleep(60)  # エラー時は1分後に再試行