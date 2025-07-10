from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
import asyncio

from app.api.v1.endpoints import data_sources, companies, daily_quotes
from app.services.encryption import get_encryption_service
from app.db.session import check_database_connection
from app.services.token_manager import cleanup_expired_tokens
from app.services.auth import StrategyRegistry
from app.services.auth.strategies.jquants_strategy import JQuantsStrategy
from app.services.auth.strategies.yfinance_strategy import YFinanceStrategy

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stockura",
    description="株価データ取得・表示システム",
    version="1.0.0",
)

# テンプレートの設定
templates = Jinja2Templates(directory="app/templates")

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# APIルーターの登録
app.include_router(
    data_sources.router,
    prefix="/api/v1/data-sources",
    tags=["data-sources"]
)

app.include_router(
    companies.router,
    prefix="/api/v1/companies",
    tags=["companies"]
)

app.include_router(
    daily_quotes.router,
    prefix="/api/v1",
    tags=["daily-quotes"]
)

# HTMXビュールーターの登録
from app.api.v1.views import (
    dashboard_router,
    data_sources_router as ds_view_router,
    api_endpoints_router,
    jobs_router,
    analysis_router,
    settings_router
)

app.include_router(dashboard_router, prefix="", tags=["pages"])
app.include_router(ds_view_router, prefix="/data-sources", tags=["pages"])
app.include_router(api_endpoints_router, prefix="", tags=["pages"])
app.include_router(jobs_router, prefix="/jobs", tags=["pages"])
app.include_router(analysis_router, prefix="/analysis", tags=["pages"])
app.include_router(settings_router, prefix="/settings", tags=["pages"])


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("Starting Stockura application...")
    
    # 認証ストラテジーを登録
    try:
        StrategyRegistry.register("jquants", JQuantsStrategy)
        StrategyRegistry.register("yfinance", YFinanceStrategy)
        logger.info(f"Registered authentication strategies: {StrategyRegistry.get_supported_providers()}")
    except Exception as e:
        logger.error(f"Failed to register authentication strategies: {e}")
        raise
    
    # データベース接続の健全性チェック
    try:
        if await check_database_connection():
            logger.info("Database connection check passed")
        else:
            logger.error("Database connection check failed")
            raise Exception("Database connection failed")
    except Exception as e:
        logger.error(f"Failed to check database connection: {e}")
        raise
    
    # 暗号化サービスのテスト
    try:
        encryption_service = get_encryption_service()
        if encryption_service.test_encryption():
            logger.info("Encryption service test passed")
        else:
            logger.error("Encryption service test failed")
            raise Exception("Encryption service test failed")
    except Exception as e:
        logger.error(f"Failed to initialize encryption service: {e}")
        raise
    
    # トークンクリーンアップタスクを開始
    try:
        asyncio.create_task(cleanup_expired_tokens())
        logger.info("Token cleanup task started successfully")
    except Exception as e:
        logger.error(f"Failed to start token cleanup task: {e}")
        # トークンクリーンアップはクリティカルではないため、続行
    
    logger.info("Application startup completed successfully")


# ページルートはすべてビューモジュールに移動済み

@app.get("/api")
async def api_root():
    """API ルートエンドポイント"""
    return {"message": "Welcome to Stockura API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "message": "Application is running",
        "version": "1.0.0"
    } 