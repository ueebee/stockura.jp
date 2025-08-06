"""J-Quants API 認証済みクライアントファクトリー"""
from typing import Optional, Tuple

from app.application.use_cases.auth_use_case import AuthUseCase
from app.core.config import get_settings
from app.domain.entities.auth import JQuantsCredentials
from app.domain.exceptions.jquants_exceptions import AuthenticationError
from app.infrastructure.jquants.announcement_client import JQuantsAnnouncementClient
from app.infrastructure.jquants.auth_repository_impl import JQuantsAuthRepository
from app.infrastructure.jquants.base_client import JQuantsBaseClient
from app.infrastructure.jquants.listed_info_client import JQuantsListedInfoClient
from app.infrastructure.jquants.trades_spec_client import TradesSpecClient
from app.infrastructure.redis.auth_repository_impl import RedisAuthRepository
from app.infrastructure.redis.redis_client import get_redis_client
from app.core.logger import get_logger

logger = get_logger(__name__)


class JQuantsClientFactory:
    """J-Quants API クライアントファクトリー"""
    
    def __init__(self) -> None:
        self._credentials: Optional[JQuantsCredentials] = None
        self._base_client: Optional[JQuantsBaseClient] = None
    
    async def _ensure_authenticated(self) -> JQuantsCredentials:
        """認証を確実に実行し、認証情報を返す"""
        if self._credentials:
            return self._credentials
            
        try:
            # 環境変数から認証情報を取得
            settings = get_settings()
            
            if not settings.jquants_email or not settings.jquants_password:
                raise AuthenticationError(
                    "J-Quants 認証情報が設定されていません。"
                    "JQUANTS_EMAIL と JQUANTS_PASSWORD を環境変数に設定してください。"
                )
            
            # 認証リポジトリを初期化（Redis が利用可能なら Redis 、そうでなければファイル）
            try:
                redis_client = await get_redis_client()
                auth_repo = RedisAuthRepository(redis_client)
                logger.info("Redis 認証リポジトリを使用します")
            except Exception as e:
                logger.warning(f"Redis 接続エラー: {e}. ファイルベースの認証リポジトリを使用します")
                auth_repo = JQuantsAuthRepository(storage_path=".jquants_auth.json")
            
            # 認証ユースケースを初期化
            auth_use_case = AuthUseCase(auth_repo)
            
            # 認証実行（キャッシュがあれば利用）
            logger.info(f"J-Quants 認証を開始します: {settings.jquants_email}")
            credentials = await auth_use_case.authenticate(
                email=settings.jquants_email,
                password=settings.jquants_password
            )
            
            # トークンの有効性確認と必要に応じて更新
            self._credentials = await auth_use_case.ensure_valid_token(credentials)
            logger.info("J-Quants 認証が完了しました")
            
            return self._credentials
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"認証エラー: {e}")
            raise AuthenticationError(f"J-Quants 認証に失敗しました: {str(e)}")
    
    async def _get_base_client(self) -> JQuantsBaseClient:
        """ベースクライアントを取得（シングルトン）"""
        if self._base_client:
            return self._base_client
            
        credentials = await self._ensure_authenticated()
        self._base_client = JQuantsBaseClient(credentials=credentials)
        return self._base_client
    
    async def create_listed_info_client(self) -> JQuantsListedInfoClient:
        """上場銘柄情報クライアントを作成"""
        base_client = await self._get_base_client()
        return JQuantsListedInfoClient(base_client)
    
    async def create_trades_spec_client(self) -> TradesSpecClient:
        """投資部門別売買状況クライアントを作成"""
        credentials = await self._ensure_authenticated()
        return TradesSpecClient(credentials=credentials)

    async def create_weekly_margin_interest_client(self) -> "WeeklyMarginInterestClient":
        """週次信用取引残高クライアントを作成"""
        from app.infrastructure.jquants.weekly_margin_interest_client import WeeklyMarginInterestClient
        credentials = await self._ensure_authenticated()
        return WeeklyMarginInterestClient(credentials=credentials)

    async def create_announcement_client(self) -> JQuantsAnnouncementClient:
        """決算発表予定クライアントを作成"""
        base_client = await self._get_base_client()
        return JQuantsAnnouncementClient(base_client)
    
    async def create_authenticated_clients(self) -> Tuple[JQuantsBaseClient, JQuantsListedInfoClient]:
        """後方互換性のための認証済みクライアント生成メソッド"""
        base_client = await self._get_base_client()
        listed_info_client = await self.create_listed_info_client()
        return base_client, listed_info_client


# 後方互換性のための関数
async def create_authenticated_client() -> Tuple[JQuantsBaseClient, JQuantsListedInfoClient]:
    """
    環境変数から認証情報を取得し、認証済みのクライアントを生成
    
    Returns:
        Tuple[JQuantsBaseClient, JQuantsListedInfoClient]: 認証済みクライアント
        
    Raises:
        AuthenticationError: 認証に失敗した場合
    """
    factory = JQuantsClientFactory()
    return await factory.create_authenticated_clients()