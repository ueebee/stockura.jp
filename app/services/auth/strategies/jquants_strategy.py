from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import httpx

from ..base import AuthStrategy


class JQuantsStrategy(AuthStrategy):
    """J-Quants用の認証ストラテジー"""

    def __init__(self, base_url: str = "https://api.jquants.com"):
        self.base_url = base_url

    def get_refresh_token(
        self, credentials: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """
        J-Quantsのリフレッシュトークンを取得します。

        Args:
            credentials: 認証情報（メールアドレスとパスワード）

        Returns:
            Tuple[Optional[str], Optional[datetime]]: (リフレッシュトークン, 有効期限)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Attempting to get refresh token from J-Quants API at {self.base_url}")
            logger.debug(f"Credentials keys: {list(credentials.keys())}")
            
            with httpx.Client() as client:
                # リフレッシュトークンの取得
                url = f"{self.base_url}/v1/token/auth_user"
                payload = {
                    "mailaddress": credentials.get("mailaddress", ""),
                    "password": credentials.get("password", ""),
                }
                logger.debug(f"Requesting refresh token from: {url}")
                
                response = client.post(url, json=payload, timeout=30.0)
                
                if response.status_code != 200:
                    logger.error(f"J-Quants API returned status {response.status_code}: {response.text}")
                    return None, None
                
                response_data = response.json()
                refresh_token = response_data.get("refreshToken")
                
                if not refresh_token:
                    logger.error(f"No refreshToken in response: {response_data}")
                    return None, None

                # 有効期限は1週間（7日間）
                expired_at = datetime.utcnow() + timedelta(days=7)
                logger.info("Successfully obtained refresh token from J-Quants")

                return refresh_token, expired_at
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting refresh token: {e.response.status_code} - {e.response.text}")
            return None, None
        except Exception as e:
            logger.error(f"Error getting refresh token: {type(e).__name__}: {e}")
            return None, None

    def get_id_token(
        self, refresh_token: str
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """
        J-QuantsのIDトークンを取得します。

        Args:
            refresh_token: リフレッシュトークン

        Returns:
            Tuple[Optional[str], Optional[datetime]]: (IDトークン, 有効期限)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Attempting to get ID token from J-Quants API")
            
            with httpx.Client() as client:
                # IDトークンの取得（クエリパラメータでリフレッシュトークンを送信）
                url = f"{self.base_url}/v1/token/auth_refresh?refreshtoken={refresh_token}"
                logger.debug(f"Requesting ID token from: {url}")
                
                response = client.post(url, timeout=30.0)
                
                if response.status_code != 200:
                    logger.error(f"J-Quants API returned status {response.status_code}: {response.text}")
                    return None, None
                
                response_data = response.json()
                id_token = response_data.get("idToken")
                
                if not id_token:
                    logger.error(f"No idToken in response: {response_data}")
                    return None, None

                # 有効期限は24時間
                expired_at = datetime.utcnow() + timedelta(hours=24)
                logger.info("Successfully obtained ID token from J-Quants")

                return id_token, expired_at
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting ID token: {e.response.status_code} - {e.response.text}")
            return None, None
        except Exception as e:
            logger.error(f"Error getting ID token: {type(e).__name__}: {e}")
            return None, None

    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        認証情報が有効かどうかを検証します。

        Args:
            credentials: 認証情報

        Returns:
            bool: 認証情報が有効な場合はTrue
        """
        required_fields = ["mailaddress", "password"]
        return all(field in credentials for field in required_fields)

