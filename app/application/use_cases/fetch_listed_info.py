"""Fetch listed info use case."""
import asyncio
from datetime import date
from logging import Logger
from typing import List, Optional

from app.application.dtos.listed_info_dto import FetchListedInfoResult, ListedInfoDTO
from app.domain.entities.listed_info import JQuantsListedInfo
from app.domain.exceptions.listed_info_exceptions import (
    ListedInfoAPIError,
    ListedInfoDataError,
    ListedInfoStorageError,
)
from app.application.interfaces.external.listed_info_client import ListedInfoClientInterface
from app.domain.repositories.listed_info_repository_interface import ListedInfoRepositoryInterface


class FetchListedInfoUseCase:
    """上場銘柄情報を取得して保存するユースケース"""

    def __init__(
        self,
        jquants_client: ListedInfoClientInterface,
        listed_info_repository: ListedInfoRepositoryInterface,
        logger: Logger,
    ):
        """Initialize use case.

        Args:
            jquants_client: Listed info client interface
            listed_info_repository: Listed info repository
            logger: Logger instance
        """
        self._jquants_client = jquants_client
        self._listed_info_repository = listed_info_repository
        self._logger = logger

    async def execute(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None,
    ) -> FetchListedInfoResult:
        """上場銘柄情報を取得して保存

        Args:
            code: 銘柄コード（特定銘柄のみ取得する場合）
            target_date: 基準日（指定しない場合は最新）

        Returns:
            FetchListedInfoResult: 処理結果
        """
        fetched_count = 0
        saved_count = 0

        try:
            # 日付のフォーマット
            date_param = None
            if target_date:
                date_param = target_date.strftime("%Y%m%d")

            self._logger.info(
                f"Fetching listed info - code: {code}, date: {date_param}"
            )

            # API から情報取得
            if code:
                # 特定銘柄の情報取得
                api_data = await self._jquants_client.get_listed_info(
                    code=code, date=date_param
                )
            else:
                # 全銘柄の情報取得（ページネーション対応）
                api_data = await self._jquants_client.get_all_listed_info(
                    date=date_param
                )

            fetched_count = len(api_data)
            self._logger.info(f"Fetched {fetched_count} records from API")
            
            # デバッグ用に API レスポンスの一部をログ出力
            if api_data:
                self._logger.debug(f"First API response: {api_data[0]}")

            if fetched_count == 0:
                return FetchListedInfoResult(
                    success=True,
                    fetched_count=0,
                    saved_count=0,
                    target_date=target_date,
                    code=code,
                )

            # DTO に変換
            dtos = [ListedInfoDTO.from_api_response(data) for data in api_data]

            # エンティティに変換
            entities = [dto.to_entity() for dto in dtos]

            # バッチ処理でデータベースに保存
            batch_size = 1000
            for i in range(0, len(entities), batch_size):
                batch = entities[i : i + batch_size]
                await self._listed_info_repository.save_all(batch)
                saved_count += len(batch)
                self._logger.info(
                    f"Saved batch {i // batch_size + 1} - {len(batch)} records"
                )

            self._logger.info(
                f"Successfully saved {saved_count} listed info records"
            )

            return FetchListedInfoResult(
                success=True,
                fetched_count=fetched_count,
                saved_count=saved_count,
                target_date=target_date,
                code=code,
            )

        except ListedInfoAPIError as e:
            self._logger.error(f"API error occurred: {str(e)}")
            return FetchListedInfoResult(
                success=False,
                fetched_count=fetched_count,
                saved_count=saved_count,
                error_message=f"API error: {str(e)}",
                target_date=target_date,
                code=code,
            )

        except ListedInfoDataError as e:
            self._logger.error(f"Data error occurred: {str(e)}")
            return FetchListedInfoResult(
                success=False,
                fetched_count=fetched_count,
                saved_count=saved_count,
                error_message=f"Data error: {str(e)}",
                target_date=target_date,
                code=code,
            )

        except ListedInfoStorageError as e:
            self._logger.error(f"Storage error occurred: {str(e)}")
            return FetchListedInfoResult(
                success=False,
                fetched_count=fetched_count,
                saved_count=saved_count,
                error_message=f"Storage error: {str(e)}",
                target_date=target_date,
                code=code,
            )

        except Exception as e:
            self._logger.error(f"Unexpected error occurred: {str(e)}")
            return FetchListedInfoResult(
                success=False,
                fetched_count=fetched_count,
                saved_count=saved_count,
                error_message=f"Unexpected error: {str(e)}",
                target_date=target_date,
                code=code,
            )

    async def fetch_and_update_all(self, target_date: Optional[date] = None) -> FetchListedInfoResult:
        """全銘柄の上場情報を取得して更新

        Args:
            target_date: 基準日（指定しない場合は最新）

        Returns:
            FetchListedInfoResult: 処理結果
        """
        return await self.execute(code=None, target_date=target_date)

    async def fetch_by_code(self, code: str, target_date: Optional[date] = None) -> FetchListedInfoResult:
        """特定銘柄の上場情報を取得

        Args:
            code: 銘柄コード
            target_date: 基準日（指定しない場合は最新）

        Returns:
            FetchListedInfoResult: 処理結果
        """
        return await self.execute(code=code, target_date=target_date)