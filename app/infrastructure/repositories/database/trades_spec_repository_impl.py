"""投資部門別売買状況リポジトリ実装"""
from datetime import date
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.domain.entities.trades_spec import TradesSpec
from app.domain.repositories.trades_spec_repository import TradesSpecRepository
from app.infrastructure.database.models.trades_spec import TradesSpecModel

logger = get_logger()


class TradesSpecRepositoryImpl(TradesSpecRepository):
    """投資部門別売買状況リポジトリの実装"""
    
    def __init__(self, session: AsyncSession) -> None:
        """リポジトリを初期化
        
        Args:
            session: AsyncSession インスタンス
        """
        self._session = session
    
    async def save(self, trades_spec: TradesSpec) -> None:
        """投資部門別売買状況を保存する"""
        model = self._to_model(trades_spec)
        
        # UPSERT 処理
        stmt = insert(TradesSpecModel).values(
            code=model.code,
            trade_date=model.trade_date,
            section=model.section,
            sales_proprietary=model.sales_proprietary,
            purchases_proprietary=model.purchases_proprietary,
            balance_proprietary=model.balance_proprietary,
            sales_consignment_individual=model.sales_consignment_individual,
            purchases_consignment_individual=model.purchases_consignment_individual,
            balance_consignment_individual=model.balance_consignment_individual,
            sales_consignment_corporate=model.sales_consignment_corporate,
            purchases_consignment_corporate=model.purchases_consignment_corporate,
            balance_consignment_corporate=model.balance_consignment_corporate,
            sales_consignment_investment_trust=model.sales_consignment_investment_trust,
            purchases_consignment_investment_trust=model.purchases_consignment_investment_trust,
            balance_consignment_investment_trust=model.balance_consignment_investment_trust,
            sales_consignment_foreign=model.sales_consignment_foreign,
            purchases_consignment_foreign=model.purchases_consignment_foreign,
            balance_consignment_foreign=model.balance_consignment_foreign,
            sales_consignment_other_corporate=model.sales_consignment_other_corporate,
            purchases_consignment_other_corporate=model.purchases_consignment_other_corporate,
            balance_consignment_other_corporate=model.balance_consignment_other_corporate,
            sales_consignment_other=model.sales_consignment_other,
            purchases_consignment_other=model.purchases_consignment_other,
            balance_consignment_other=model.balance_consignment_other,
            sales_total=model.sales_total,
            purchases_total=model.purchases_total,
            balance_total=model.balance_total,
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=["code", "trade_date"],
            set_={
                "section": stmt.excluded.section,
                "sales_proprietary": stmt.excluded.sales_proprietary,
                "purchases_proprietary": stmt.excluded.purchases_proprietary,
                "balance_proprietary": stmt.excluded.balance_proprietary,
                "sales_consignment_individual": stmt.excluded.sales_consignment_individual,
                "purchases_consignment_individual": stmt.excluded.purchases_consignment_individual,
                "balance_consignment_individual": stmt.excluded.balance_consignment_individual,
                "sales_consignment_corporate": stmt.excluded.sales_consignment_corporate,
                "purchases_consignment_corporate": stmt.excluded.purchases_consignment_corporate,
                "balance_consignment_corporate": stmt.excluded.balance_consignment_corporate,
                "sales_consignment_investment_trust": stmt.excluded.sales_consignment_investment_trust,
                "purchases_consignment_investment_trust": stmt.excluded.purchases_consignment_investment_trust,
                "balance_consignment_investment_trust": stmt.excluded.balance_consignment_investment_trust,
                "sales_consignment_foreign": stmt.excluded.sales_consignment_foreign,
                "purchases_consignment_foreign": stmt.excluded.purchases_consignment_foreign,
                "balance_consignment_foreign": stmt.excluded.balance_consignment_foreign,
                "sales_consignment_other_corporate": stmt.excluded.sales_consignment_other_corporate,
                "purchases_consignment_other_corporate": stmt.excluded.purchases_consignment_other_corporate,
                "balance_consignment_other_corporate": stmt.excluded.balance_consignment_other_corporate,
                "sales_consignment_other": stmt.excluded.sales_consignment_other,
                "purchases_consignment_other": stmt.excluded.purchases_consignment_other,
                "balance_consignment_other": stmt.excluded.balance_consignment_other,
                "sales_total": stmt.excluded.sales_total,
                "purchases_total": stmt.excluded.purchases_total,
                "balance_total": stmt.excluded.balance_total,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        
        await self._session.execute(stmt)
        await self._session.flush()
    
    async def save_bulk(self, trades_specs: List[TradesSpec]) -> None:
        """複数の投資部門別売買状況を一括保存する"""
        if not trades_specs:
            return
        
        # エンティティをモデルに変換
        models = [self._to_model(spec) for spec in trades_specs]
        
        # バルク UPSERT 用のデータ準備
        values = []
        for model in models:
            values.append({
                "code": model.code,
                "trade_date": model.trade_date,
                "section": model.section,
                "sales_proprietary": model.sales_proprietary,
                "purchases_proprietary": model.purchases_proprietary,
                "balance_proprietary": model.balance_proprietary,
                "sales_consignment_individual": model.sales_consignment_individual,
                "purchases_consignment_individual": model.purchases_consignment_individual,
                "balance_consignment_individual": model.balance_consignment_individual,
                "sales_consignment_corporate": model.sales_consignment_corporate,
                "purchases_consignment_corporate": model.purchases_consignment_corporate,
                "balance_consignment_corporate": model.balance_consignment_corporate,
                "sales_consignment_investment_trust": model.sales_consignment_investment_trust,
                "purchases_consignment_investment_trust": model.purchases_consignment_investment_trust,
                "balance_consignment_investment_trust": model.balance_consignment_investment_trust,
                "sales_consignment_foreign": model.sales_consignment_foreign,
                "purchases_consignment_foreign": model.purchases_consignment_foreign,
                "balance_consignment_foreign": model.balance_consignment_foreign,
                "sales_consignment_other_corporate": model.sales_consignment_other_corporate,
                "purchases_consignment_other_corporate": model.purchases_consignment_other_corporate,
                "balance_consignment_other_corporate": model.balance_consignment_other_corporate,
                "sales_consignment_other": model.sales_consignment_other,
                "purchases_consignment_other": model.purchases_consignment_other,
                "balance_consignment_other": model.balance_consignment_other,
                "sales_total": model.sales_total,
                "purchases_total": model.purchases_total,
                "balance_total": model.balance_total,
            })
        
        # PostgreSQL の ON CONFLICT を使用した UPSERT
        stmt = insert(TradesSpecModel).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["code", "trade_date"],
            set_={
                "section": stmt.excluded.section,
                "sales_proprietary": stmt.excluded.sales_proprietary,
                "purchases_proprietary": stmt.excluded.purchases_proprietary,
                "balance_proprietary": stmt.excluded.balance_proprietary,
                "sales_consignment_individual": stmt.excluded.sales_consignment_individual,
                "purchases_consignment_individual": stmt.excluded.purchases_consignment_individual,
                "balance_consignment_individual": stmt.excluded.balance_consignment_individual,
                "sales_consignment_corporate": stmt.excluded.sales_consignment_corporate,
                "purchases_consignment_corporate": stmt.excluded.purchases_consignment_corporate,
                "balance_consignment_corporate": stmt.excluded.balance_consignment_corporate,
                "sales_consignment_investment_trust": stmt.excluded.sales_consignment_investment_trust,
                "purchases_consignment_investment_trust": stmt.excluded.purchases_consignment_investment_trust,
                "balance_consignment_investment_trust": stmt.excluded.balance_consignment_investment_trust,
                "sales_consignment_foreign": stmt.excluded.sales_consignment_foreign,
                "purchases_consignment_foreign": stmt.excluded.purchases_consignment_foreign,
                "balance_consignment_foreign": stmt.excluded.balance_consignment_foreign,
                "sales_consignment_other_corporate": stmt.excluded.sales_consignment_other_corporate,
                "purchases_consignment_other_corporate": stmt.excluded.purchases_consignment_other_corporate,
                "balance_consignment_other_corporate": stmt.excluded.balance_consignment_other_corporate,
                "sales_consignment_other": stmt.excluded.sales_consignment_other,
                "purchases_consignment_other": stmt.excluded.purchases_consignment_other,
                "balance_consignment_other": stmt.excluded.balance_consignment_other,
                "sales_total": stmt.excluded.sales_total,
                "purchases_total": stmt.excluded.purchases_total,
                "balance_total": stmt.excluded.balance_total,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        
        await self._session.execute(stmt)
        await self._session.flush()
        
        logger.info(f"Saved {len(trades_specs)} trades_spec records")
    
    async def find_by_code_and_date(self, code: str, trade_date: date) -> Optional[TradesSpec]:
        """銘柄コードと日付で投資部門別売買状況を検索する"""
        result = await self._session.execute(
            select(TradesSpecModel).where(
                TradesSpecModel.code == code,
                TradesSpecModel.trade_date == trade_date,
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            return self._to_entity(model)
        return None
    
    async def find_by_code_and_date_range(
        self,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[TradesSpec]:
        """銘柄コードと日付範囲で投資部門別売買状況を検索する"""
        result = await self._session.execute(
            select(TradesSpecModel)
            .where(
                TradesSpecModel.code == code,
                TradesSpecModel.trade_date >= start_date,
                TradesSpecModel.trade_date <= end_date,
            )
            .order_by(TradesSpecModel.trade_date)
        )
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]
    
    async def find_by_date_and_section(
        self,
        trade_date: date,
        section: Optional[str] = None
    ) -> List[TradesSpec]:
        """日付と市場区分で投資部門別売買状況を検索する"""
        query = select(TradesSpecModel).where(TradesSpecModel.trade_date == trade_date)
        
        if section:
            query = query.where(TradesSpecModel.section == section)
            
        query = query.order_by(TradesSpecModel.code)
        
        result = await self._session.execute(query)
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]
    
    async def find_by_date_range_and_section(
        self,
        start_date: date,
        end_date: date,
        section: Optional[str] = None
    ) -> List[TradesSpec]:
        """日付範囲と市場区分で投資部門別売買状況を検索する"""
        query = select(TradesSpecModel).where(
            TradesSpecModel.trade_date >= start_date,
            TradesSpecModel.trade_date <= end_date,
        )
        
        if section:
            query = query.where(TradesSpecModel.section == section)
            
        query = query.order_by(TradesSpecModel.trade_date, TradesSpecModel.code)
        
        result = await self._session.execute(query)
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]
    
    async def delete_by_date_range(self, start_date: date, end_date: date) -> int:
        """日付範囲で投資部門別売買状況を削除する"""
        result = await self._session.execute(
            delete(TradesSpecModel).where(
                TradesSpecModel.trade_date >= start_date,
                TradesSpecModel.trade_date <= end_date,
            )
        )
        await self._session.flush()
        
        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} records for date range {start_date} to {end_date}")
        return deleted_count
    
    def _to_entity(self, model: TradesSpecModel) -> TradesSpec:
        """モデルをエンティティに変換
        
        Args:
            model: TradesSpecModel
            
        Returns:
            TradesSpec エンティティ
        """
        return TradesSpec(
            code=model.code,
            trade_date=model.trade_date,
            section=model.section,
            sales_proprietary=model.sales_proprietary,
            purchases_proprietary=model.purchases_proprietary,
            balance_proprietary=model.balance_proprietary,
            sales_consignment_individual=model.sales_consignment_individual,
            purchases_consignment_individual=model.purchases_consignment_individual,
            balance_consignment_individual=model.balance_consignment_individual,
            sales_consignment_corporate=model.sales_consignment_corporate,
            purchases_consignment_corporate=model.purchases_consignment_corporate,
            balance_consignment_corporate=model.balance_consignment_corporate,
            sales_consignment_investment_trust=model.sales_consignment_investment_trust,
            purchases_consignment_investment_trust=model.purchases_consignment_investment_trust,
            balance_consignment_investment_trust=model.balance_consignment_investment_trust,
            sales_consignment_foreign=model.sales_consignment_foreign,
            purchases_consignment_foreign=model.purchases_consignment_foreign,
            balance_consignment_foreign=model.balance_consignment_foreign,
            sales_consignment_other_corporate=model.sales_consignment_other_corporate,
            purchases_consignment_other_corporate=model.purchases_consignment_other_corporate,
            balance_consignment_other_corporate=model.balance_consignment_other_corporate,
            sales_consignment_other=model.sales_consignment_other,
            purchases_consignment_other=model.purchases_consignment_other,
            balance_consignment_other=model.balance_consignment_other,
            sales_total=model.sales_total,
            purchases_total=model.purchases_total,
            balance_total=model.balance_total,
        )
    
    def _to_model(self, entity: TradesSpec) -> TradesSpecModel:
        """エンティティをモデルに変換
        
        Args:
            entity: TradesSpec エンティティ
            
        Returns:
            TradesSpecModel
        """
        return TradesSpecModel(
            code=entity.code,
            trade_date=entity.trade_date,
            section=entity.section,
            sales_proprietary=entity.sales_proprietary,
            purchases_proprietary=entity.purchases_proprietary,
            balance_proprietary=entity.balance_proprietary,
            sales_consignment_individual=entity.sales_consignment_individual,
            purchases_consignment_individual=entity.purchases_consignment_individual,
            balance_consignment_individual=entity.balance_consignment_individual,
            sales_consignment_corporate=entity.sales_consignment_corporate,
            purchases_consignment_corporate=entity.purchases_consignment_corporate,
            balance_consignment_corporate=entity.balance_consignment_corporate,
            sales_consignment_investment_trust=entity.sales_consignment_investment_trust,
            purchases_consignment_investment_trust=entity.purchases_consignment_investment_trust,
            balance_consignment_investment_trust=entity.balance_consignment_investment_trust,
            sales_consignment_foreign=entity.sales_consignment_foreign,
            purchases_consignment_foreign=entity.purchases_consignment_foreign,
            balance_consignment_foreign=entity.balance_consignment_foreign,
            sales_consignment_other_corporate=entity.sales_consignment_other_corporate,
            purchases_consignment_other_corporate=entity.purchases_consignment_other_corporate,
            balance_consignment_other_corporate=entity.balance_consignment_other_corporate,
            sales_consignment_other=entity.sales_consignment_other,
            purchases_consignment_other=entity.purchases_consignment_other,
            balance_consignment_other=entity.balance_consignment_other,
            sales_total=entity.sales_total,
            purchases_total=entity.purchases_total,
            balance_total=entity.balance_total,
        )