from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import httpx

from ..base import AuthStrategy


class JQuantsStrategy(AuthStrategy):
    """J-Quants用の認証ストラテジー"""

    def __init__(self, base_url: str = "https://api.jquants.com"):
        self.base_url = base_url

    def get_refresh_token(self, credentials: Dict[str, Any]) -> Tuple[Optional[str], Optional[datetime]]:
        """
        J-Quantsのリフレッシュトークンを取得します。

        Args:
            credentials: 認証情報（メールアドレスとパスワード）

        Returns:
            Tuple[Optional[str], Optional[datetime]]: (リフレッシュトークン, 有効期限)
        """
        try:
            with httpx.Client() as client:
                # リフレッシュトークンの取得
                response = client.post(
                    f"{self.base_url}/v1/token/auth_user",
                    json={
                        "mailaddress": credentials["mailaddress"],
                        "password": credentials["password"]
                    }
                )
                response.raise_for_status()
                refresh_token = response.json()["refreshToken"]

                # 有効期限は24時間
                expired_at = datetime.utcnow() + timedelta(hours=24)

                return refresh_token, expired_at
        except Exception as e:
            print(f"Error getting refresh token: {e}")
            return None, None

    def get_id_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[datetime]]:
        """
        J-QuantsのIDトークンを取得します。

        Args:
            refresh_token: リフレッシュトークン

        Returns:
            Tuple[Optional[str], Optional[datetime]]: (IDトークン, 有効期限)
        """
        try:
            with httpx.Client() as client:
                # IDトークンの取得
                response = client.post(
                    f"{self.base_url}/v1/token/auth_refresh",
                    headers={"Authorization": f"Bearer {refresh_token}"}
                )
                response.raise_for_status()
                id_token = response.json()["idToken"]

                # 有効期限は1時間
                expired_at = datetime.utcnow() + timedelta(hours=1)

                return id_token, expired_at
        except Exception as e:
            print(f"Error getting ID token: {e}")
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