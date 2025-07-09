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


# ページルート
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """ダッシュボードページ"""
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})

@app.get("/data-sources", response_class=HTMLResponse)
async def data_sources_page(request: Request):
    """データソース管理ページ"""
    return templates.TemplateResponse("pages/data_sources.html", {"request": request})

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """ジョブ管理ページ"""
    return templates.TemplateResponse("pages/jobs.html", {"request": request})

@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """分析ページ"""
    return templates.TemplateResponse("pages/analysis.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """設定ページ"""
    return templates.TemplateResponse("pages/settings.html", {"request": request})

# HTMX API エンドポイント
@app.get("/api/v1/dashboard/activities", response_class=HTMLResponse)
async def get_activities(request: Request):
    """最新アクティビティの取得"""
    # サンプルデータ（実際はDBから取得）
    activities = [
        {"time": "10分前", "action": "J-Quantsから企業データを同期", "status": "success"},
        {"time": "30分前", "action": "日次株価データの取得", "status": "success"},
        {"time": "1時間前", "action": "Yahoo Financeからのデータ取得", "status": "error"},
    ]
    return templates.TemplateResponse(
        "partials/activity_list.html", 
        {"request": request, "activities": activities}
    )

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