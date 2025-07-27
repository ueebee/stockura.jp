from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class RefreshToken:
    """リフレッシュトークンのバリューオブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("リフレッシュトークンは空にできません")


@dataclass(frozen=True)
class IdToken:
    """ID トークンのバリューオブジェクト"""

    value: str
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ID トークンは空にできません")

    @property
    def is_expired(self) -> bool:
        """トークンが期限切れかどうか確認"""
        return datetime.now() >= self.expires_at

    def is_expiring_soon(self, threshold_minutes: int = 5) -> bool:
        """トークンがまもなく期限切れになるかどうか確認"""
        threshold = datetime.now() + timedelta(minutes=threshold_minutes)
        return threshold >= self.expires_at


@dataclass
class JQuantsCredentials:
    """J-Quants API 認証情報のエンティティ"""

    email: str
    password: str
    refresh_token: Optional[RefreshToken] = None
    id_token: Optional[IdToken] = None

    def __post_init__(self) -> None:
        if not self.email:
            raise ValueError("メールアドレスは必須です")
        if not self.password:
            raise ValueError("パスワードは必須です")

    def has_valid_id_token(self) -> bool:
        """有効な ID トークンを持っているか確認"""
        return self.id_token is not None and not self.id_token.is_expired

    def needs_refresh(self) -> bool:
        """ID トークンの更新が必要か確認"""
        if self.id_token is None:
            return True
        return self.id_token.is_expired or self.id_token.is_expiring_soon()

    def update_tokens(
        self, refresh_token: RefreshToken, id_token: IdToken
    ) -> JQuantsCredentials:
        """新しいトークンで認証情報を更新"""
        return JQuantsCredentials(
            email=self.email,
            password=self.password,
            refresh_token=refresh_token,
            id_token=id_token,
        )

    def update_id_token(self, id_token: IdToken) -> JQuantsCredentials:
        """ID トークンのみ更新"""
        return JQuantsCredentials(
            email=self.email,
            password=self.password,
            refresh_token=self.refresh_token,
            id_token=id_token,
        )
