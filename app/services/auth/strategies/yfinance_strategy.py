from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from ..base import AuthStrategy


class YFinanceStrategy(AuthStrategy):
    """Yahoo Finance用の認証ストラテジー（認証不要）"""

    def __init__(self, base_url: str = "https://query1.finance.yahoo.com"):
        self.base_url = base_url

    def get_refresh_token(self, credentials: Dict[str, Any]) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Yahoo Financeは認証不要のため、ダミートークンを返します。
        
        Args:
            credentials: 認証情報（使用されません）
            
        Returns:
            Tuple[Optional[str], Optional[datetime]]: (ダミートークン, 有効期限)
        """
        # Yahoo Financeは認証不要なので、ダミートークンを返す
        dummy_token = "yfinance_no_auth_required"
        # 長期間有効な期限を設定（1年）
        expired_at = datetime.utcnow() + timedelta(days=365)
        return dummy_token, expired_at

    def get_id_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Yahoo Financeは認証不要のため、ダミートークンを返します。
        
        Args:
            refresh_token: リフレッシュトークン（使用されません）
            
        Returns:
            Tuple[Optional[str], Optional[datetime]]: (ダミートークン, 有効期限)
        """
        # Yahoo Financeは認証不要なので、ダミートークンを返す
        dummy_token = "yfinance_api_token"
        # 長期間有効な期限を設定（1年）
        expired_at = datetime.utcnow() + timedelta(days=365)
        return dummy_token, expired_at

    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Yahoo Financeは認証不要のため、常にTrueを返します。
        
        Args:
            credentials: 認証情報
            
        Returns:
            bool: 常にTrue
        """
        return True