"""決算発表予定取得タスク（asyncpg 版）"""

import asyncio
from typing import Dict, Any

import asyncpg
from celery.utils.log import get_task_logger

from app.application.use_cases.fetch_announcement import FetchAnnouncementUseCase
from app.core.config import get_settings
from app.infrastructure.celery.app import celery_app
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.repositories.database.announcement_repository_impl import AnnouncementRepositoryImpl
from app.infrastructure.database.connection import get_sessionmaker

logger = get_task_logger(__name__)


async def async_fetch_announcement_data() -> Dict[str, Any]:
    """非同期で決算発表予定データを取得・保存する"""
    settings = get_settings()
    
    # データベース接続の作成
    conn = await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
    )
    
    try:
        # セッションメーカーとセッション作成
        AsyncSessionMaker = get_sessionmaker()
        async with AsyncSessionMaker() as session:
            # クライアントファクトリーの初期化
            client_factory = JQuantsClientFactory()
            announcement_client = await client_factory.create_announcement_client()
            
            # リポジトリの初期化
            announcement_repository = AnnouncementRepositoryImpl(session)
            
            # ユースケースの初期化と実行
            use_case = FetchAnnouncementUseCase(
                announcement_client=announcement_client,
                announcement_repository=announcement_repository,
            )
            
            logger.info("Starting announcement data fetch")
            result = await use_case.fetch_and_save_announcements()
            
            logger.info(f"Successfully fetched {result.total_count} announcements")
            
            return {
                "status": "success",
                "total_count": result.total_count,
                "message": f"Fetched {result.total_count} announcements",
            }
            
    except Exception as e:
        logger.error(f"Error fetching announcement data: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to fetch announcement data",
        }
    finally:
        await conn.close()


@celery_app.task(bind=True, name="fetch_announcement_data")
def fetch_announcement_data(self) -> Dict[str, Any]:
    """決算発表予定データを取得する Celery タスク"""
    logger.info(f"Starting announcement data fetch task: {self.request.id}")
    
    try:
        # 非同期処理を同期的に実行
        result = asyncio.run(async_fetch_announcement_data())
        
        if result["status"] == "success":
            logger.info(f"Task {self.request.id} completed successfully")
        else:
            logger.error(f"Task {self.request.id} failed: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Task {self.request.id} error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Task execution failed",
        }