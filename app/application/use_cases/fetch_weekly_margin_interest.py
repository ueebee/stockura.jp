"""週次信用取引残高取得ユースケース"""

from datetime import date
from typing import Optional

from structlog import get_logger

from app.application.dtos.weekly_margin_interest_dto import (
    FetchWeeklyMarginInterestResult,
)
from app.domain.repositories import WeeklyMarginInterestRepository
from app.infrastructure.jquants.weekly_margin_interest_client import (
    WeeklyMarginInterestClient,
)

logger = get_logger()


class FetchWeeklyMarginInterestUseCase:
    """週次信用取引残高を取得して保存するユースケース"""

    def __init__(
        self,
        weekly_margin_interest_client: WeeklyMarginInterestClient,
        weekly_margin_interest_repository: WeeklyMarginInterestRepository,
    ):
        """ユースケースを初期化

        Args:
            weekly_margin_interest_client: WeeklyMarginInterest API クライアント
            weekly_margin_interest_repository: WeeklyMarginInterest リポジトリ
        """
        self._weekly_margin_interest_client = weekly_margin_interest_client
        self._weekly_margin_interest_repository = weekly_margin_interest_repository

    async def execute(
        self,
        code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> FetchWeeklyMarginInterestResult:
        """週次信用取引残高を取得して保存

        Args:
            code: 銘柄コード（省略時は全銘柄）
            from_date: 開始日
            to_date: 終了日

        Returns:
            FetchWeeklyMarginInterestResult: 処理結果
        """
        fetched_count = 0
        saved_count = 0

        try:
            logger.info(
                "Fetching weekly margin interest data",
                code=code,
                from_date=from_date,
                to_date=to_date,
            )

            # API から週次信用取引残高データを取得
            if code:
                # 特定銘柄のデータ取得
                weekly_margin_interests = await self._weekly_margin_interest_client.fetch_weekly_margin_interest(
                    code=code,
                    from_date=from_date,
                    to_date=to_date,
                )
            else:
                # 全銘柄のデータ取得
                weekly_margin_interests = await self._weekly_margin_interest_client.fetch_all_weekly_margin_interest(
                    from_date=from_date,
                    to_date=to_date,
                )

            fetched_count = len(weekly_margin_interests)
            logger.info(f"Fetched {fetched_count} records from API")

            if fetched_count == 0:
                return FetchWeeklyMarginInterestResult(
                    success=True,
                    fetched_count=0,
                    saved_count=0,
                    code=code,
                    from_date=from_date,
                    to_date=to_date,
                )

            # バッチ処理でデータベースに保存
            batch_size = 1000
            for i in range(0, len(weekly_margin_interests), batch_size):
                batch = weekly_margin_interests[i : i + batch_size]
                await self._weekly_margin_interest_repository.save_bulk(batch)
                saved_count += len(batch)
                logger.info(f"Saved batch {i // batch_size + 1} - {len(batch)} records")

            logger.info(
                f"Successfully saved {saved_count} weekly margin interest records"
            )

            return FetchWeeklyMarginInterestResult(
                success=True,
                fetched_count=fetched_count,
                saved_count=saved_count,
                code=code,
                from_date=from_date,
                to_date=to_date,
            )

        except Exception as e:
            logger.error(
                f"Error occurred while fetching weekly margin interest: {str(e)}"
            )
            return FetchWeeklyMarginInterestResult(
                success=False,
                fetched_count=fetched_count,
                saved_count=saved_count,
                code=code,
                from_date=from_date,
                to_date=to_date,
                error_message=str(e),
            )

    async def fetch_by_date_range(
        self,
        from_date: date,
        to_date: date,
        code: Optional[str] = None,
    ) -> FetchWeeklyMarginInterestResult:
        """日付範囲で週次信用取引残高を取得

        Args:
            from_date: 開始日
            to_date: 終了日
            code: 銘柄コード（省略可）

        Returns:
            FetchWeeklyMarginInterestResult: 処理結果
        """
        return await self.execute(
            code=code,
            from_date=from_date,
            to_date=to_date,
        )

    async def fetch_by_code(
        self,
        code: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> FetchWeeklyMarginInterestResult:
        """銘柄コードで週次信用取引残高を取得

        Args:
            code: 銘柄コード
            from_date: 開始日（省略可）
            to_date: 終了日（省略可）

        Returns:
            FetchWeeklyMarginInterestResult: 処理結果
        """
        return await self.execute(
            code=code,
            from_date=from_date,
            to_date=to_date,
        )

    async def fetch_latest(
        self,
        code: Optional[str] = None,
    ) -> FetchWeeklyMarginInterestResult:
        """最新の週次信用取引残高を取得

        Args:
            code: 銘柄コード（省略可）

        Returns:
            FetchWeeklyMarginInterestResult: 処理結果
        """
        return await self.execute(code=code)
