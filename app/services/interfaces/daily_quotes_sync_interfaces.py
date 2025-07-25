"""
日次株価データ同期サービスのインターフェース定義

DailyQuotesSyncServiceのリファクタリングで使用する抽象基底クラス
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from decimal import Decimal

from app.models.daily_quote import DailyQuote


class IDailyQuotesDataFetcher(ABC):
    """日次株価データ取得インターフェース"""
    
    @abstractmethod
    async def fetch_quotes_by_date(
        self, 
        target_date: date,
        codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        指定日の株価データを取得
        
        Args:
            target_date: 取得対象日
            codes: 銘柄コードリスト（Noneの場合は全銘柄）
            
        Returns:
            List[Dict[str, Any]]: J-Quants APIレスポンスの株価データリスト
            
        Raises:
            DataFetchError: データ取得に失敗した場合
            RateLimitError: レート制限に達した場合
        """
        pass
    
    @abstractmethod
    async def fetch_quotes_by_date_range(
        self,
        from_date: date,
        to_date: date,
        codes: Optional[List[str]] = None
    ) -> Dict[date, List[Dict[str, Any]]]:
        """
        日付範囲の株価データを取得
        
        Args:
            from_date: 開始日
            to_date: 終了日
            codes: 銘柄コードリスト（Noneの場合は全銘柄）
            
        Returns:
            Dict[date, List[Dict[str, Any]]]: 日付をキーとした株価データ辞書
            
        Raises:
            DataFetchError: データ取得に失敗した場合
            RateLimitError: レート制限に達した場合
        """
        pass


class IDailyQuotesDataMapper(ABC):
    """日次株価データマッピングインターフェース"""
    
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
    def validate_quote_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        株価データの妥当性検証
        
        Args:
            data: 検証対象データ
            
        Returns:
            Tuple[bool, Optional[str]]: (検証結果, エラーメッセージ)
        """
        pass
    
    @abstractmethod
    def convert_price_fields(self, value: Any) -> Optional[Decimal]:
        """
        価格フィールドの安全な変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            Optional[Decimal]: 変換された価格（変換できない場合はNone）
        """
        pass
    
    @abstractmethod
    def convert_volume_fields(self, value: Any) -> Optional[int]:
        """
        出来高フィールドの安全な変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            Optional[int]: 変換された出来高（変換できない場合はNone）
        """
        pass


class IDailyQuotesRepository(ABC):
    """日次株価データリポジトリインターフェース"""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def find_latest_date_by_code(self, code: str) -> Optional[date]:
        """
        銘柄の最新取引日を取得
        
        Args:
            code: 銘柄コード
            
        Returns:
            Optional[date]: 最新取引日（データがない場合はNone）
        """
        pass
    
    @abstractmethod
    async def check_company_exists(self, code: str) -> bool:
        """
        企業マスタに存在するか確認
        
        Args:
            code: 銘柄コード
            
        Returns:
            bool: 存在する場合True
        """
        pass
    
    @abstractmethod
    async def get_active_company_codes(self) -> List[str]:
        """
        アクティブな企業コードリストを取得
        
        Returns:
            List[str]: アクティブな企業の銘柄コードリスト
        """
        pass
    
    @abstractmethod
    async def commit_batch(self) -> None:
        """バッチコミット"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """ロールバック"""
        pass


class DataFetchError(Exception):
    """データ取得エラー"""
    pass


class RateLimitError(Exception):
    """レート制限エラー"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after