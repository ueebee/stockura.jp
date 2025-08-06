"""Redis ベースの J-Quants 認証リポジトリ実装"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional

import aiohttp
from aiohttp import ClientError, ClientSession
from redis.asyncio import Redis

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    NetworkError,
    StorageError,
    TokenRefreshError,
)
from app.domain.repositories.auth_repository import AuthRepository


class RedisAuthRepository(AuthRepository):
    """Redis を使用した J-Quants API 認証リポジトリの実装"""

    BASE_URL = "https://api.jquants.com/v1"
    REFRESH_TOKEN_ENDPOINT = "/token/auth_user"
    ID_TOKEN_ENDPOINT = "/token/auth_refresh"
    
    # Redis キーのプレフィックス
    REFRESH_TOKEN_PREFIX = "jquants:refresh_token:"
    ID_TOKEN_PREFIX = "jquants:id_token:"
    CREDENTIALS_PREFIX = "jquants:credentials:"
    
    # トークンの有効期限
    REFRESH_TOKEN_TTL = 7 * 24 * 60 * 60  # 7 日間（秒）
    ID_TOKEN_TTL = 23 * 60 * 60  # 23 時間（秒） - トークンの有効期限（24 時間）より少し短く

    def __init__(self, redis_client: Redis) -> None:
        """
        Args:
            redis_client: Redis クライアント
        """
        self._redis = redis_client

    async def get_refresh_token(
        self, email: str, password: str
    ) -> Optional[RefreshToken]:
        """メールアドレスとパスワードからリフレッシュトークンを取得"""
        # TCP コネクターの設定
        connector = aiohttp.TCPConnector(
            force_close=True,  # 接続を強制的にクローズ
            limit=100,         # 接続数の制限
            ttl_dns_cache=300  # DNS キャッシュの TTL
        )
        
        # タイムアウトの設定
        timeout = aiohttp.ClientTimeout(
            total=30,      # 全体のタイムアウト
            connect=10,    # 接続タイムアウト
            sock_read=10   # 読み取りタイムアウト
        )
        
        session = None
        try:
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            
            payload = {"mailaddress": email, "password": password}
            
            async with session.post(
                f"{self.BASE_URL}{self.REFRESH_TOKEN_ENDPOINT}",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return RefreshToken(value=data["refreshToken"])
                elif response.status == 400:
                    raise AuthenticationError("メールアドレスまたはパスワードが正しくありません。")
                else:
                    raise AuthenticationError(
                        f"認証エラーが発生しました。ステータスコード: {response.status}"
                    )
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"ネットワークエラーが発生しました: {str(e)}")
        except (KeyError, json.JSONDecodeError) as e:
            raise AuthenticationError(f"レスポンスの解析に失敗しました: {str(e)}")
        finally:
            # セッションを確実にクローズ
            if session:
                await session.close()
                # TCP コネクションが完全にクローズされるまで少し待つ
                await asyncio.sleep(0.1)

    async def get_id_token(self, refresh_token: RefreshToken) -> Optional[IdToken]:
        """リフレッシュトークンから ID トークンを取得"""
        # TCP コネクターの設定
        connector = aiohttp.TCPConnector(
            force_close=True,  # 接続を強制的にクローズ
            limit=100,         # 接続数の制限
            ttl_dns_cache=300  # DNS キャッシュの TTL
        )
        
        # タイムアウトの設定
        timeout = aiohttp.ClientTimeout(
            total=30,      # 全体のタイムアウト
            connect=10,    # 接続タイムアウト
            sock_read=10   # 読み取りタイムアウト
        )
        
        session = None
        try:
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            
            params = {"refreshtoken": refresh_token.value}
            
            async with session.post(
                f"{self.BASE_URL}{self.ID_TOKEN_ENDPOINT}",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # ID トークンの有効期限は通常 24 時間
                    expires_at = datetime.now() + timedelta(hours=24)
                    return IdToken(value=data["idToken"], expires_at=expires_at)
                elif response.status == 400:
                    raise TokenRefreshError("リフレッシュトークンが無効です。")
                else:
                    raise TokenRefreshError(
                        f"トークンリフレッシュエラーが発生しました。ステータスコード: {response.status}"
                    )
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"ネットワークエラーが発生しました: {str(e)}")
        except (KeyError, json.JSONDecodeError) as e:
            raise TokenRefreshError(f"レスポンスの解析に失敗しました: {str(e)}")
        finally:
            # セッションを確実にクローズ
            if session:
                await session.close()
                # TCP コネクションが完全にクローズされるまで少し待つ
                await asyncio.sleep(0.1)

    async def save_credentials(self, credentials: JQuantsCredentials) -> None:
        """認証情報を Redis に保存"""
        try:
            # リフレッシュトークンを保存（TTL: 7 日間）
            if credentials.refresh_token:
                await self._redis.setex(
                    f"{self.REFRESH_TOKEN_PREFIX}{credentials.email}",
                    self.REFRESH_TOKEN_TTL,
                    credentials.refresh_token.value
                )
            
            # ID トークンを保存（TTL: 24 時間）
            if credentials.id_token:
                await self._redis.setex(
                    f"{self.ID_TOKEN_PREFIX}{credentials.email}",
                    self.ID_TOKEN_TTL,
                    credentials.id_token.value
                )
                
                # ID トークンの有効期限も別途保存
                await self._redis.setex(
                    f"{self.ID_TOKEN_PREFIX}{credentials.email}:expires_at",
                    self.ID_TOKEN_TTL,
                    credentials.id_token.expires_at.isoformat()
                )
            
            # 認証情報のメタデータを保存（パスワードは保存しない）
            metadata = {
                "email": credentials.email,
                "last_updated": datetime.now().isoformat()
            }
            await self._redis.setex(
                f"{self.CREDENTIALS_PREFIX}{credentials.email}",
                self.REFRESH_TOKEN_TTL,  # リフレッシュトークンと同じ TTL
                json.dumps(metadata)
            )
            
        except Exception as e:
            raise StorageError(f"認証情報の保存に失敗しました: {str(e)}")

    async def load_credentials(self, email: str) -> Optional[JQuantsCredentials]:
        """Redis から認証情報を読み込み"""
        try:
            # メタデータを確認
            metadata_json = await self._redis.get(f"{self.CREDENTIALS_PREFIX}{email}")
            if not metadata_json:
                return None
            
            # リフレッシュトークンを取得
            refresh_token_value = await self._redis.get(
                f"{self.REFRESH_TOKEN_PREFIX}{email}"
            )
            refresh_token = None
            if refresh_token_value:
                refresh_token = RefreshToken(value=refresh_token_value)
            
            # ID トークンを取得
            id_token_value = await self._redis.get(f"{self.ID_TOKEN_PREFIX}{email}")
            id_token_expires = await self._redis.get(
                f"{self.ID_TOKEN_PREFIX}{email}:expires_at"
            )
            id_token = None
            if id_token_value and id_token_expires:
                id_token = IdToken(
                    value=id_token_value,
                    expires_at=datetime.fromisoformat(id_token_expires)
                )
            
            # 注意: パスワードは Redis に保存していないため、
            # 完全な認証情報を復元することはできません。
            # 実際の使用では、パスワードは初回認証時のみ必要で、
            # その後はトークンベースで認証を行います。
            return JQuantsCredentials(
                email=email,
                password="REDIS_STORED_CREDENTIAL",  # パスワードは保存されていない
                refresh_token=refresh_token,
                id_token=id_token,
            )
            
        except Exception as e:
            raise StorageError(f"認証情報の読み込みに失敗しました: {str(e)}")

    async def delete_credentials(self, email: str) -> None:
        """認証情報を削除（ログアウト時などに使用）"""
        try:
            keys_to_delete = [
                f"{self.REFRESH_TOKEN_PREFIX}{email}",
                f"{self.ID_TOKEN_PREFIX}{email}",
                f"{self.ID_TOKEN_PREFIX}{email}:expires_at",
                f"{self.CREDENTIALS_PREFIX}{email}",
            ]
            
            for key in keys_to_delete:
                await self._redis.delete(key)
                
        except Exception as e:
            raise StorageError(f"認証情報の削除に失敗しました: {str(e)}")