"""
企業データ同期サービスのインターフェース定義

CompanySyncServiceのリファクタリングで使用する抽象基底クラス
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


class ICompanyDataFetcher(ABC):
    """企業データ取得インターフェース"""
    
    @abstractmethod
    async def fetch_all_companies(self, target_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        全企業データを取得
        
        Args:
            target_date: 取得対象日（Noneの場合は最新）
            
        Returns:
            List[Dict[str, Any]]: J-Quants APIレスポンスの企業データリスト
            
        Raises:
            DataFetchError: データ取得に失敗した場合
        """
        pass
    
    @abstractmethod
    async def fetch_company_by_code(self, code: str, target_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        特定企業データを取得
        
        Args:
            code: 銘柄コード
            target_date: 取得対象日（Noneの場合は最新）
            
        Returns:
            Optional[Dict[str, Any]]: J-Quants APIレスポンスの企業データ（見つからない場合はNone）
            
        Raises:
            DataFetchError: データ取得に失敗した場合
        """
        pass


class ICompanyDataMapper(ABC):
    """企業データマッピングインターフェース"""
    
    @abstractmethod
    def map_to_model(self, api_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        APIデータをモデル用にマッピング
        
        Args:
            api_data: J-Quants APIレスポンスデータ
            
        Returns:
            Optional[Dict[str, Any]]: モデル用にマッピングされたデータ（無効な場合はNone）
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        データ検証
        
        Args:
            data: 検証対象データ
            
        Returns:
            Tuple[bool, Optional[str]]: (検証結果, エラーメッセージ)
        """
        pass


class ICompanyRepository(ABC):
    """企業データリポジトリインターフェース"""
    
    @abstractmethod
    async def find_by_code(self, code: str) -> Optional[Company]:
        """
        銘柄コードで企業を検索
        
        Args:
            code: 銘柄コード
            
        Returns:
            Optional[Company]: 企業エンティティ（見つからない場合はNone）
        """
        pass
    
    @abstractmethod
    async def find_all_active(self) -> List[Company]:
        """
        全てのアクティブな企業を取得
        
        Returns:
            List[Company]: アクティブな企業のリスト
        """
        pass
    
    @abstractmethod
    async def save(self, company_data: Dict[str, Any]) -> Company:
        """
        企業データを保存
        
        Args:
            company_data: 保存する企業データ
            
        Returns:
            Company: 保存された企業エンティティ
        """
        pass
    
    @abstractmethod
    async def update(self, company: Company, update_data: Dict[str, Any]) -> Company:
        """
        企業データを更新
        
        Args:
            company: 更新対象の企業エンティティ
            update_data: 更新データ
            
        Returns:
            Company: 更新された企業エンティティ
        """
        pass
    
    @abstractmethod
    async def bulk_upsert(self, companies_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        企業データを一括更新
        
        Args:
            companies_data: 企業データのリスト
            
        Returns:
            Dict[str, int]: 処理結果統計 {"new_count": n, "updated_count": m}
        """
        pass
    
    @abstractmethod
    async def deactivate_companies(self, exclude_codes: List[str]) -> int:
        """
        指定コード以外の企業を非アクティブ化
        
        Args:
            exclude_codes: 除外する銘柄コードのリスト
            
        Returns:
            int: 非アクティブ化した企業数
        """
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """トランザクションをコミット"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """トランザクションをロールバック"""
        pass


class DataFetchError(Exception):
    """データ取得エラー"""
    pass


class DataValidationError(Exception):
    """データ検証エラー"""
    pass


class RepositoryError(Exception):
    """リポジトリ操作エラー"""
    pass