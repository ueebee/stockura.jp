import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

import aiohttp
from aiohttp import ClientError, ClientSession

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    NetworkError,
    StorageError,
    TokenRefreshError,
)
from app.domain.repositories.auth_repository_interface import AuthRepositoryInterface


class JQuantsAuthRepository(AuthRepositoryInterface):
    """J-Quants API 認証リポジトリの実装"""

    BASE_URL = "https://api.jquants.com/v1"
    REFRESH_TOKEN_ENDPOINT = "/token/auth_user"
    ID_TOKEN_ENDPOINT = "/token/auth_refresh"

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """
        Args:
            storage_path: 認証情報を保存するファイルパス（None の場合はメモリのみ）
        """
        self._storage_path = storage_path
        self._memory_cache: Dict[str, JQuantsCredentials] = {}

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
        """認証情報を永続化"""
        # メモリキャッシュに保存
        self._memory_cache[credentials.email] = credentials

        # ファイルストレージが設定されている場合は保存
        if self._storage_path:
            try:
                # 既存のデータを読み込み
                existing_data = {}
                try:
                    with open(self._storage_path, "r") as f:
                        existing_data = json.load(f)
                except FileNotFoundError:
                    pass

                # 新しい認証情報を追加
                credential_dict = {
                    "email": credentials.email,
                    "password": credentials.password,
                    "refresh_token": (
                        credentials.refresh_token.value
                        if credentials.refresh_token
                        else None
                    ),
                    "id_token": (
                        credentials.id_token.value if credentials.id_token else None
                    ),
                    "id_token_expires_at": (
                        credentials.id_token.expires_at.isoformat()
                        if credentials.id_token
                        else None
                    ),
                }
                existing_data[credentials.email] = credential_dict

                # ファイルに書き込み
                with open(self._storage_path, "w") as f:
                    json.dump(existing_data, f, indent=2)

            except Exception as e:
                raise StorageError(f"認証情報の保存に失敗しました: {str(e)}")

    async def load_credentials(self, email: str) -> Optional[JQuantsCredentials]:
        """メールアドレスから認証情報を読み込み"""
        # メモリキャッシュを確認
        if email in self._memory_cache:
            return self._memory_cache[email]

        # ファイルストレージから読み込み
        if self._storage_path:
            try:
                with open(self._storage_path, "r") as f:
                    data = json.load(f)
                    
                if email in data:
                    credential_dict = data[email]
                    
                    # RefreshToken を復元
                    refresh_token = None
                    if credential_dict.get("refresh_token"):
                        refresh_token = RefreshToken(
                            value=credential_dict["refresh_token"]
                        )
                    
                    # IdToken を復元
                    id_token = None
                    if credential_dict.get("id_token") and credential_dict.get(
                        "id_token_expires_at"
                    ):
                        id_token = IdToken(
                            value=credential_dict["id_token"],
                            expires_at=datetime.fromisoformat(
                                credential_dict["id_token_expires_at"]
                            ),
                        )
                    
                    credentials = JQuantsCredentials(
                        email=credential_dict["email"],
                        password=credential_dict["password"],
                        refresh_token=refresh_token,
                        id_token=id_token,
                    )
                    
                    # メモリキャッシュに追加
                    self._memory_cache[email] = credentials
                    return credentials
                    
            except FileNotFoundError:
                return None
            except Exception as e:
                raise StorageError(f"認証情報の読み込みに失敗しました: {str(e)}")

        return None