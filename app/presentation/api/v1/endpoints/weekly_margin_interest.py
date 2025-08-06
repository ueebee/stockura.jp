"""週次信用取引残高 API エンドポイント"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.weekly_margin_interest_dto import (
    FetchWeeklyMarginInterestResult,
    WeeklyMarginInterestDTO,
)
from app.application.use_cases.fetch_weekly_margin_interest import (
    FetchWeeklyMarginInterestUseCase,
)
from app.domain.repositories import WeeklyMarginInterestRepository
from app.infrastructure.database.connection import get_session as get_async_session
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.jquants.weekly_margin_interest_client import (
    WeeklyMarginInterestClient,
)
from app.infrastructure.repositories.weekly_margin_interest_repository_impl import (
    WeeklyMarginInterestRepositoryImpl,
)

router = APIRouter()


class FetchWeeklyMarginInterestRequest(BaseModel):
    """週次信用取引残高取得リクエスト"""

    code: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class FetchWeeklyMarginInterestResponse(BaseModel):
    """週次信用取引残高取得レスポンス"""

    success: bool
    fetched_count: int
    saved_count: int
    code: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    error_message: Optional[str] = None

    @classmethod
    def from_result(
        cls, result: FetchWeeklyMarginInterestResult
    ) -> "FetchWeeklyMarginInterestResponse":
        """結果 DTO からレスポンスを作成"""
        return cls(
            success=result.success,
            fetched_count=result.fetched_count,
            saved_count=result.saved_count,
            code=result.code,
            from_date=result.from_date,
            to_date=result.to_date,
            error_message=result.error_message,
        )


class WeeklyMarginInterestResponse(BaseModel):
    """週次信用取引残高レスポンス"""

    code: str
    date: date
    short_margin_trade_volume: Optional[float] = None
    long_margin_trade_volume: Optional[float] = None
    short_negotiable_margin_trade_volume: Optional[float] = None
    long_negotiable_margin_trade_volume: Optional[float] = None
    short_standardized_margin_trade_volume: Optional[float] = None
    long_standardized_margin_trade_volume: Optional[float] = None
    issue_type: Optional[str] = None


async def get_weekly_margin_interest_client() -> WeeklyMarginInterestClient:
    """WeeklyMarginInterest クライアントの依存性注入"""
    factory = JQuantsClientFactory()
    client = await factory.create_weekly_margin_interest_client()
    return client


async def get_weekly_margin_interest_repository(
    session: AsyncSession = Depends(get_async_session),
) -> WeeklyMarginInterestRepository:
    """WeeklyMarginInterest リポジトリの依存性注入"""
    return WeeklyMarginInterestRepositoryImpl(session)


async def get_fetch_weekly_margin_interest_use_case(
    client: WeeklyMarginInterestClient = Depends(get_weekly_margin_interest_client),
    repository: WeeklyMarginInterestRepository = Depends(
        get_weekly_margin_interest_repository
    ),
) -> FetchWeeklyMarginInterestUseCase:
    """FetchWeeklyMarginInterest ユースケースの依存性注入"""
    return FetchWeeklyMarginInterestUseCase(client, repository)


@router.post("/fetch", response_model=FetchWeeklyMarginInterestResponse)
async def fetch_weekly_margin_interest(
    request: FetchWeeklyMarginInterestRequest,
    use_case: FetchWeeklyMarginInterestUseCase = Depends(
        get_fetch_weekly_margin_interest_use_case
    ),
) -> FetchWeeklyMarginInterestResponse:
    """週次信用取引残高を取得してデータベースに保存

    Args:
        request: 取得条件
        use_case: FetchWeeklyMarginInterest ユースケース

    Returns:
        取得結果
    """
    result = await use_case.execute(
        code=request.code,
        from_date=request.from_date,
        to_date=request.to_date,
    )

    return FetchWeeklyMarginInterestResponse.from_result(result)


@router.get("/search", response_model=List[WeeklyMarginInterestResponse])
async def search_weekly_margin_interest(
    code: Optional[str] = Query(None, description="銘柄コード"),
    date: Optional[date] = Query(None, description="週末日付"),
    from_date: Optional[date] = Query(None, description="開始日"),
    to_date: Optional[date] = Query(None, description="終了日"),
    issue_type: Optional[str] = Query(
        None, description="銘柄種別（1: 貸借銘柄, 2: 貸借融資銘柄, 3: その他）"
    ),
    repository: WeeklyMarginInterestRepository = Depends(
        get_weekly_margin_interest_repository
    ),
) -> List[WeeklyMarginInterestResponse]:
    """週次信用取引残高を検索

    Args:
        code: 銘柄コード
        date: 週末日付（単一日付検索）
        from_date: 開始日（範囲検索用）
        to_date: 終了日（範囲検索用）
        issue_type: 銘柄種別
        repository: WeeklyMarginInterest リポジトリ

    Returns:
        検索結果
    """
    weekly_margin_interests = []

    try:
        if code and date:
            # 銘柄コードと日付で検索
            wmi = await repository.find_by_code_and_date(code, date)
            if wmi:
                weekly_margin_interests = [wmi]

        elif code and from_date and to_date:
            # 銘柄コードと日付範囲で検索
            weekly_margin_interests = await repository.find_by_code_and_date_range(
                code, from_date, to_date
            )

        elif date:
            # 日付で検索
            weekly_margin_interests = await repository.find_by_date(date)

        elif from_date and to_date:
            # 日付範囲で検索
            weekly_margin_interests = await repository.find_by_date_range(
                from_date, to_date
            )

        elif issue_type:
            # 銘柄種別で検索
            weekly_margin_interests = await repository.find_by_issue_type(
                issue_type, from_date, to_date
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="検索条件を指定してください（銘柄コード、日付、日付範囲、銘柄種別など）",
            )

        # エンティティをレスポンスに変換
        return [
            WeeklyMarginInterestResponse(
                code=wmi.code,
                date=wmi.date,
                short_margin_trade_volume=wmi.short_margin_trade_volume,
                long_margin_trade_volume=wmi.long_margin_trade_volume,
                short_negotiable_margin_trade_volume=wmi.short_negotiable_margin_trade_volume,
                long_negotiable_margin_trade_volume=wmi.long_negotiable_margin_trade_volume,
                short_standardized_margin_trade_volume=wmi.short_standardized_margin_trade_volume,
                long_standardized_margin_trade_volume=wmi.long_standardized_margin_trade_volume,
                issue_type=wmi.issue_type,
            )
            for wmi in weekly_margin_interests
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"検索中にエラーが発生しました: {str(e)}"
        )
