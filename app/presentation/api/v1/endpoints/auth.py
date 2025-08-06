from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.application.use_cases.auth_use_case import AuthUseCase
from app.domain.entities.auth import JQuantsCredentials
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    TokenRefreshError,
)
from app.domain.repositories.auth_repository import AuthRepository
from app.infrastructure.repositories.redis.auth_repository_impl import RedisAuthRepository
from app.infrastructure.redis.redis_client import get_redis_client

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    email: str = Field(..., description="J-Quants アカウントのメールアドレス")
    password: str = Field(..., description="J-Quants アカウントのパスワード")


class LoginResponse(BaseModel):
    email: str
    has_valid_token: bool
    message: str


class RefreshTokenRequest(BaseModel):
    email: str = Field(..., description="J-Quants アカウントのメールアドレス")


class RefreshTokenResponse(BaseModel):
    email: str
    has_valid_token: bool
    message: str


async def get_auth_repository() -> AuthRepository:
    """認証リポジトリの依存性注入"""
    redis_client = await get_redis_client()
    return RedisAuthRepository(redis_client)


def get_auth_use_case(
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> AuthUseCase:
    """認証ユースケースの依存性注入"""
    return AuthUseCase(auth_repository)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
) -> LoginResponse:
    """
    J-Quants アカウントでログイン
    
    Args:
        request: ログインリクエスト（メールアドレスとパスワード）
        
    Returns:
        LoginResponse: ログイン結果
        
    Raises:
        HTTPException: 認証に失敗した場合
    """
    try:
        credentials = await auth_use_case.authenticate(
            email=request.email,
            password=request.password
        )
        
        return LoginResponse(
            email=credentials.email,
            has_valid_token=credentials.has_valid_id_token(),
            message="ログインに成功しました"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ログイン処理中にエラーが発生しました: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
) -> RefreshTokenResponse:
    """
    ID トークンを更新
    
    Args:
        request: トークン更新リクエスト（メールアドレス）
        
    Returns:
        RefreshTokenResponse: トークン更新結果
        
    Raises:
        HTTPException: トークン更新に失敗した場合
    """
    try:
        # 保存された認証情報を取得
        existing_credentials = await auth_use_case.get_valid_credentials(request.email)
        if not existing_credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証情報が見つかりません。先にログインしてください。"
            )
        
        # トークンを更新
        updated_credentials = await auth_use_case.ensure_valid_token(existing_credentials)
        
        return RefreshTokenResponse(
            email=updated_credentials.email,
            has_valid_token=updated_credentials.has_valid_id_token(),
            message="トークンの更新に成功しました"
        )
        
    except TokenRefreshError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"トークン更新処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/status/{email}", response_model=dict)
async def check_auth_status(
    email: str,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
) -> dict:
    """
    認証状態を確認
    
    Args:
        email: 確認対象のメールアドレス
        
    Returns:
        dict: 認証状態
    """
    try:
        credentials = await auth_use_case.get_valid_credentials(email)
        
        if credentials:
            return {
                "email": email,
                "authenticated": True,
                "has_valid_token": credentials.has_valid_id_token(),
                "needs_refresh": credentials.needs_refresh()
            }
        else:
            return {
                "email": email,
                "authenticated": False,
                "has_valid_token": False,
                "needs_refresh": True
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"認証状態の確認中にエラーが発生しました: {str(e)}"
        )


class LogoutRequest(BaseModel):
    email: str = Field(..., description="J-Quants アカウントのメールアドレス")


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> dict:
    """
    ログアウト（認証情報を削除）
    
    Args:
        email: ログアウトするアカウントのメールアドレス
        
    Returns:
        dict: ログアウト結果
    """
    try:
        # RedisAuthRepository の場合のみ delete_credentials メソッドを呼び出す
        if hasattr(auth_repository, 'delete_credentials'):
            await auth_repository.delete_credentials(request.email)
        
        return {
            "email": request.email,
            "message": "ログアウトしました"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ログアウト処理中にエラーが発生しました: {str(e)}"
        )