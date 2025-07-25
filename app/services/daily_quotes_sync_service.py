"""
株価データ同期サービス（リファクタリング版）

J-Quants APIから株価データを取得し、データベースに保存・更新する機能を提供
責務を分離し、各コンポーネントを依存性注入で利用
"""

import logging
import json
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.daily_quote import DailyQuotesSyncHistory
from app.services.jquants_client import JQuantsClientManager
from app.services.data_source_service import DataSourceService
from app.services.base_sync_service import BaseSyncService
from app.services.interfaces.daily_quotes_sync_interfaces import (
    IDailyQuotesDataFetcher,
    IDailyQuotesDataMapper,
    IDailyQuotesRepository,
    DataFetchError,
    RateLimitError
)
from app.services.daily_quotes.daily_quotes_data_fetcher import DailyQuotesDataFetcher
from app.services.daily_quotes.daily_quotes_data_mapper import DailyQuotesDataMapper
from app.services.daily_quotes.daily_quotes_repository import DailyQuotesRepository
from app.core.exceptions import (
    APIError, DataValidationError, SyncError,
    DataSourceNotFoundError
)
from app.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class DailyQuotesSyncService(BaseSyncService[DailyQuotesSyncHistory]):
    """株価データ同期サービス"""
    
    def __init__(
        self,
        data_source_service: DataSourceService,
        jquants_client_manager: JQuantsClientManager,
        db: Optional[AsyncSession] = None,
        fetcher: Optional[IDailyQuotesDataFetcher] = None,
        mapper: Optional[IDailyQuotesDataMapper] = None,
        repository: Optional[IDailyQuotesRepository] = None
    ):
        """
        初期化
        
        Args:
            data_source_service: データソースサービス
            jquants_client_manager: J-Quantsクライアント管理
            db: データベースセッション（オプション）
            fetcher: データ取得サービス（オプション）
            mapper: データマッピングサービス（オプション）
            repository: リポジトリサービス（オプション）
        """
        # dbが指定されていない場合は基底クラスの初期化をスキップ
        self._has_db = db is not None
        if self._has_db:
            super().__init__(db)
        else:
            # 基底クラスを初期化せずにロガーのみ設定
            self.logger = logging.getLogger(self.__class__.__name__)
        
        self.data_source_service = data_source_service
        self.jquants_client_manager = jquants_client_manager
        
        # 依存サービスの初期化（未指定の場合はNone）
        self._fetcher = fetcher
        self.mapper = mapper or DailyQuotesDataMapper()
        self._repository = repository
        self._data_source_id = None
    
    def _initialize_fetcher(self, data_source_id: int) -> IDailyQuotesDataFetcher:
        """フェッチャーの遅延初期化"""
        if self._fetcher is None or self._data_source_id != data_source_id:
            self._fetcher = DailyQuotesDataFetcher(
                jquants_client_manager=self.jquants_client_manager,
                data_source_id=data_source_id
            )
            self._data_source_id = data_source_id
        return self._fetcher
    
    def _initialize_repository(self, session: AsyncSession) -> IDailyQuotesRepository:
        """リポジトリの初期化（セッションごと）"""
        return DailyQuotesRepository(session)
    
    def get_history_model(self) -> type:
        """履歴モデルクラスを返す"""
        return DailyQuotesSyncHistory
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        同期処理のエントリーポイント
        
        Args:
            **kwargs: 同期パラメータ
            
        Returns:
            Dict[str, Any]: 同期結果
        """
        # パラメータの取得
        data_source_id = kwargs['data_source_id']
        sync_type = kwargs.get('sync_type', 'full')
        target_date = kwargs.get('target_date')
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        specific_codes = kwargs.get('specific_codes')
        execution_type = kwargs.get('execution_type', 'manual')
        
        # 同期実行
        history = await self.sync_daily_quotes(
            data_source_id=data_source_id,
            sync_type=sync_type,
            target_date=target_date,
            from_date=from_date,
            to_date=to_date,
            specific_codes=specific_codes,
            execution_type=execution_type
        )
        
        return {
            "status": history.status,
            "history_id": history.id,
            "total_records": history.total_records,
            "new_records": history.new_records,
            "updated_records": history.updated_records,
            "skipped_records": history.skipped_records
        }
    
    async def sync_daily_quotes(
        self,
        data_source_id: int,
        sync_type: str = "full",
        target_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        specific_codes: Optional[List[str]] = None,
        execution_type: str = "manual"
    ) -> DailyQuotesSyncHistory:
        """
        株価データの同期を実行
        
        Args:
            data_source_id: データソースID
            sync_type: 同期タイプ（full/incremental/single_stock）
            target_date: 対象日（incremental同期時）
            from_date: 期間指定開始日（full同期時）
            to_date: 期間指定終了日（full同期時）
            specific_codes: 特定銘柄コードリスト（single_stock同期時）
            execution_type: 実行タイプ（manual/scheduled）
            
        Returns:
            DailyQuotesSyncHistory: 同期履歴レコード
        """
        logger.info(f"Starting daily quotes sync: type={sync_type}, data_source_id={data_source_id}")
        
        # フェッチャーを初期化
        fetcher = self._initialize_fetcher(data_source_id)
        
        # 同期履歴レコードを作成
        sync_history = DailyQuotesSyncHistory(
            sync_date=target_date or date.today(),
            sync_type=sync_type,
            status="running",
            started_at=datetime.utcnow(),
            from_date=from_date,
            to_date=to_date,
            specific_codes=json.dumps(specific_codes) if specific_codes else None,
            execution_type=execution_type
        )
        
        async with async_session_maker() as session:
            # リポジトリを初期化
            repository = self._initialize_repository(session)
            
            try:
                session.add(sync_history)
                await session.commit()
                await session.refresh(sync_history)
                
                # 同期タイプに応じて処理を実行
                if sync_type == "full":
                    await self._sync_full_data(
                        fetcher, repository, sync_history, from_date, to_date
                    )
                elif sync_type == "incremental":
                    await self._sync_incremental_data(
                        fetcher, repository, sync_history, target_date
                    )
                elif sync_type == "single_stock":
                    await self._sync_single_stock_data(
                        fetcher, repository, sync_history, specific_codes, target_date
                    )
                else:
                    raise ValueError(f"Unknown sync_type: {sync_type}")
                
                # 成功時の処理
                sync_history.status = "completed"
                sync_history.completed_at = datetime.utcnow()
                await session.commit()
                
                logger.info(f"Daily quotes sync completed successfully: {sync_history.id}")
                return sync_history
                
            except Exception as e:
                # 統一されたエラーハンドリング
                error_info = await ErrorHandler.handle_sync_error(
                    error=e,
                    service_name="DailyQuotesSyncService",
                    context={
                        "sync_type": sync_type,
                        "data_source_id": data_source_id,
                        "target_date": target_date.isoformat() if target_date else None,
                        "from_date": from_date.isoformat() if from_date else None,
                        "to_date": to_date.isoformat() if to_date else None
                    },
                    db=session,
                    sync_history_id=sync_history.id
                )
                
                sync_history.status = "failed"
                sync_history.error_message = str(e)
                sync_history.completed_at = datetime.utcnow()
                await session.commit()
                raise
    
    async def _sync_full_data(
        self,
        fetcher: IDailyQuotesDataFetcher,
        repository: IDailyQuotesRepository,
        sync_history: DailyQuotesSyncHistory,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> None:
        """
        全データ同期を実行
        
        Args:
            fetcher: データ取得サービス
            repository: リポジトリサービス
            sync_history: 同期履歴
            from_date: 開始日
            to_date: 終了日
        """
        logger.info("Starting full data sync")
        
        # 日付範囲を設定（デフォルトは過去1年間）
        if not from_date:
            from_date = date.today() - timedelta(days=365)
        if not to_date:
            to_date = date.today() - timedelta(days=1)  # 前営業日まで
        
        logger.info(f"Syncing data from {from_date} to {to_date}")
        
        # 日付範囲のデータを取得
        try:
            quotes_by_date = await fetcher.fetch_quotes_by_date_range(
                from_date, to_date
            )
        except (DataFetchError, RateLimitError) as e:
            logger.error(f"Failed to fetch quotes: {e}")
            raise
        
        # 統計情報
        total_new = 0
        total_updated = 0
        total_skipped = 0
        
        # 各日付のデータを処理
        for current_date, quotes_data in quotes_by_date.items():
            try:
                # データをマッピング
                mapped_quotes = []
                for quote in quotes_data:
                    mapped = self.mapper.map_to_model(quote)
                    if mapped:
                        mapped_quotes.append(mapped)
                
                if mapped_quotes:
                    # 一括更新
                    new, updated, skipped = await repository.bulk_upsert(mapped_quotes)
                    total_new += new
                    total_updated += updated
                    total_skipped += skipped
                    
                    logger.info(
                        f"Processed {len(mapped_quotes)} quotes for {current_date}: "
                        f"new={new}, updated={updated}, skipped={skipped}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing data for {current_date}: {e}")
                # 個別日付のエラーは継続
        
        # 統計情報を更新
        sync_history.total_records = total_new + total_updated + total_skipped
        sync_history.new_records = total_new
        sync_history.updated_records = total_updated
        sync_history.skipped_records = total_skipped
        
        logger.info(
            f"Full sync completed: total={sync_history.total_records}, "
            f"new={total_new}, updated={total_updated}, skipped={total_skipped}"
        )
    
    async def _sync_incremental_data(
        self,
        fetcher: IDailyQuotesDataFetcher,
        repository: IDailyQuotesRepository,
        sync_history: DailyQuotesSyncHistory,
        target_date: Optional[date]
    ) -> None:
        """
        増分データ同期を実行
        
        Args:
            fetcher: データ取得サービス
            repository: リポジトリサービス
            sync_history: 同期履歴
            target_date: 対象日（デフォルトは前営業日）
        """
        logger.info("Starting incremental data sync")
        
        # 対象日を設定（デフォルトは前営業日）
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        logger.info(f"Syncing incremental data for date: {target_date}")
        
        # データを取得
        try:
            quotes_data = await fetcher.fetch_quotes_by_date(target_date)
        except (DataFetchError, RateLimitError) as e:
            logger.error(f"Failed to fetch quotes for {target_date}: {e}")
            raise
        
        if quotes_data:
            # データをマッピング
            mapped_quotes = []
            for quote in quotes_data:
                mapped = self.mapper.map_to_model(quote)
                if mapped:
                    mapped_quotes.append(mapped)
            
            if mapped_quotes:
                # 一括更新
                new, updated, skipped = await repository.bulk_upsert(mapped_quotes)
                
                # 統計情報を更新
                sync_history.total_records = new + updated + skipped
                sync_history.new_records = new
                sync_history.updated_records = updated
                sync_history.skipped_records = skipped
                
                logger.info(
                    f"Incremental sync completed: total={sync_history.total_records}, "
                    f"new={new}, updated={updated}, skipped={skipped}"
                )
        else:
            logger.info(f"No data available for {target_date}")
            sync_history.total_records = 0
    
    async def _sync_single_stock_data(
        self,
        fetcher: IDailyQuotesDataFetcher,
        repository: IDailyQuotesRepository,
        sync_history: DailyQuotesSyncHistory,
        specific_codes: Optional[List[str]],
        target_date: Optional[date]
    ) -> None:
        """
        特定銘柄のデータ同期を実行
        
        Args:
            fetcher: データ取得サービス
            repository: リポジトリサービス
            sync_history: 同期履歴
            specific_codes: 対象銘柄コードリスト
            target_date: 対象日
        """
        if not specific_codes:
            raise ValueError("specific_codes is required for single_stock sync")
        
        logger.info(f"Starting single stock sync for codes: {specific_codes}")
        
        # 対象日を設定
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        # データを取得
        try:
            quotes_data = await fetcher.fetch_quotes_by_date(target_date, specific_codes)
        except (DataFetchError, RateLimitError) as e:
            logger.error(f"Failed to fetch quotes for specific codes: {e}")
            raise
        
        if quotes_data:
            # データをマッピング
            mapped_quotes = []
            for quote in quotes_data:
                mapped = self.mapper.map_to_model(quote)
                if mapped:
                    mapped_quotes.append(mapped)
            
            if mapped_quotes:
                # 一括更新
                new, updated, skipped = await repository.bulk_upsert(mapped_quotes)
                
                # 統計情報を更新
                sync_history.target_companies = len(specific_codes)
                sync_history.total_records = new + updated + skipped
                sync_history.new_records = new
                sync_history.updated_records = updated
                sync_history.skipped_records = skipped
                
                logger.info(
                    f"Single stock sync completed: total={sync_history.total_records}, "
                    f"new={new}, updated={updated}, skipped={skipped}"
                )
        else:
            logger.info("No data retrieved for specified codes")
            sync_history.total_records = 0
    
    async def get_sync_history(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[DailyQuotesSyncHistory]:
        """
        同期履歴を取得
        
        Args:
            limit: 取得件数
            offset: オフセット
            status: ステータスフィルタ
            
        Returns:
            List[DailyQuotesSyncHistory]: 同期履歴リスト
        """
        # 基底クラスのメソッドが使える場合は使用
        if self._has_db and hasattr(super(), 'get_sync_history'):
            return await super().get_sync_history(limit, offset, status)
        
        # そうでない場合は独自実装
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            stmt = select(DailyQuotesSyncHistory).order_by(
                DailyQuotesSyncHistory.started_at.desc()
            )
            
            if status:
                stmt = stmt.where(DailyQuotesSyncHistory.status == status)
            
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            histories = result.scalars().all()
        return histories
    
    async def get_sync_status(self, sync_id: int) -> Optional[DailyQuotesSyncHistory]:
        """
        特定の同期履歴を取得
        
        Args:
            sync_id: 同期履歴ID
            
        Returns:
            Optional[DailyQuotesSyncHistory]: 同期履歴（見つからない場合はNone）
        """
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(DailyQuotesSyncHistory).where(
                    DailyQuotesSyncHistory.id == sync_id
                )
            )
            sync_history = result.scalar_one_or_none()
        return sync_history