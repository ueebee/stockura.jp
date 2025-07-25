"""
企業データリポジトリ

データベース操作を抽象化し、企業データの永続化を担当
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.services.interfaces.company_sync_interfaces import ICompanyRepository, RepositoryError
from app.models.company import Company

logger = logging.getLogger(__name__)


class CompanyRepository(ICompanyRepository):
    """企業データリポジトリの実装"""
    
    def __init__(self, db: AsyncSession):
        """
        初期化
        
        Args:
            db: データベースセッション
        """
        self.db = db
    
    async def find_by_code(self, code: str) -> Optional[Company]:
        """
        銘柄コードで企業を検索
        
        Args:
            code: 銘柄コード
            
        Returns:
            Optional[Company]: 企業エンティティ（見つからない場合はNone）
        """
        try:
            result = await self.db.execute(
                select(Company).where(Company.code == code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding company by code {code}: {e}")
            raise RepositoryError(f"Failed to find company by code: {str(e)}")
    
    async def find_all_active(self) -> List[Company]:
        """
        全てのアクティブな企業を取得
        
        Returns:
            List[Company]: アクティブな企業のリスト
        """
        try:
            result = await self.db.execute(
                select(Company).where(Company.is_active == True)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error finding active companies: {e}")
            raise RepositoryError(f"Failed to find active companies: {str(e)}")
    
    async def save(self, company_data: Dict[str, Any]) -> Company:
        """
        企業データを保存
        
        Args:
            company_data: 保存する企業データ
            
        Returns:
            Company: 保存された企業エンティティ
        """
        try:
            company = Company(**company_data)
            self.db.add(company)
            await self.db.flush()  # IDを取得するためflush
            logger.debug(f"Saved new company: {company.code} - {company.company_name}")
            return company
        except Exception as e:
            logger.error(f"Error saving company: {e}")
            raise RepositoryError(f"Failed to save company: {str(e)}")
    
    async def update(self, company: Company, update_data: Dict[str, Any]) -> Company:
        """
        企業データを更新
        
        Args:
            company: 更新対象の企業エンティティ
            update_data: 更新データ
            
        Returns:
            Company: 更新された企業エンティティ
        """
        try:
            # 更新可能なフィールドのみ更新
            updated_fields = []
            for field, value in update_data.items():
                if field == "code":  # 主キー的フィールドはスキップ
                    continue
                if hasattr(company, field):
                    current_value = getattr(company, field)
                    if current_value != value:
                        setattr(company, field, value)
                        updated_fields.append(field)
            
            if updated_fields:
                company.updated_at = datetime.utcnow()
                await self.db.flush()
                logger.debug(f"Updated company {company.code}: {updated_fields}")
            
            return company
        except Exception as e:
            logger.error(f"Error updating company {company.code}: {e}")
            raise RepositoryError(f"Failed to update company: {str(e)}")
    
    async def bulk_upsert(self, companies_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        企業データを一括更新
        
        Args:
            companies_data: 企業データのリスト
            
        Returns:
            Dict[str, int]: 処理結果統計 {"new_count": n, "updated_count": m}
        """
        if not companies_data:
            return {"new_count": 0, "updated_count": 0}
        
        try:
            # 既存企業のコードを取得
            existing_codes_result = await self.db.execute(
                select(Company.code)
            )
            existing_codes = set(existing_codes_result.scalars().all())
            
            new_count = 0
            updated_count = 0
            
            # バッチサイズを定義（大量データの場合のメモリ効率化）
            batch_size = 100
            
            for i in range(0, len(companies_data), batch_size):
                batch = companies_data[i:i + batch_size]
                
                for company_data in batch:
                    code = company_data.get("code")
                    if not code:
                        logger.warning(f"Skipping company data without code: {company_data}")
                        continue
                    
                    # PostgreSQLのUPSERT機能を使用
                    stmt = pg_insert(Company).values(**company_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["code"],
                        set_={
                            **{k: v for k, v in company_data.items() if k != "code"},
                            "updated_at": datetime.utcnow()
                        }
                    )
                    await self.db.execute(stmt)
                    
                    # 統計カウント
                    if code in existing_codes:
                        updated_count += 1
                    else:
                        new_count += 1
                        existing_codes.add(code)
                
                # バッチごとにflush
                await self.db.flush()
            
            logger.info(f"Bulk upsert completed: {new_count} new, {updated_count} updated")
            return {"new_count": new_count, "updated_count": updated_count}
            
        except Exception as e:
            logger.error(f"Error in bulk upsert: {e}")
            raise RepositoryError(f"Failed to bulk upsert companies: {str(e)}")
    
    async def deactivate_companies(self, exclude_codes: List[str]) -> int:
        """
        指定コード以外の企業を非アクティブ化
        
        Args:
            exclude_codes: 除外する銘柄コードのリスト
            
        Returns:
            int: 非アクティブ化した企業数
        """
        try:
            if not exclude_codes:
                # 全企業を非アクティブ化
                result = await self.db.execute(
                    update(Company)
                    .where(Company.is_active == True)
                    .values(
                        is_active=False,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # 指定コード以外を非アクティブ化
                result = await self.db.execute(
                    update(Company)
                    .where(
                        and_(
                            Company.is_active == True,
                            ~Company.code.in_(exclude_codes)
                        )
                    )
                    .values(
                        is_active=False,
                        updated_at=datetime.utcnow()
                    )
                )
            
            deactivated_count = result.rowcount
            
            if deactivated_count > 0:
                logger.info(f"Deactivated {deactivated_count} companies")
            
            return deactivated_count
            
        except Exception as e:
            logger.error(f"Error deactivating companies: {e}")
            raise RepositoryError(f"Failed to deactivate companies: {str(e)}")
    
    async def commit(self) -> None:
        """トランザクションをコミット"""
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error committing transaction: {e}")
            raise RepositoryError(f"Failed to commit transaction: {str(e)}")
    
    async def rollback(self) -> None:
        """トランザクションをロールバック"""
        try:
            await self.db.rollback()
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise RepositoryError(f"Failed to rollback transaction: {str(e)}")