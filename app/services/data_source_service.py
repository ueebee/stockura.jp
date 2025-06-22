from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate, TokenResponse


class DataSourceService:
    """データソースサービス"""

    def __init__(self, db: AsyncSession):
        self.db = db

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
    ) -> tuple[List[DataSource], int]:
        """データソース一覧を取得します"""
        # クエリを構築
        query = select(DataSource)
        
        # フィルタリング
        if is_enabled is not None:
            query = query.where(DataSource.is_enabled == is_enabled)
        
        # 総件数を取得
        count_result = await self.db.execute(
            select(DataSource.id).select_from(query.subquery())
        )
        total = len(count_result.scalars().all())
        
        # ページネーション
        query = query.offset(skip).limit(limit)
        
        # データを取得
        result = await self.db.execute(query)
        data_sources = result.scalars().all()
        
        return data_sources, total

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
            return None

        try:
            # データソースモデルのメソッドを使用してトークンを取得
            result = data_source.get_refresh_token()
            if result and isinstance(result, tuple) and len(result) == 2:
                success, data = result
                if success:
                    return TokenResponse(
                        token=data.get("refresh_token"),
                        expired_at=data.get("expired_at"),
                        token_type="refresh_token"
                    )
        except Exception as e:
            # ログ出力やエラーハンドリングを追加
            print(f"Error getting refresh token: {e}")
        
        return None

    async def get_id_token(
        self, 
        data_source_id: int, 
        refresh_token: str
    ) -> Optional[TokenResponse]:
        """IDトークンを取得します"""
        data_source = await self.get_data_source(data_source_id)
        if not data_source:
            return None

        try:
            # データソースモデルのメソッドを使用してトークンを取得
            result = data_source.get_id_token(refresh_token)
            if result and isinstance(result, tuple) and len(result) == 2:
                success, data = result
                if success:
                    return TokenResponse(
                        token=data.get("id_token"),
                        expired_at=data.get("expired_at"),
                        token_type="id_token"
                    )
        except Exception as e:
            # ログ出力やエラーハンドリングを追加
            print(f"Error getting id token: {e}")
        
        return None 