"""投資部門別売買状況 API エンドポイント"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.trades_spec_dto import FetchTradesSpecResult, TradesSpecDTO
from app.application.use_cases.fetch_trades_spec import FetchTradesSpecUseCase
from app.domain.repositories.trades_spec_repository import TradesSpecRepository
from app.infrastructure.database.connection import get_session as get_async_session
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.jquants.trades_spec_client import TradesSpecClient
from app.infrastructure.repositories.trades_spec_repository_impl import TradesSpecRepositoryImpl

router = APIRouter()


class FetchTradesSpecRequest(BaseModel):
    """投資部門別売買状況取得リクエスト"""
    section: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    max_pages: Optional[int] = None


class FetchTradesSpecResponse(BaseModel):
    """投資部門別売買状況取得レスポンス"""
    success: bool
    fetched_count: int
    saved_count: int
    section: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    error_message: Optional[str] = None
    
    @classmethod
    def from_result(cls, result: FetchTradesSpecResult) -> "FetchTradesSpecResponse":
        """結果 DTO からレスポンスを作成"""
        return cls(
            success=result.success,
            fetched_count=result.fetched_count,
            saved_count=result.saved_count,
            section=result.section,
            from_date=result.from_date,
            to_date=result.to_date,
            error_message=result.error_message,
        )


class TradesSpecResponse(BaseModel):
    """投資部門別売買状況レスポンス"""
    code: str
    trade_date: date
    section: Optional[str] = None
    sales_proprietary: Optional[int] = None
    purchases_proprietary: Optional[int] = None
    balance_proprietary: Optional[int] = None
    sales_consignment_individual: Optional[int] = None
    purchases_consignment_individual: Optional[int] = None
    balance_consignment_individual: Optional[int] = None
    sales_consignment_corporate: Optional[int] = None
    purchases_consignment_corporate: Optional[int] = None
    balance_consignment_corporate: Optional[int] = None
    sales_consignment_investment_trust: Optional[int] = None
    purchases_consignment_investment_trust: Optional[int] = None
    balance_consignment_investment_trust: Optional[int] = None
    sales_consignment_foreign: Optional[int] = None
    purchases_consignment_foreign: Optional[int] = None
    balance_consignment_foreign: Optional[int] = None
    sales_consignment_other_corporate: Optional[int] = None
    purchases_consignment_other_corporate: Optional[int] = None
    balance_consignment_other_corporate: Optional[int] = None
    sales_consignment_other: Optional[int] = None
    purchases_consignment_other: Optional[int] = None
    balance_consignment_other: Optional[int] = None
    sales_total: Optional[int] = None
    purchases_total: Optional[int] = None
    balance_total: Optional[int] = None


async def get_trades_spec_client() -> TradesSpecClient:
    """TradesSpec クライアントの依存性注入"""
    factory = JQuantsClientFactory()
    client = await factory.create_trades_spec_client()
    return client


async def get_trades_spec_repository(
    session: AsyncSession = Depends(get_async_session),
) -> TradesSpecRepository:
    """TradesSpec リポジトリの依存性注入"""
    return TradesSpecRepositoryImpl(session)


async def get_fetch_trades_spec_use_case(
    client: TradesSpecClient = Depends(get_trades_spec_client),
    repository: TradesSpecRepository = Depends(get_trades_spec_repository),
) -> FetchTradesSpecUseCase:
    """FetchTradesSpec ユースケースの依存性注入"""
    return FetchTradesSpecUseCase(client, repository)


@router.post("/fetch", response_model=FetchTradesSpecResponse)
async def fetch_trades_spec(
    request: FetchTradesSpecRequest,
    use_case: FetchTradesSpecUseCase = Depends(get_fetch_trades_spec_use_case),
) -> FetchTradesSpecResponse:
    """投資部門別売買状況を取得してデータベースに保存
    
    Args:
        request: 取得条件
        use_case: FetchTradesSpec ユースケース
        
    Returns:
        取得結果
    """
    result = await use_case.execute(
        section=request.section,
        from_date=request.from_date,
        to_date=request.to_date,
        max_pages=request.max_pages,
    )
    
    return FetchTradesSpecResponse.from_result(result)


@router.get("/search", response_model=list[TradesSpecResponse])
async def search_trades_spec(
    code: Optional[str] = Query(None, description="銘柄コード"),
    trade_date: Optional[date] = Query(None, description="取引日"),
    from_date: Optional[date] = Query(None, description="開始日"),
    to_date: Optional[date] = Query(None, description="終了日"),
    section: Optional[str] = Query(None, description="市場区分"),
    repository: TradesSpecRepository = Depends(get_trades_spec_repository),
) -> list[TradesSpecResponse]:
    """投資部門別売買状況を検索
    
    Args:
        code: 銘柄コード
        trade_date: 取引日（単一日付検索）
        from_date: 開始日（範囲検索用）
        to_date: 終了日（範囲検索用）
        section: 市場区分
        repository: TradesSpec リポジトリ
        
    Returns:
        検索結果
    """
    trades_specs = []
    
    try:
        if code and trade_date:
            # 銘柄コードと日付で検索
            spec = await repository.find_by_code_and_date(code, trade_date)
            if spec:
                trades_specs = [spec]
                
        elif code and from_date and to_date:
            # 銘柄コードと日付範囲で検索
            trades_specs = await repository.find_by_code_and_date_range(
                code, from_date, to_date
            )
            
        elif trade_date:
            # 日付と市場区分で検索
            trades_specs = await repository.find_by_date_and_section(
                trade_date, section
            )
            
        elif from_date and to_date:
            # 日付範囲と市場区分で検索
            trades_specs = await repository.find_by_date_range_and_section(
                from_date, to_date, section
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="検索条件を指定してください（銘柄コード、日付、日付範囲など）"
            )
            
        # エンティティをレスポンスに変換
        return [
            TradesSpecResponse(
                code=spec.code,
                trade_date=spec.trade_date,
                section=spec.section,
                sales_proprietary=spec.sales_proprietary,
                purchases_proprietary=spec.purchases_proprietary,
                balance_proprietary=spec.balance_proprietary,
                sales_consignment_individual=spec.sales_consignment_individual,
                purchases_consignment_individual=spec.purchases_consignment_individual,
                balance_consignment_individual=spec.balance_consignment_individual,
                sales_consignment_corporate=spec.sales_consignment_corporate,
                purchases_consignment_corporate=spec.purchases_consignment_corporate,
                balance_consignment_corporate=spec.balance_consignment_corporate,
                sales_consignment_investment_trust=spec.sales_consignment_investment_trust,
                purchases_consignment_investment_trust=spec.purchases_consignment_investment_trust,
                balance_consignment_investment_trust=spec.balance_consignment_investment_trust,
                sales_consignment_foreign=spec.sales_consignment_foreign,
                purchases_consignment_foreign=spec.purchases_consignment_foreign,
                balance_consignment_foreign=spec.balance_consignment_foreign,
                sales_consignment_other_corporate=spec.sales_consignment_other_corporate,
                purchases_consignment_other_corporate=spec.purchases_consignment_other_corporate,
                balance_consignment_other_corporate=spec.balance_consignment_other_corporate,
                sales_consignment_other=spec.sales_consignment_other,
                purchases_consignment_other=spec.purchases_consignment_other,
                balance_consignment_other=spec.balance_consignment_other,
                sales_total=spec.sales_total,
                purchases_total=spec.purchases_total,
                balance_total=spec.balance_total,
            )
            for spec in trades_specs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"検索中にエラーが発生しました: {str(e)}"
        )