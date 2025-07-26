"""
APIクライアントインターフェース

外部APIとの通信を抽象化するインターフェース
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import date


class IAPIClient(ABC):
    """API通信の抽象インターフェース"""
    
    @abstractmethod
    async def get_listed_companies(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        上場企業情報を取得
        
        Args:
            code: 銘柄コード（4桁）
            target_date: 基準日
            
        Returns:
            List[Dict[str, Any]]: 上場企業情報のリスト
            
        Raises:
            AuthenticationError: 認証エラー
            RateLimitError: レート制限エラー
            NetworkError: ネットワークエラー
            DataValidationError: データ検証エラー
        """
        pass
    
    @abstractmethod
    async def get_daily_quotes(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        specific_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        日次株価データを取得
        
        Args:
            code: 銘柄コード（5桁）
            target_date: 取得日付
            from_date: 取得開始日
            to_date: 取得終了日
            specific_codes: 特定銘柄コードリスト
            
        Returns:
            List[Dict[str, Any]]: 株価データのリスト
            
        Raises:
            AuthenticationError: 認証エラー
            RateLimitError: レート制限エラー
            NetworkError: ネットワークエラー
            DataValidationError: データ検証エラー
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        API接続をテスト
        
        Returns:
            bool: 接続成功時はTrue
            
        Raises:
            AuthenticationError: 認証エラー
            NetworkError: ネットワークエラー
        """
        pass