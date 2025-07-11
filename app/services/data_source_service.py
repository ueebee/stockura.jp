from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from datetime import datetime
import logging

from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate, TokenResponse, DataSourceListResponse
from app.services.token_manager import get_token_manager, AutoTokenRefresh

logger = logging.getLogger(__name__)


class DataSourceService:
    """データソースサービス"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.token_manager = None
        self.auto_refresh = None

    async def create_data_source(self, data: DataSourceCreate) -> DataSource:
        """データソースを作成します"""
        # データソースモデルのインスタンスを作成
        data_source = DataSource(
            name=data.name,
            description=data.description,
            provider_type=data.provider_type,
            is_enabled=data.is_enabled,
            base_url=data.base_url,
            api_version=data.api_version,
            rate_limit_per_minute=data.rate_limit_per_minute,
            rate_limit_per_hour=data.rate_limit_per_hour,
            rate_limit_per_day=data.rate_limit_per_day,
        )

        # 認証情報がある場合は暗号化して保存
        if data.credentials:
            data_source.set_credentials(data.credentials)

        # データベースに保存
        self.db.add(data_source)
        await self.db.commit()
        await self.db.refresh(data_source)
        
        return data_source

    async def get_data_source(self, data_source_id: int) -> Optional[DataSource]:
        """データソースを取得します"""
        result = await self.db.execute(
            select(DataSource).where(DataSource.id == data_source_id)
        )
        return result.scalar_one_or_none()

    async def list_data_sources(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_enabled: Optional[bool] = None
    ) -> DataSourceListResponse:
        """データソース一覧を取得します"""
        from app.schemas.data_source import DataSourceListResponse, DataSourceResponse
        
        # クエリを構築
        query = select(DataSource)
        
        # フィルタリング
        if is_enabled is not None:
            query = query.where(DataSource.is_enabled == is_enabled)
        
        # 総件数を取得
        count_query = select(func.count()).select_from(DataSource)
        if is_enabled is not None:
            count_query = count_query.where(DataSource.is_enabled == is_enabled)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # ページネーション
        query = query.offset(skip).limit(limit).order_by(DataSource.id)
        
        # データを取得
        result = await self.db.execute(query)
        data_sources = result.scalars().all()
        
        # レスポンスを構築
        items = [DataSourceResponse.model_validate(ds) for ds in data_sources]
        
        return DataSourceListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )

    async def get_jquants_source(self) -> Optional[DataSource]:
        """有効なJ-Quantsデータソースを取得します"""
        result = await self.db.execute(
            select(DataSource).where(
                DataSource.provider_type == "jquants",
                DataSource.is_enabled == True
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def update_data_source(
        self, 
        data_source_id: int, 
        data: DataSourceUpdate
    ) -> Optional[DataSource]:
        """データソースを更新します"""
        # 更新するフィールドを準備
        update_data = {}
        
        if data.name is not None:
            update_data["name"] = data.name
        if data.description is not None:
            update_data["description"] = data.description
        if data.provider_type is not None:
            update_data["provider_type"] = data.provider_type
        if data.is_enabled is not None:
            update_data["is_enabled"] = data.is_enabled
        if data.base_url is not None:
            update_data["base_url"] = data.base_url
        if data.api_version is not None:
            update_data["api_version"] = data.api_version
        if data.rate_limit_per_minute is not None:
            update_data["rate_limit_per_minute"] = data.rate_limit_per_minute
        if data.rate_limit_per_hour is not None:
            update_data["rate_limit_per_hour"] = data.rate_limit_per_hour
        if data.rate_limit_per_day is not None:
            update_data["rate_limit_per_day"] = data.rate_limit_per_day

        # データソースを取得
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            return None

        # 認証情報がある場合は暗号化して保存
        if data.credentials is not None:
            data_source.set_credentials(data.credentials)

        # フィールドを更新
        for field, value in update_data.items():
            setattr(data_source, field, value)

        # データベースに保存
        await self.db.commit()
        await self.db.refresh(data_source)
        
        return data_source

    async def delete_data_source(self, data_source_id: int) -> bool:
        """データソースを削除します"""
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            return False

        await self.db.delete(data_source)
        await self.db.commit()
        
        return True

    async def get_refresh_token(self, data_source_id: int) -> Optional[TokenResponse]:
        """リフレッシュトークンを取得します"""
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            logger.error(f"Data source not found: {data_source_id}")
            return None

        # トークンマネージャーを初期化
        if self.token_manager is None:
            self.token_manager = await get_token_manager()

        try:
            # 既存の有効なトークンがあるかチェック
            existing_token = await self.token_manager.get_valid_refresh_token(data_source_id)
            if existing_token:
                # 既存トークンの有効期限を取得
                token_status = await self.token_manager.get_token_status(data_source_id)
                refresh_info = token_status.get("refresh_token", {})
                expired_at = datetime.fromisoformat(refresh_info["expired_at"]) if refresh_info.get("expired_at") else None
                
                logger.info(f"Using existing refresh token for data_source_id: {data_source_id}")
                return TokenResponse(
                    token=existing_token,
                    expired_at=expired_at,
                    token_type="refresh_token"
                )

            # 新しいトークンを取得
            success, data = data_source.get_refresh_token()
            if success and data:
                token = data.get("refresh_token")
                expired_at = datetime.fromisoformat(data.get("expired_at")) if data.get("expired_at") else None
                
                # トークンマネージャーに保存
                if token and expired_at:
                    await self.token_manager.store_refresh_token(data_source_id, token, expired_at)
                    logger.info(f"New refresh token obtained and stored for data_source_id: {data_source_id}")
                
                return TokenResponse(
                    token=token,
                    expired_at=expired_at,
                    token_type="refresh_token"
                )
            else:
                error_msg = data.get('error') if data else 'Unknown error'
                logger.error(f"Failed to get refresh token for data_source_id {data_source_id}: {error_msg}")
        except Exception as e:
            logger.error(f"Error getting refresh token for data_source_id {data_source_id}: {e}")
        
        return None

    async def get_id_token(
        self, 
        data_source_id: int, 
        refresh_token: str
    ) -> Optional[TokenResponse]:
        """IDトークンを取得します"""
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            logger.error(f"Data source not found: {data_source_id}")
            return None

        # トークンマネージャーを初期化
        if self.token_manager is None:
            self.token_manager = await get_token_manager()

        try:
            # 既存の有効なIDトークンがあるかチェック
            existing_token = await self.token_manager.get_valid_id_token(data_source_id)
            if existing_token:
                # 既存トークンの有効期限を取得
                token_status = await self.token_manager.get_token_status(data_source_id)
                id_info = token_status.get("id_token", {})
                expired_at = datetime.fromisoformat(id_info["expired_at"]) if id_info.get("expired_at") else None
                
                logger.info(f"Using existing ID token for data_source_id: {data_source_id}")
                return TokenResponse(
                    token=existing_token,
                    expired_at=expired_at,
                    token_type="id_token"
                )

            # 新しいIDトークンを取得
            success, data = data_source.get_id_token(refresh_token)
            if success and data:
                token = data.get("id_token")
                expired_at = datetime.fromisoformat(data.get("expired_at")) if data.get("expired_at") else None
                
                # トークンマネージャーに保存
                if token and expired_at:
                    await self.token_manager.store_id_token(data_source_id, token, expired_at)
                    logger.info(f"New ID token obtained and stored for data_source_id: {data_source_id}")
                
                return TokenResponse(
                    token=token,
                    expired_at=expired_at,
                    token_type="id_token"
                )
            else:
                error_msg = data.get('error') if data else 'Unknown error'
                logger.error(f"Failed to get ID token for data_source_id {data_source_id}: {error_msg}")
        except Exception as e:
            logger.error(f"Error getting ID token for data_source_id {data_source_id}: {e}")
        
        return None

    async def get_valid_api_token(self, data_source_id: int) -> Optional[str]:
        """
        APIアクセス用の有効なトークンを取得（自動更新対応）
        
        Args:
            data_source_id: データソースID
            
        Returns:
            Optional[str]: 有効なIDトークン
        """
        # トークンマネージャーとオートリフレッシュを初期化
        if self.token_manager is None:
            self.token_manager = await get_token_manager()
        if self.auto_refresh is None:
            self.auto_refresh = AutoTokenRefresh(self.token_manager, self)
        
        try:
            # 自動更新機能を使用して有効なIDトークンを取得
            return await self.auto_refresh.ensure_valid_id_token(data_source_id)
        except Exception as e:
            logger.error(f"Error getting valid API token for data_source_id {data_source_id}: {e}")
            return None 