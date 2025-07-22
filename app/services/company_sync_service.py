"""
企業データ同期サービス

J-Quants APIから上場企業データを取得してデータベースに同期するサービス
"""

import logging
from datetime import datetime, date
import datetime as dt
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.company import (
    Company, 
    CompanySyncHistory, 
    Sector17Master, 
    Sector33Master, 
    MarketMaster
)
from app.services.jquants_client import JQuantsClientManager
from app.services.data_source_service import DataSourceService
from app.services.base_sync_service import BaseSyncService
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
        jquants_client_manager: JQuantsClientManager
    ):
        """
        初期化
        
        Args:
            db: データベースセッション
            data_source_service: データソースサービス
            jquants_client_manager: J-Quantsクライアント管理
        """
        super().__init__(db)
        self.data_source_service = data_source_service
        self.jquants_client_manager = jquants_client_manager
    
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
            
        Returns:
            CompanySyncHistory: 同期履歴
        """
        if sync_date is None:
            sync_date = dt.date.today()
        
        logger.info(f"Starting company sync for type: {sync_type}")
        
        # 同期履歴を作成（基底クラスのメソッドを使用）
        sync_history = await self.create_sync_history(
            sync_type=sync_type,
            sync_date=sync_date,
            execution_type=execution_type
        )
        
        try:
            # J-Quants APIから企業データを取得
            try:
                client = await self.jquants_client_manager.get_client(data_source_id)
            except Exception as e:
                raise DataSourceNotFoundError(data_source_id)
            
            try:
                companies_data = await client.get_all_listed_companies()
            except Exception as e:
                if "401" in str(e) or "authentication" in str(e).lower():
                    raise APIError(
                        "J-Quants API authentication failed",
                        status_code=401,
                        details={"data_source_id": data_source_id}
                    )
                elif "429" in str(e) or "rate limit" in str(e).lower():
                    raise APIError(
                        "J-Quants API rate limit exceeded",
                        status_code=429,
                        details={"data_source_id": data_source_id}
                    )
                else:
                    raise APIError(
                        f"Failed to fetch companies from J-Quants API: {str(e)}",
                        details={"data_source_id": data_source_id}
                    )
            
            if not companies_data:
                raise DataValidationError(
                    "No company data received from J-Quants API",
                    field="companies_data",
                    value=None
                )
            
            logger.info(f"Retrieved {len(companies_data)} companies from J-Quants API")
            
            # データベースに保存
            stats = await self._save_companies_data(companies_data)
            
            # 同期履歴を更新（基底クラスのメソッドを使用）
            sync_history = await self.update_sync_history_success(
                sync_history,
                total_companies=len(companies_data),
                new_companies=stats["new_count"],
                updated_companies=stats["updated_count"],
                deleted_companies=stats.get("deleted_count", 0)
            )
            
            logger.info(f"Company sync completed successfully. New: {stats['new_count']}, Updated: {stats['updated_count']}")
            return sync_history
            
        except Exception as e:
            # 統一されたエラーハンドリング
            error_info = await ErrorHandler.handle_sync_error(
                error=e,
                service_name="CompanySyncService",
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
            
            raise
    
    async def _save_companies_data(
        self, 
        companies_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        企業データをデータベースに保存
        
        Args:
            companies_data: J-Quants APIから取得した企業データ
            
        Returns:
            Dict[str, int]: 保存統計（new_count, updated_count）
        """
        new_count = 0
        updated_count = 0
        
        for company_data in companies_data:
            try:
                # データのマッピングと検証
                mapped_data = self._map_jquants_data_to_model(company_data)
                
                if not mapped_data:
                    logger.warning(f"Skipping invalid company data: {company_data}")
                    continue
                
                # 既存データをチェック
                existing_company = await self._get_existing_company(mapped_data["code"])
                
                if existing_company:
                    # 既存データを更新
                    await self._update_company(existing_company, mapped_data)
                    updated_count += 1
                else:
                    # 新規データを作成
                    await self._create_company(mapped_data)
                    new_count += 1
                    
            except DataValidationError as e:
                # データ検証エラーは警告レベルでログ出力し、処理を続行
                logger.warning(f"Data validation error for company {company_data.get('Code', 'unknown')}: {e}")
                continue
            except Exception as e:
                # その他のエラーはエラーレベルでログ出力
                await ErrorHandler.handle_sync_error(
                    error=e,
                    service_name="CompanySyncService",
                    context={
                        "company_code": company_data.get('Code', 'unknown'),
                        "operation": "save_company_data"
                    }
                )
                continue
        
        # 変更をコミット
        await self.db.commit()
        
        return {
            "new_count": new_count,
            "updated_count": updated_count
        }
    
    def _map_jquants_data_to_model(
        self, 
        jquants_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        J-Quants APIのデータをCompanyモデル用にマッピング
        
        Args:
            jquants_data: J-Quants APIのレスポンスデータ
            
        Returns:
            Optional[Dict[str, Any]]: マッピングされたデータ（無効な場合はNone）
        """
        try:
            # 必須フィールドのチェック
            code = jquants_data.get("Code")
            company_name = jquants_data.get("CompanyName")
            
            if not code:
                raise DataValidationError(
                    "Missing required field: Code",
                    field="Code",
                    value=None,
                    details={"company_data": jquants_data}
                )
            
            if not company_name:
                raise DataValidationError(
                    "Missing required field: CompanyName",
                    field="CompanyName",
                    value=None,
                    details={"company_data": jquants_data}
                )
            
            return {
                "code": str(code),
                "company_name": str(company_name),
                "company_name_english": jquants_data.get("CompanyNameEnglish"),
                "sector17_code": jquants_data.get("Sector17Code"),
                "sector33_code": jquants_data.get("Sector33Code"),
                "scale_category": jquants_data.get("ScaleCategory"),
                "market_code": jquants_data.get("MarketCode"),
                "margin_code": jquants_data.get("MarginCode"),
                "is_active": True
            }
        except Exception as e:
            logger.error(f"Error mapping J-Quants data: {e}")
            return None
    
    async def _get_existing_company(
        self, 
        code: str
    ) -> Optional[Company]:
        """
        既存の企業データを取得
        
        Args:
            code: 銘柄コード
            
        Returns:
            Optional[Company]: 既存企業データ（見つからない場合はNone）
        """
        result = await self.db.execute(
            select(Company).where(Company.code == code)
        )
        return result.scalar_one_or_none()
    
    async def _create_company(self, company_data: Dict[str, Any]):
        """
        新しい企業データを作成
        
        Args:
            company_data: 企業データ
        """
        company = Company(**company_data)
        self.db.add(company)
        logger.debug(f"Created new company: {company_data['code']} - {company_data['company_name']}")
    
    async def _update_company(
        self, 
        existing_company: Company, 
        new_data: Dict[str, Any]
    ):
        """
        既存の企業データを更新
        
        Args:
            existing_company: 既存の企業データ
            new_data: 新しいデータ
        """
        # 更新が必要なフィールドをチェック
        updated_fields = []
        
        for field, new_value in new_data.items():
            if field in ["code"]:  # 主キー的フィールドはスキップ
                continue
                
            current_value = getattr(existing_company, field)
            if current_value != new_value:
                setattr(existing_company, field, new_value)
                updated_fields.append(field)
        
        if updated_fields:
            existing_company.updated_at = datetime.utcnow()
            logger.debug(f"Updated company {existing_company.code}: {updated_fields}")
    
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
        # 基底クラスのメソッドを使用して履歴を取得
        histories = await self.get_sync_history(limit, offset, status)
        
        # 総件数を取得
        query = select(CompanySyncHistory)
        if status:
            query = query.where(CompanySyncHistory.status == status)
        count_result = await self.db.execute(
            select(CompanySyncHistory.id).select_from(query.subquery())
        )
        total = len(count_result.scalars().all())
        
        return histories, total
    
    async def deactivate_missing_companies(self, active_codes: List[str]) -> int:
        """
        J-Quants APIに存在しない企業を非アクティブ化
        
        Args:
            active_codes: アクティブな銘柄コードのリスト
            
        Returns:
            int: 非アクティブ化した企業数
        """
        if not active_codes:
            return 0
        
        # アクティブコードリストに含まれない企業を非アクティブ化
        result = await self.db.execute(
            update(Company)
            .where(
                and_(
                    Company.is_active == True,
                    ~Company.code.in_(active_codes)
                )
            )
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        
        deactivated_count = result.rowcount
        await self.db.commit()
        
        if deactivated_count > 0:
            logger.info(f"Deactivated {deactivated_count} companies not found in J-Quants API")
        
        return deactivated_count
    
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
            
            client = await self.jquants_client_manager.get_client(data_source.id)
            
            # 1. J-Quantsから全銘柄取得
            companies_data = await client.get_all_listed_companies()
            
            if not companies_data:
                raise Exception("No company data received from J-Quants API")
            
            logger.info(f"Retrieved {len(companies_data)} companies from J-Quants API")
            
            # 2. 既存の全企業を非アクティブ化
            await self.db.execute(
                update(Company).values(is_active=False)
            )
            
            # 3. 取得データを一括更新（upsert）
            sync_count = 0
            for company_data in companies_data:
                await self._upsert_company_simple(company_data)
                sync_count += 1
            
            await self.db.commit()
            
            # 4. 実行結果を返す
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "success",
                "sync_count": sync_count,
                "duration": duration,
                "executed_at": start_time
            }
            
        except Exception as e:
            await self.db.rollback()
            # エラーハンドリング（基底クラスのメソッドを使用）
            self.handle_error(e, {
                "method": "sync_all_companies_simple",
                "start_time": start_time
            })
            return {
                "status": "failed",
                "error": str(e),
                "executed_at": start_time
            }
    
    async def _upsert_company_simple(self, company_data: Dict):
        """
        企業情報をupsert（シンプル版）
        
        Args:
            company_data: J-Quants APIから取得した企業データ
        """
        stmt = pg_insert(Company).values(
            code=company_data["Code"],
            company_name=company_data["CompanyName"],
            company_name_english=company_data.get("CompanyNameEnglish"),
            sector17_code=company_data.get("Sector17Code"),
            sector33_code=company_data.get("Sector33Code"),
            scale_category=company_data.get("ScaleCategory"),
            market_code=company_data.get("MarketCode"),
            margin_code=company_data.get("MarginCode"),
            is_active=True
        ).on_conflict_do_update(
            index_elements=["code"],
            set_={
                "company_name": company_data["CompanyName"],
                "company_name_english": company_data.get("CompanyNameEnglish"),
                "sector17_code": company_data.get("Sector17Code"),
                "sector33_code": company_data.get("Sector33Code"),
                "scale_category": company_data.get("ScaleCategory"),
                "market_code": company_data.get("MarketCode"),
                "margin_code": company_data.get("MarginCode"),
                "is_active": True,
                "updated_at": datetime.utcnow()
            }
        )
        await self.db.execute(stmt)