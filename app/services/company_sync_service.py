"""
企業データ同期サービス（リファクタリング版）

J-Quants APIから上場企業データを取得してデータベースに同期するサービス
責務を分離し、各コンポーネントを依存性注入で利用
"""

import logging
from datetime import datetime, date
import datetime as dt
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanySyncHistory
from app.services.jquants_client import JQuantsClientManager
from app.services.data_source_service import DataSourceService
from app.services.base_sync_service import BaseSyncService
from app.services.interfaces.company_sync_interfaces import (
    ICompanyDataFetcher,
    ICompanyDataMapper,
    ICompanyRepository
)
from app.services.company.company_data_fetcher import CompanyDataFetcher
from app.services.company.company_data_mapper import CompanyDataMapper
from app.services.company.company_repository import CompanyRepository
from app.core.exceptions import (
    APIError, DataValidationError, SyncError,
    DataSourceNotFoundError
)
from app.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class CompanySyncService(BaseSyncService[CompanySyncHistory]):
    """企業データ同期サービス"""
    
    def __init__(
        self, 
        db: AsyncSession,
        data_source_service: DataSourceService,
        jquants_client_manager: JQuantsClientManager,
        fetcher: Optional[ICompanyDataFetcher] = None,
        mapper: Optional[ICompanyDataMapper] = None,
        repository: Optional[ICompanyRepository] = None
    ):
        """
        初期化
        
        Args:
            db: データベースセッション
            data_source_service: データソースサービス
            jquants_client_manager: J-Quantsクライアント管理
            fetcher: データ取得サービス（オプション）
            mapper: データマッピングサービス（オプション）
            repository: リポジトリサービス（オプション）
        """
        super().__init__(db)
        self.data_source_service = data_source_service
        self.jquants_client_manager = jquants_client_manager
        
        # 依存サービスの初期化（未指定の場合はデフォルト実装を使用）
        self.fetcher = fetcher
        self.mapper = mapper or CompanyDataMapper()
        self.repository = repository or CompanyRepository(db)
    
    def _initialize_fetcher(self, data_source_id: int) -> ICompanyDataFetcher:
        """フェッチャーの遅延初期化"""
        if self.fetcher is None:
            self.fetcher = CompanyDataFetcher(
                jquants_client_manager=self.jquants_client_manager,
                data_source_id=data_source_id
            )
        return self.fetcher
    
    def get_history_model(self) -> type:
        """履歴モデルクラスを返す"""
        return CompanySyncHistory
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        同期処理のエントリーポイント
        
        Args:
            **kwargs: 同期パラメータ
            
        Returns:
            Dict[str, Any]: 同期結果
        """
        data_source_id = kwargs.get('data_source_id')
        sync_type = kwargs.get('sync_type', 'full')
        
        if data_source_id:
            # 通常の同期処理
            history = await self.sync_companies(data_source_id, sync_type)
            return {
                "status": history.status,
                "history_id": history.id,
                "total_companies": history.total_companies,
                "new_companies": history.new_companies,
                "updated_companies": history.updated_companies
            }
        else:
            # シンプル同期（data_source_idなし）
            return await self.sync_all_companies_simple()
    
    async def sync_companies(
        self, 
        data_source_id: int,
        sync_type: str = "full",
        sync_date: Optional[date] = None,
        execution_type: str = "manual"
    ) -> CompanySyncHistory:
        """
        企業データの同期を実行
        
        Args:
            data_source_id: J-QuantsデータソースのID
            sync_type: 同期タイプ（"full" または "incremental"）
            sync_date: 同期対象日
            execution_type: 実行タイプ
            
        Returns:
            CompanySyncHistory: 同期履歴
        """
        if sync_date is None:
            sync_date = dt.date.today()
        
        logger.info(f"Starting company sync for type: {sync_type}")
        
        # フェッチャーを初期化
        fetcher = self._initialize_fetcher(data_source_id)
        
        # 同期履歴を作成
        sync_history = await self.create_sync_history(
            sync_type=sync_type,
            sync_date=sync_date,
            execution_type=execution_type
        )
        
        try:
            # 1. データ取得
            companies_data = await fetcher.fetch_all_companies(target_date=sync_date)
            
            if not companies_data:
                logger.warning("No company data received from J-Quants API")
                # 空の結果でも成功として扱う
                return await self.update_sync_history_success(
                    sync_history,
                    total_companies=0,
                    new_companies=0,
                    updated_companies=0,
                    deleted_companies=0
                )
            
            logger.info(f"Retrieved {len(companies_data)} companies from J-Quants API")
            
            # 2. データ変換
            mapped_data_list = []
            for api_data in companies_data:
                mapped_data = self.mapper.map_to_model(api_data)
                if mapped_data:
                    mapped_data_list.append(mapped_data)
                else:
                    logger.warning(f"Failed to map company data: {api_data.get('Code', 'unknown')}")
            
            logger.info(f"Successfully mapped {len(mapped_data_list)} companies")
            
            # 3. データ保存
            stats = await self.repository.bulk_upsert(mapped_data_list)
            
            # 4. 非アクティブ化処理（フル同期の場合）
            deleted_count = 0
            if sync_type == "full" and mapped_data_list:
                active_codes = [data["code"] for data in mapped_data_list]
                deleted_count = await self.repository.deactivate_companies(active_codes)
            
            # 5. コミット
            await self.repository.commit()
            
            # 6. 同期履歴を更新
            sync_history = await self.update_sync_history_success(
                sync_history,
                total_companies=len(companies_data),
                new_companies=stats["new_count"],
                updated_companies=stats["updated_count"],
                deleted_companies=deleted_count
            )
            
            logger.info(
                f"Company sync completed successfully. "
                f"New: {stats['new_count']}, "
                f"Updated: {stats['updated_count']}, "
                f"Deleted: {deleted_count}"
            )
            return sync_history
            
        except Exception as e:
            # エラーハンドリング
            error_info = await ErrorHandler.handle_sync_error(
                error=e,
                service_name="CompanySyncServiceV2",
                context={
                    "sync_type": sync_type,
                    "data_source_id": data_source_id,
                    "sync_date": sync_date.isoformat()
                },
                db=self.db,
                sync_history_id=sync_history.id
            )
            
            # 同期履歴を更新
            await self.update_sync_history_failure(sync_history, e)
            
            # ロールバック
            await self.repository.rollback()
            
            raise
    
    async def get_sync_history_with_count(
        self, 
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Tuple[List[CompanySyncHistory], int]:
        """
        同期履歴を取得（カウント付き）
        
        Args:
            limit: 取得件数制限
            offset: オフセット
            status: ステータスフィルタ
            
        Returns:
            Tuple[List[CompanySyncHistory], int]: (同期履歴リスト, 総件数)
        """
        from sqlalchemy import select, func
        
        # 基底クラスのメソッドを使用して履歴を取得
        histories = await self.get_sync_history(limit, offset, status)
        
        # 総件数を取得
        query = select(func.count(CompanySyncHistory.id))
        if status:
            query = query.where(CompanySyncHistory.status == status)
        
        result = await self.db.execute(query)
        total = result.scalar()
        
        return histories, total
    
    async def sync_all_companies_simple(self) -> Dict[str, Any]:
        """
        全上場企業を同期（シンプル版・フル同期）
        
        Returns:
            Dict[str, Any]: 同期結果
        """
        start_time = datetime.utcnow()
        
        try:
            # J-Quantsクライアントを取得（最初の有効なデータソースを使用）
            data_source = await self.data_source_service.get_jquants_source()
            if not data_source:
                raise Exception("No active J-Quants data source found")
            
            # フェッチャーを初期化
            fetcher = self._initialize_fetcher(data_source.id)
            
            # 1. J-Quantsから全銘柄取得
            companies_data = await fetcher.fetch_all_companies()
            
            if not companies_data:
                raise Exception("No company data received from J-Quants API")
            
            logger.info(f"Retrieved {len(companies_data)} companies from J-Quants API")
            
            # 2. データ変換
            mapped_data_list = []
            for api_data in companies_data:
                mapped_data = self.mapper.map_to_model(api_data)
                if mapped_data:
                    mapped_data_list.append(mapped_data)
            
            # 3. 既存の全企業を非アクティブ化
            await self.repository.deactivate_companies([])
            
            # 4. 取得データを一括更新（upsert）
            stats = await self.repository.bulk_upsert(mapped_data_list)
            
            # 5. コミット
            await self.repository.commit()
            
            # 6. 実行結果を返す
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "success",
                "sync_count": stats["new_count"] + stats["updated_count"],
                "duration": duration,
                "executed_at": start_time
            }
            
        except Exception as e:
            await self.repository.rollback()
            # エラーハンドリング
            self.handle_error(e, {
                "method": "sync_all_companies_simple",
                "start_time": start_time
            })
            return {
                "status": "failed",
                "error": str(e),
                "executed_at": start_time
            }