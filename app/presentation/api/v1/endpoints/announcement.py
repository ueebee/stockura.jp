"""決算発表予定 API エンドポイント"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.fetch_announcement import FetchAnnouncementUseCase
from app.core.logger import get_logger
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.repositories.announcement_repository_impl import AnnouncementRepositoryImpl

logger = get_logger(__name__)
router = APIRouter()


async def get_fetch_announcement_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> FetchAnnouncementUseCase:
    """FetchAnnouncement ユースケースの依存性注入"""
    client_factory = JQuantsClientFactory()
    announcement_client = await client_factory.create_announcement_client()
    announcement_repository = AnnouncementRepositoryImpl(session)
    
    return FetchAnnouncementUseCase(
        announcement_client=announcement_client,
        announcement_repository=announcement_repository,
    )


@router.post("/refresh", summary="決算発表予定データを更新")
async def refresh_announcements(
    use_case: FetchAnnouncementUseCase = Depends(get_fetch_announcement_use_case),
):
    """J-Quants API から最新の決算発表予定データを取得して更新"""
    try:
        result = await use_case.fetch_and_save_announcements()
        return {
            "message": "Announcements refreshed successfully",
            "total_count": result.total_count,
        }
    except Exception as e:
        logger.error(f"Failed to refresh announcements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="決算発表予定一覧を取得")
async def get_announcements(
    date: Optional[date] = Query(None, description="発表日（YYYY-MM-DD 形式）"),
    code: Optional[str] = Query(None, description="銘柄コード（4 桁）"),
    use_case: FetchAnnouncementUseCase = Depends(get_fetch_announcement_use_case),
):
    """条件に基づいて決算発表予定一覧を取得"""
    try:
        if date and code:
            # 特定の日付と銘柄コードで検索
            announcement = await use_case.get_announcement(date, code)
            if not announcement:
                raise HTTPException(status_code=404, detail="Announcement not found")
            return {"announcements": [announcement.to_dict()], "total_count": 1}
        elif date:
            # 日付で検索
            result = await use_case.get_announcements_by_date(date)
        elif code:
            # 銘柄コードで検索
            result = await use_case.get_announcements_by_code(code)
        else:
            # 最新のデータを取得
            result = await use_case.get_latest_announcements()
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get announcements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", summary="最新の決算発表予定を取得")
async def get_latest_announcements(
    use_case: FetchAnnouncementUseCase = Depends(get_fetch_announcement_use_case),
):
    """最新の決算発表予定一覧を取得"""
    try:
        result = await use_case.get_latest_announcements()
        return result.to_dict()
    except Exception as e:
        logger.error(f"Failed to get latest announcements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}", summary="特定銘柄の決算発表予定を取得")
async def get_announcement_by_code(
    code: str,
    use_case: FetchAnnouncementUseCase = Depends(get_fetch_announcement_use_case),
):
    """指定された銘柄コードの決算発表予定履歴を取得"""
    try:
        result = await use_case.get_announcements_by_code(code)
        if result.total_count == 0:
            raise HTTPException(status_code=404, detail="No announcements found for this code")
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get announcements for code {code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))