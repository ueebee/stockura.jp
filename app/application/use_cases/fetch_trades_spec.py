"""投資部門別売買状況取得ユースケース"""
from datetime import date
from typing import Optional
from structlog import get_logger

from app.application.dtos.trades_spec_dto import FetchTradesSpecResult
from app.domain.repositories.trades_spec_repository import TradesSpecRepository
from app.infrastructure.jquants.trades_spec_client import TradesSpecClient

logger = get_logger()


class FetchTradesSpecUseCase:
    """投資部門別売買状況を取得して保存するユースケース"""
    
    def __init__(
        self,
        trades_spec_client: TradesSpecClient,
        trades_spec_repository: TradesSpecRepository,
    ):
        """ユースケースを初期化
        
        Args:
            trades_spec_client: TradesSpec API クライアント
            trades_spec_repository: TradesSpec リポジトリ
        """
        self._trades_spec_client = trades_spec_client
        self._trades_spec_repository = trades_spec_repository
    
    async def execute(
        self,
        section: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        max_pages: Optional[int] = None,
    ) -> FetchTradesSpecResult:
        """投資部門別売買状況を取得して保存
        
        Args:
            section: 市場区分（例："TSEPrime"）
            from_date: 開始日
            to_date: 終了日
            max_pages: 最大取得ページ数
            
        Returns:
            FetchTradesSpecResult: 処理結果
        """
        fetched_count = 0
        saved_count = 0
        
        try:
            logger.info(
                "Fetching trades spec data",
                section=section,
                from_date=from_date,
                to_date=to_date,
                max_pages=max_pages,
            )
            
            # API から投資部門別売買状況データを取得
            trades_specs = await self._trades_spec_client.fetch_all_trades_spec(
                section=section,
                from_date=from_date,
                to_date=to_date,
                max_pages=max_pages,
            )
            
            fetched_count = len(trades_specs)
            logger.info(f"Fetched {fetched_count} records from API")
            
            if fetched_count == 0:
                return FetchTradesSpecResult(
                    success=True,
                    fetched_count=0,
                    saved_count=0,
                    section=section,
                    from_date=from_date,
                    to_date=to_date,
                )
            
            # バッチ処理でデータベースに保存
            batch_size = 1000
            for i in range(0, len(trades_specs), batch_size):
                batch = trades_specs[i:i + batch_size]
                await self._trades_spec_repository.save_bulk(batch)
                saved_count += len(batch)
                logger.info(
                    f"Saved batch {i // batch_size + 1} - {len(batch)} records"
                )
            
            logger.info(
                f"Successfully saved {saved_count} trades spec records"
            )
            
            return FetchTradesSpecResult(
                success=True,
                fetched_count=fetched_count,
                saved_count=saved_count,
                section=section,
                from_date=from_date,
                to_date=to_date,
            )
            
        except Exception as e:
            logger.error(f"Error occurred while fetching trades spec: {str(e)}")
            return FetchTradesSpecResult(
                success=False,
                fetched_count=fetched_count,
                saved_count=saved_count,
                section=section,
                from_date=from_date,
                to_date=to_date,
                error_message=str(e),
            )
    
    async def fetch_by_date_range(
        self,
        from_date: date,
        to_date: date,
        section: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> FetchTradesSpecResult:
        """日付範囲で投資部門別売買状況を取得
        
        Args:
            from_date: 開始日
            to_date: 終了日
            section: 市場区分（省略可）
            max_pages: 最大取得ページ数
            
        Returns:
            FetchTradesSpecResult: 処理結果
        """
        return await self.execute(
            section=section,
            from_date=from_date,
            to_date=to_date,
            max_pages=max_pages,
        )
    
    async def fetch_by_section(
        self,
        section: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        max_pages: Optional[int] = None,
    ) -> FetchTradesSpecResult:
        """市場区分で投資部門別売買状況を取得
        
        Args:
            section: 市場区分
            from_date: 開始日（省略可）
            to_date: 終了日（省略可）
            max_pages: 最大取得ページ数
            
        Returns:
            FetchTradesSpecResult: 処理結果
        """
        return await self.execute(
            section=section,
            from_date=from_date,
            to_date=to_date,
            max_pages=max_pages,
        )
    
    async def fetch_latest(
        self,
        section: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> FetchTradesSpecResult:
        """最新の投資部門別売買状況を取得
        
        Args:
            section: 市場区分（省略可）
            max_pages: 最大取得ページ数
            
        Returns:
            FetchTradesSpecResult: 処理結果
        """
        return await self.execute(
            section=section,
            max_pages=max_pages,
        )