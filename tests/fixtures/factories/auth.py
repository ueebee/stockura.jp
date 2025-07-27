"""
認証関連のテストファクトリー

認証エンティティのテストデータを生成します。
"""

from datetime import datetime, timedelta

import factory

from app.domain.entities.auth import IdToken, JQuantsCredentials, RefreshToken
from tests.fixtures.factories.base import BaseFactory


class RefreshTokenFactory(factory.Factory):
    """リフレッシュトークンのファクトリー"""
    
    class Meta:
        model = RefreshToken
    
    value = factory.Faker("sha256")


class IdTokenFactory(factory.Factory):
    """ID トークンのファクトリー"""
    
    class Meta:
        model = IdToken
    
    value = factory.Faker("sha256")
    expires_at = factory.LazyFunction(
        lambda: datetime.now() + timedelta(hours=24)
    )
    
    class Params:
        # パラメータで期限切れトークンを生成
        expired = factory.Trait(
            expires_at=factory.LazyFunction(
                lambda: datetime.now() - timedelta(hours=1)
            )
        )
        # まもなく期限切れになるトークン
        expiring_soon = factory.Trait(
            expires_at=factory.LazyFunction(
                lambda: datetime.now() + timedelta(minutes=3)
            )
        )


class JQuantsCredentialsFactory(factory.Factory):
    """J-Quants 認証情報のファクトリー"""
    
    class Meta:
        model = JQuantsCredentials
    
    email = factory.Faker("email")
    password = factory.Faker("password", length=12)
    refresh_token = factory.SubFactory(RefreshTokenFactory)
    id_token = factory.SubFactory(IdTokenFactory)
    
    class Params:
        # トークンなしの認証情報
        without_tokens = factory.Trait(
            refresh_token=None,
            id_token=None
        )
        # 期限切れトークンを持つ認証情報
        with_expired_token = factory.Trait(
            id_token=factory.SubFactory(IdTokenFactory, expired=True)
        )
        # テスト用の固定認証情報
        test_user = factory.Trait(
            email="test@example.com",
            password="test_password_123"
        )