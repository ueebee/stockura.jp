"""
日次株価データフェッチャー実装

J-Quants APIからの株価データ取得を担当
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import date, timedelta

from app.services.interfaces.daily_quotes_sync_interfaces import (
    IDailyQuotesDataFetcher,
    DataFetchError,
    RateLimitError
)
from app.services.jquants_client import JQuantsClientManager
from app.core.exceptions import APIError, DataSourceNotFoundError

logger = logging.getLogger(__name__)


class DailyQuotesDataFetcher(IDailyQuotesDataFetcher):
    """日次株価データフェッチャー"""
    
    def __init__(
        self,
        jquants_client_manager: JQuantsClientManager,
        data_source_id: int
    ):
        """
        初期化
        
        Args:
            jquants_client_manager: J-Quantsクライアント管理
            data_source_id: データソースID
        """
        self.jquants_client_manager = jquants_client_manager
        self.data_source_id = data_source_id
        self._client = None
        
        # レート制限設定（5000req/5min = 約16.7req/sec）
        self._rate_limit_delay = 0.1  # 100ms間隔で安全マージンを確保
    
    async def _get_client(self):
        """J-Quantsクライアントを取得（遅延初期化）"""
        if self._client is None:
            try:
                self._client = await self.jquants_client_manager.get_client(
                    self.data_source_id
                )
            except Exception as e:
                raise DataSourceNotFoundError(
                    f"Failed to get J-Quants client for data source {self.data_source_id}: {str(e)}"
                )
        return self._client
    
    async def fetch_quotes_by_date(
        self, 
        target_date: date,
        codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        指定日の株価データを取得
        
        Args:
            target_date: 取得対象日
            codes: 銘柄コードリスト（Noneの場合は全銘柄）
            
        Returns:
            List[Dict[str, Any]]: J-Quants APIレスポンスの株価データリスト
            
        Raises:
            DataFetchError: データ取得に失敗した場合
            RateLimitError: レート制限に達した場合
        """
        client = await self._get_client()
        
        try:
            if codes:
                # 特定銘柄の取得（銘柄ごとに個別リクエスト）
                all_quotes = []
                for code in codes:
                    try:
                        quotes = await client.get_daily_quotes(
                            code=code,
                            target_date=target_date
                        )
                        all_quotes.extend(quotes)
                        
                        # レート制限対策
                        await asyncio.sleep(self._rate_limit_delay)
                        
                    except Exception as e:
                        logger.error(f"Error fetching data for code {code} on {target_date}: {e}")
                        # 個別銘柄のエラーは継続
                        continue
                
                return all_quotes
            else:
                # 全銘柄の取得
                quotes = await client.get_daily_quotes(target_date=target_date)
                return quotes or []
                
        except Exception as e:
            # エラーの種類に応じた例外変換
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                raise DataFetchError(
                    f"Authentication failed for J-Quants API: {error_msg}"
                )
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                raise RateLimitError(
                    "J-Quants API rate limit exceeded",
                    retry_after=60
                )
            elif "404" in error_msg:
                # データが存在しない場合は空リストを返す
                logger.info(f"No data available for date {target_date}")
                return []
            else:
                raise DataFetchError(
                    f"Failed to fetch quotes for date {target_date}: {error_msg}"
                )
    
    async def fetch_quotes_by_date_range(
        self,
        from_date: date,
        to_date: date,
        codes: Optional[List[str]] = None
    ) -> Dict[date, List[Dict[str, Any]]]:
        """
        日付範囲の株価データを取得
        
        Args:
            from_date: 開始日
            to_date: 終了日
            codes: 銘柄コードリスト（Noneの場合は全銘柄）
            
        Returns:
            Dict[date, List[Dict[str, Any]]]: 日付をキーとした株価データ辞書
            
        Raises:
            DataFetchError: データ取得に失敗した場合
            RateLimitError: レート制限に達した場合
        """
        result = {}
        current_date = from_date
        
        # 日付範囲の検証
        if from_date > to_date:
            raise DataFetchError(
                f"Invalid date range: from_date ({from_date}) > to_date ({to_date})"
            )
        
        # 期間が長すぎる場合の警告
        days_diff = (to_date - from_date).days
        if days_diff > 365:
            logger.warning(f"Large date range requested: {days_diff} days")
        
        while current_date <= to_date:
            try:
                # 各日付のデータを取得
                quotes = await self.fetch_quotes_by_date(current_date, codes)
                if quotes:
                    result[current_date] = quotes
                
                # レート制限対策
                await asyncio.sleep(self._rate_limit_delay)
                
            except RateLimitError as e:
                # レート制限エラーの場合は待機後にリトライ
                logger.warning(f"Rate limit reached, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after or 60)
                # 同じ日付でリトライ
                continue
                
            except DataFetchError as e:
                # その他のエラーは記録して次の日付へ
                logger.error(f"Error fetching data for {current_date}: {e}")
                # エラーでも処理を継続
                
            current_date += timedelta(days=1)
        
        return result