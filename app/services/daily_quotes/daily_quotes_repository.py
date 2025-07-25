"""
日次株価データリポジトリ実装

データベース操作を担当するリポジトリクラス
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, func
from sqlalchemy.dialects.postgresql import insert

from app.models.daily_quote import DailyQuote
from app.models.company import Company
from app.services.interfaces.daily_quotes_sync_interfaces import IDailyQuotesRepository
from app.core.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DailyQuotesRepository(IDailyQuotesRepository):
    """日次株価データリポジトリ"""
    
    def __init__(self, db: AsyncSession):
        """
        初期化
        
        Args:
            db: データベースセッション
        """
        self.db = db
        self._company_cache: Optional[Dict[str, bool]] = None
        self._batch_counter = 0
        
    async def find_by_code_and_date(
        self, 
        code: str, 
        trade_date: date
    ) -> Optional[DailyQuote]:
        """
        銘柄コードと日付で検索
        
        Args:
            code: 銘柄コード
            trade_date: 取引日
            
        Returns:
            Optional[DailyQuote]: 株価データ（見つからない場合はNone）
        """
        stmt = select(DailyQuote).where(
            and_(
                DailyQuote.code == code,
                DailyQuote.trade_date == trade_date
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def bulk_upsert(
        self, 
        quotes_data: List[Dict[str, Any]]
    ) -> Tuple[int, int, int]:
        """
        一括更新
        
        Args:
            quotes_data: 株価データのリスト
            
        Returns:
            Tuple[int, int, int]: (新規件数, 更新件数, スキップ件数)
        """
        new_count = 0
        updated_count = 0
        skipped_count = 0
        
        # 企業存在確認用のキャッシュを初期化
        if self._company_cache is None:
            await self._load_company_cache()
        
        for quote_data in quotes_data:
            try:
                # 企業存在確認
                code = quote_data.get("code")
                if not self._company_cache.get(code, False):
                    logger.warning(f"Company code {code} not found in master data, skipping")
                    skipped_count += 1
                    continue
                
                # 既存レコードの確認
                existing = await self.find_by_code_and_date(
                    code=code,
                    trade_date=quote_data["trade_date"]
                )
                
                if existing:
                    # 更新
                    await self._update_quote(existing, quote_data)
                    updated_count += 1
                else:
                    # 新規作成
                    await self._create_quote(quote_data)
                    new_count += 1
                
                # バッチコミット（100件ごと）
                self._batch_counter += 1
                if self._batch_counter >= 100:
                    await self.commit_batch()
                    self._batch_counter = 0
                    
            except Exception as e:
                logger.error(f"Error processing quote data: {e}")
                skipped_count += 1
        
        # 最終コミット
        if self._batch_counter > 0:
            await self.commit_batch()
            self._batch_counter = 0
        
        return new_count, updated_count, skipped_count
    
    async def find_latest_date_by_code(self, code: str) -> Optional[date]:
        """
        銘柄の最新取引日を取得
        
        Args:
            code: 銘柄コード
            
        Returns:
            Optional[date]: 最新取引日（データがない場合はNone）
        """
        stmt = select(func.max(DailyQuote.trade_date)).where(
            DailyQuote.code == code
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def check_company_exists(self, code: str) -> bool:
        """
        企業マスタに存在するか確認
        
        Args:
            code: 銘柄コード
            
        Returns:
            bool: 存在する場合True
        """
        if self._company_cache is not None:
            return self._company_cache.get(code, False)
        
        stmt = select(Company.code).where(
            and_(
                Company.code == code,
                Company.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def get_active_company_codes(self) -> List[str]:
        """
        アクティブな企業コードリストを取得
        
        Returns:
            List[str]: アクティブな企業の銘柄コードリスト
        """
        stmt = select(Company.code).where(Company.is_active == True)
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]
    
    async def commit_batch(self) -> None:
        """バッチコミット"""
        await self.db.commit()
        logger.debug("Batch committed")
    
    async def rollback(self) -> None:
        """ロールバック"""
        await self.db.rollback()
        logger.debug("Transaction rolled back")
    
    async def _load_company_cache(self) -> None:
        """企業マスタをキャッシュにロード"""
        codes = await self.get_active_company_codes()
        self._company_cache = {code: True for code in codes}
        logger.info(f"Loaded {len(self._company_cache)} active companies to cache")
    
    async def _create_quote(self, quote_data: Dict[str, Any]) -> None:
        """
        株価データを新規作成
        
        Args:
            quote_data: 株価データ
        """
        quote = DailyQuote(**quote_data)
        self.db.add(quote)
    
    async def _update_quote(
        self, 
        existing: DailyQuote, 
        quote_data: Dict[str, Any]
    ) -> None:
        """
        既存の株価データを更新
        
        Args:
            existing: 既存のエンティティ
            quote_data: 更新データ
        """
        # 更新対象フィールドのみ更新
        update_fields = [
            "open_price", "high_price", "low_price", "close_price",
            "volume", "turnover_value",
            "adjustment_factor", "adjustment_open", "adjustment_high",
            "adjustment_low", "adjustment_close", "adjustment_volume",
            "upper_limit_flag", "lower_limit_flag",
            "morning_open", "morning_high", "morning_low", "morning_close",
            "morning_volume", "morning_turnover_value",
            "afternoon_open", "afternoon_high", "afternoon_low", "afternoon_close",
            "afternoon_volume", "afternoon_turnover_value"
        ]
        
        for field in update_fields:
            if field in quote_data:
                setattr(existing, field, quote_data[field])
    
    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._company_cache = None