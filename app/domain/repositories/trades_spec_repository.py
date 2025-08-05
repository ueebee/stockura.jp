"""投資部門別売買状況リポジトリインターフェース"""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.domain.entities.trades_spec import TradesSpec


class TradesSpecRepository(ABC):
    """投資部門別売買状況リポジトリのインターフェース"""
    
    @abstractmethod
    async def save(self, trades_spec: TradesSpec) -> None:
        """投資部門別売買状況を保存する
        
        Args:
            trades_spec: 保存する投資部門別売買状況エンティティ
        """
        pass
    
    @abstractmethod
    async def save_bulk(self, trades_specs: List[TradesSpec]) -> None:
        """複数の投資部門別売買状況を一括保存する
        
        Args:
            trades_specs: 保存する投資部門別売買状況エンティティのリスト
        """
        pass
    
    @abstractmethod
    async def find_by_code_and_date(self, code: str, trade_date: date) -> Optional[TradesSpec]:
        """銘柄コードと日付で投資部門別売買状況を検索する
        
        Args:
            code: 銘柄コード
            trade_date: 取引日
            
        Returns:
            見つかった場合は TradesSpec 、見つからない場合は None
        """
        pass
    
    @abstractmethod
    async def find_by_code_and_date_range(
        self,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[TradesSpec]:
        """銘柄コードと日付範囲で投資部門別売買状況を検索する
        
        Args:
            code: 銘柄コード
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            検索結果のリスト
        """
        pass
    
    @abstractmethod
    async def find_by_date_and_section(
        self,
        trade_date: date,
        section: Optional[str] = None
    ) -> List[TradesSpec]:
        """日付と市場区分で投資部門別売買状況を検索する
        
        Args:
            trade_date: 取引日
            section: 市場区分（省略可）
            
        Returns:
            検索結果のリスト
        """
        pass
    
    @abstractmethod
    async def find_by_date_range_and_section(
        self,
        start_date: date,
        end_date: date,
        section: Optional[str] = None
    ) -> List[TradesSpec]:
        """日付範囲と市場区分で投資部門別売買状況を検索する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            section: 市場区分（省略可）
            
        Returns:
            検索結果のリスト
        """
        pass
    
    @abstractmethod
    async def delete_by_date_range(self, start_date: date, end_date: date) -> int:
        """日付範囲で投資部門別売買状況を削除する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            削除された件数
        """
        pass