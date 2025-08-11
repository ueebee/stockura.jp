from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.infrastructure.redis.redis_client import redis_client
from app.presentation.api.v1 import api_router
from app.presentation.middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    RequestIDMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    try:
        # Redis 接続は任意（エラーが発生しても続行）
        await redis_client.connect()
    except Exception as e:
        print(f"Redis connection failed: {e}")
    
    yield
    
    # 終了時の処理
    try:
        await redis_client.disconnect()
    except Exception:
        pass


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ミドルウェアの登録（順序が重要：下から上に実行される）
# 1. CORS（最も内側）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. リクエスト ID 管理
app.add_middleware(RequestIDMiddleware)

# 3. リクエスト/レスポンスロギング
app.add_middleware(RequestLoggingMiddleware)

# 4. エラーハンドリング（最も外側）
app.add_middleware(ErrorHandlingMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Welcome to Stockura API",
        "version": settings.app_version,
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }
