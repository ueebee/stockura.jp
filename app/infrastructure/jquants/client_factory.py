"""J-Quants API 認証済みクライアントファクトリー"""
from typing import Tuple

from app.application.use_cases.auth_use_case import AuthUseCase
from app.core.config import get_settings
from app.domain.exceptions.jquants_exceptions import AuthenticationError
from app.infrastructure.jquants.auth_repository_impl import JQuantsAuthRepository
from app.infrastructure.jquants.base_client import JQuantsBaseClient
from app.infrastructure.jquants.listed_info_client import JQuantsListedInfoClient
from app.infrastructure.redis.auth_repository_impl import RedisAuthRepository
from app.infrastructure.redis.redis_client import get_redis_client
from app.core.logger import get_logger

logger = get_logger(__name__)


async def create_authenticated_client() -> Tuple[JQuantsBaseClient, JQuantsListedInfoClient]:
    """
    環境変数から認証情報を取得し、認証済みのクライアントを生成
    
    Returns:
        Tuple[JQuantsBaseClient, JQuantsListedInfoClient]: 認証済みクライアント
        
    Raises:
        AuthenticationError: 認証に失敗した場合
    """
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
        valid_credentials = await auth_use_case.ensure_valid_token(credentials)
        logger.info("J-Quants 認証が完了しました")
        
        # 認証済みクライアントを生成
        base_client = JQuantsBaseClient(credentials=valid_credentials)
        listed_info_client = JQuantsListedInfoClient(base_client)
        
        return base_client, listed_info_client
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"クライアント初期化エラー: {e}")
        raise AuthenticationError(f"J-Quants クライアントの初期化に失敗しました: {str(e)}")