"""
株価データ同期サービス

J-Quants APIから株価データを取得し、データベースに保存・更新する機能を提供
"""

import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal, InvalidOperation
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, or_, func

from app.db.session import get_session, async_session_maker
from app.models.daily_quote import DailyQuote, DailyQuotesSyncHistory
from app.services.jquants_client import JQuantsClientManager, JQuantsDailyQuotesClient
from app.services.data_source_service import DataSourceService
from app.services.base_sync_service import BaseSyncService
from app.core.exceptions import (
    APIError, DataValidationError, SyncError,
    DataSourceNotFoundError, RateLimitError
)
from app.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class DailyQuotesSyncService(BaseSyncService[DailyQuotesSyncHistory]):
    """株価データ同期サービス"""
    
    def __init__(
        self,
        data_source_service: DataSourceService,
        jquants_client_manager: JQuantsClientManager,
        db: Optional[AsyncSession] = None
    ):
        """
        初期化
        
        Args:
            data_source_service: データソースサービス
            jquants_client_manager: J-Quantsクライアント管理
            db: データベースセッション（オプション）
        """
        # dbが指定されていない場合は基底クラスの初期化をスキップ
        self._has_db = db is not None
        if self._has_db:
            super().__init__(db)
        else:
            # 基底クラスを初期化せずにロガーのみ設定
            self.logger = logging.getLogger(self.__class__.__name__)
        
        self.data_source_service = data_source_service
        self.jquants_client_manager = jquants_client_manager
    
    def get_history_model(self) -> type:
        """履歴モデルクラスを返す"""
        return DailyQuotesSyncHistory
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        同期処理のエントリーポイント
        
        Args:
            **kwargs: 同期パラメータ
            
        Returns:
            Dict[str, Any]: 同期結果
        """
        # パラメータの取得
        data_source_id = kwargs['data_source_id']
        sync_type = kwargs.get('sync_type', 'full')
        target_date = kwargs.get('target_date')
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        specific_codes = kwargs.get('specific_codes')
        
        # 同期実行
        history = await self.sync_daily_quotes(
            data_source_id=data_source_id,
            sync_type=sync_type,
            target_date=target_date,
            from_date=from_date,
            to_date=to_date,
            specific_codes=specific_codes
        )
        
        return {
            "status": history.status,
            "history_id": history.id,
            "total_records": history.total_records,
            "new_records": history.new_records,
            "updated_records": history.updated_records,
            "skipped_records": history.skipped_records
        }
    
    async def sync_daily_quotes(
        self,
        data_source_id: int,
        sync_type: str = "full",
        target_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        specific_codes: Optional[List[str]] = None,
        execution_type: str = "manual"
    ) -> DailyQuotesSyncHistory:
        """
        株価データの同期を実行
        
        Args:
            data_source_id: データソースID
            sync_type: 同期タイプ（full/incremental/single_stock）
            target_date: 対象日（incremental同期時）
            from_date: 期間指定開始日（full同期時）
            to_date: 期間指定終了日（full同期時）
            specific_codes: 特定銘柄コードリスト（single_stock同期時）
            
        Returns:
            DailyQuotesSyncHistory: 同期履歴レコード
        """
        logger.info(f"Starting daily quotes sync: type={sync_type}, data_source_id={data_source_id}")
        
        # 同期履歴レコードを作成
        sync_history = DailyQuotesSyncHistory(
            sync_date=target_date or date.today(),
            sync_type=sync_type,
            status="running",
            started_at=datetime.utcnow(),
            from_date=from_date,
            to_date=to_date,
            specific_codes=json.dumps(specific_codes) if specific_codes else None,
            execution_type=execution_type
        )
        
        async with async_session_maker() as session:
            try:
                session.add(sync_history)
                await session.commit()
                await session.refresh(sync_history)
                
                # 同期タイプに応じて処理を実行
                if sync_type == "full":
                    await self._sync_full_data(session, data_source_id, sync_history, from_date, to_date)
                elif sync_type == "incremental":
                    await self._sync_incremental_data(session, data_source_id, sync_history, target_date)
                elif sync_type == "single_stock":
                    await self._sync_single_stock_data(session, data_source_id, sync_history, specific_codes, target_date)
                else:
                    raise ValueError(f"Unknown sync_type: {sync_type}")
                
                # 成功時の処理
                sync_history.status = "completed"
                sync_history.completed_at = datetime.utcnow()
                await session.commit()
                
                logger.info(f"Daily quotes sync completed successfully: {sync_history.id}")
                return sync_history
                
            except Exception as e:
                # 統一されたエラーハンドリング
                error_info = await ErrorHandler.handle_sync_error(
                    error=e,
                    service_name="DailyQuotesSyncService",
                    context={
                        "sync_type": sync_type,
                        "data_source_id": data_source_id,
                        "target_date": target_date.isoformat() if target_date else None,
                        "from_date": from_date.isoformat() if from_date else None,
                        "to_date": to_date.isoformat() if to_date else None
                    },
                    db=session,
                    sync_history_id=sync_history.id
                )
                
                sync_history.status = "failed"
                sync_history.error_message = str(e)
                sync_history.completed_at = datetime.utcnow()
                await session.commit()
                raise
    
    async def _sync_full_data(
        self,
        session: AsyncSession,
        data_source_id: int,
        sync_history: DailyQuotesSyncHistory,
        from_date: Optional[date],
        to_date: Optional[date]
    ) -> None:
        """
        全データ同期を実行
        
        Args:
            session: データベースセッション
            data_source_id: データソースID
            sync_history: 同期履歴
            from_date: 開始日
            to_date: 終了日
        """
        logger.info("Starting full data sync")
        
        # J-Quantsクライアントを取得
        try:
            client = await self.jquants_client_manager.get_daily_quotes_client(data_source_id)
        except Exception as e:
            raise DataSourceNotFoundError(data_source_id)
        
        # 日付範囲を設定（デフォルトは過去1年間）
        if not from_date:
            from_date = date.today() - timedelta(days=365)
        if not to_date:
            to_date = date.today() - timedelta(days=1)  # 前営業日まで
        
        logger.info(f"Syncing data from {from_date} to {to_date}")
        
        # 期間内の各日付について処理
        current_date = from_date
        total_new = 0
        total_updated = 0
        total_skipped = 0
        
        while current_date <= to_date:
            try:
                date_str = current_date.strftime('%Y-%m-%d')
                logger.info(f"Processing date: {date_str}")
                
                # J-QuantsAPIから当日のデータを取得
                try:
                    quotes_data = await client.get_stock_prices_by_date(date_str)
                except Exception as e:
                    if "401" in str(e) or "authentication" in str(e).lower():
                        raise APIError(
                            "J-Quants API authentication failed",
                            status_code=401,
                            details={"data_source_id": data_source_id, "date": date_str}
                        )
                    elif "429" in str(e) or "rate limit" in str(e).lower():
                        raise RateLimitError(
                            "J-Quants API rate limit exceeded",
                            retry_after=60,
                            details={"data_source_id": data_source_id, "date": date_str}
                        )
                    else:
                        raise APIError(
                            f"Failed to fetch quotes for date {date_str}: {str(e)}",
                            details={"data_source_id": data_source_id, "date": date_str}
                        )
                
                if quotes_data:
                    new, updated, skipped = await self._process_quotes_data(
                        session, quotes_data, sync_history
                    )
                    total_new += new
                    total_updated += updated
                    total_skipped += skipped
                    
                    logger.info(f"Processed {len(quotes_data)} quotes for {date_str}: new={new}, updated={updated}, skipped={skipped}")
                else:
                    logger.info(f"No data available for {date_str}")
                
                # レート制限対策（5000req/5min）
                await asyncio.sleep(0.1)
                
            except DataValidationError as e:
                # データ検証エラーは警告として記録し、処理を継続
                logger.warning(f"Data validation error for date {current_date}: {e}")
                continue
            except RateLimitError as e:
                # レート制限エラーの場合は待機後にリトライ
                logger.warning(f"Rate limit reached, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after or 60)
                continue
            except Exception as e:
                # その他のエラーはエラーハンドラーに送信して継続
                await ErrorHandler.handle_sync_error(
                    error=e,
                    service_name="DailyQuotesSyncService",
                    context={
                        "operation": "sync_full_data",
                        "date": current_date.isoformat(),
                        "data_source_id": data_source_id
                    }
                )
                # 個別日付のエラーは継続
            
            current_date += timedelta(days=1)
        
        # 統計情報を更新
        sync_history.total_records = total_new + total_updated + total_skipped
        sync_history.new_records = total_new
        sync_history.updated_records = total_updated
        sync_history.skipped_records = total_skipped
        
        logger.info(f"Full sync completed: total={sync_history.total_records}, new={total_new}, updated={total_updated}, skipped={total_skipped}")
    
    async def _sync_incremental_data(
        self,
        session: AsyncSession,
        data_source_id: int,
        sync_history: DailyQuotesSyncHistory,
        target_date: Optional[date]
    ) -> None:
        """
        増分データ同期を実行
        
        Args:
            session: データベースセッション
            data_source_id: データソースID
            sync_history: 同期履歴
            target_date: 対象日（デフォルトは前営業日）
        """
        logger.info("Starting incremental data sync")
        
        # J-Quantsクライアントを取得
        try:
            client = await self.jquants_client_manager.get_daily_quotes_client(data_source_id)
        except Exception as e:
            raise DataSourceNotFoundError(data_source_id)
        
        # 対象日を設定（デフォルトは前営業日）
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        date_str = target_date.strftime('%Y-%m-%d')
        logger.info(f"Syncing incremental data for date: {date_str}")
        
        # J-QuantsAPIから当日のデータを取得
        quotes_data = await client.get_stock_prices_by_date(date_str)
        
        if quotes_data:
            new, updated, skipped = await self._process_quotes_data(
                session, quotes_data, sync_history
            )
            
            # 統計情報を更新
            sync_history.total_records = new + updated + skipped
            sync_history.new_records = new
            sync_history.updated_records = updated
            sync_history.skipped_records = skipped
            
            logger.info(f"Incremental sync completed: total={sync_history.total_records}, new={new}, updated={updated}, skipped={skipped}")
        else:
            logger.info(f"No data available for {date_str}")
            sync_history.total_records = 0
    
    async def _sync_single_stock_data(
        self,
        session: AsyncSession,
        data_source_id: int,
        sync_history: DailyQuotesSyncHistory,
        specific_codes: Optional[List[str]],
        target_date: Optional[date]
    ) -> None:
        """
        特定銘柄のデータ同期を実行
        
        Args:
            session: データベースセッション
            data_source_id: データソースID
            sync_history: 同期履歴
            specific_codes: 対象銘柄コードリスト
            target_date: 対象日
        """
        if not specific_codes:
            raise ValueError("specific_codes is required for single_stock sync")
        
        logger.info(f"Starting single stock sync for codes: {specific_codes}")
        
        # J-Quantsクライアントを取得
        try:
            client = await self.jquants_client_manager.get_daily_quotes_client(data_source_id)
        except Exception as e:
            raise DataSourceNotFoundError(data_source_id)
        
        # 対象日を設定
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        date_str = target_date.strftime('%Y-%m-%d')
        
        # 各銘柄について処理
        all_quotes_data = []
        for code in specific_codes:
            try:
                quotes_data = await client.get_stock_prices_by_date(date_str, codes=[code])
                all_quotes_data.extend(quotes_data)
                
                # レート制限対策
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching data for code {code}: {e}")
        
        if all_quotes_data:
            new, updated, skipped = await self._process_quotes_data(
                session, all_quotes_data, sync_history
            )
            
            # 統計情報を更新
            sync_history.target_companies = len(specific_codes)
            sync_history.total_records = new + updated + skipped
            sync_history.new_records = new
            sync_history.updated_records = updated
            sync_history.skipped_records = skipped
            
            logger.info(f"Single stock sync completed: total={sync_history.total_records}, new={new}, updated={updated}, skipped={skipped}")
        else:
            logger.info("No data retrieved for specified codes")
            sync_history.total_records = 0
    
    async def _process_quotes_data(
        self,
        session: AsyncSession,
        quotes_data: List[Dict[str, Any]],
        sync_history: DailyQuotesSyncHistory
    ) -> tuple[int, int, int]:
        """
        株価データを処理してデータベースに保存
        
        Args:
            session: データベースセッション
            quotes_data: 株価データリスト
            sync_history: 同期履歴
            
        Returns:
            tuple[int, int, int]: (新規件数, 更新件数, スキップ件数)
        """
        new_count = 0
        updated_count = 0
        skipped_count = 0
        
        for quote_data in quotes_data:
            try:
                # データの妥当性チェック
                if not self._validate_quote_data(quote_data):
                    skipped_count += 1
                    continue
                
                # 企業コードの取得
                code = quote_data.get("Code")
                trade_date_str = quote_data.get("Date")
                trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d").date()
                
                # 企業マスタに存在するかチェック
                from app.models.company import Company
                company_stmt = select(Company).where(Company.code == code)
                company_result = await session.execute(company_stmt)
                company = company_result.scalar_one_or_none()
                
                if not company:
                    logger.warning(f"Company code {code} not found in master data, skipping")
                    skipped_count += 1
                    continue
                
                # 既存レコードをチェック
                stmt = select(DailyQuote).where(
                    and_(DailyQuote.code == code, DailyQuote.trade_date == trade_date)
                )
                result = await session.execute(stmt)
                existing_quote = result.scalar_one_or_none()
                
                if existing_quote:
                    # 更新
                    self._update_daily_quote(existing_quote, quote_data)
                    updated_count += 1
                else:
                    # 新規作成
                    new_quote = self._create_daily_quote(quote_data)
                    session.add(new_quote)
                    new_count += 1
                
                # 定期的にコミット（メモリ使用量を抑制）
                if (new_count + updated_count) % 100 == 0:
                    await session.commit()
                    
            except DataValidationError as e:
                # データ検証エラーは警告として記録し、処理を継続
                logger.warning(f"Data validation error for quote: {e}")
                skipped_count += 1
            except Exception as e:
                # その他のエラーはエラーハンドラーに送信
                await ErrorHandler.handle_sync_error(
                    error=e,
                    service_name="DailyQuotesSyncService",
                    context={
                        "operation": "process_quote_data",
                        "quote_code": quote_data.get("Code"),
                        "quote_date": quote_data.get("Date")
                    }
                )
                skipped_count += 1
        
        # 最終コミット
        await session.commit()
        
        return new_count, updated_count, skipped_count
    
    def _validate_quote_data(self, quote_data: Dict[str, Any]) -> bool:
        """
        株価データの妥当性をチェック
        
        Args:
            quote_data: 株価データ
            
        Returns:
            bool: 妥当性チェック結果
        """
        required_fields = ["Code", "Date"]
        
        # 必須フィールドの存在確認
        for field in required_fields:
            if field not in quote_data or quote_data[field] is None:
                raise DataValidationError(
                    f"Missing required field: {field}",
                    field=field,
                    value=None,
                    details={"quote_data": quote_data}
                )
        
        # 日付の妥当性チェック
        try:
            datetime.strptime(quote_data["Date"], "%Y-%m-%d")
        except ValueError:
            raise DataValidationError(
                f"Invalid date format: {quote_data['Date']}",
                field="Date",
                value=quote_data["Date"],
                details={"expected_format": "YYYY-MM-DD"}
            )
        
        # 四本値の論理的整合性チェック（データが存在する場合）
        if all(key in quote_data and quote_data[key] is not None for key in ["Open", "High", "Low", "Close"]):
            try:
                open_price = float(quote_data["Open"])
                high_price = float(quote_data["High"])
                low_price = float(quote_data["Low"])
                close_price = float(quote_data["Close"])
                
                if not (low_price <= open_price <= high_price and low_price <= close_price <= high_price):
                    raise DataValidationError(
                        "Invalid OHLC data: high/low prices are inconsistent",
                        field="OHLC",
                        value={
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "close": close_price
                        }
                    )
            except (ValueError, TypeError) as e:
                raise DataValidationError(
                    f"Invalid price data: {str(e)}",
                    field="price_data",
                    value=quote_data
                )
        
        return True
    
    def _create_daily_quote(self, quote_data: Dict[str, Any]) -> DailyQuote:
        """
        株価データからDailyQuoteモデルを作成
        
        Args:
            quote_data: 株価データ
            
        Returns:
            DailyQuote: 作成されたモデル
        """
        trade_date = datetime.strptime(quote_data["Date"], "%Y-%m-%d").date()
        
        return DailyQuote(
            code=quote_data["Code"],
            trade_date=trade_date,
            
            # 調整前価格データ
            open_price=self._safe_decimal(quote_data.get("Open")),
            high_price=self._safe_decimal(quote_data.get("High")),
            low_price=self._safe_decimal(quote_data.get("Low")),
            close_price=self._safe_decimal(quote_data.get("Close")),
            volume=self._safe_int(quote_data.get("Volume")),
            turnover_value=self._safe_int(quote_data.get("TurnoverValue")),
            
            # 調整後価格データ
            adjustment_factor=self._safe_decimal(quote_data.get("AdjustmentFactor", 1.0)),
            adjustment_open=self._safe_decimal(quote_data.get("AdjustmentOpen")),
            adjustment_high=self._safe_decimal(quote_data.get("AdjustmentHigh")),
            adjustment_low=self._safe_decimal(quote_data.get("AdjustmentLow")),
            adjustment_close=self._safe_decimal(quote_data.get("AdjustmentClose")),
            adjustment_volume=self._safe_int(quote_data.get("AdjustmentVolume")),
            
            # 制限フラグ
            upper_limit_flag=self._safe_bool(quote_data.get("UpperLimit", False)),
            lower_limit_flag=self._safe_bool(quote_data.get("LowerLimit", False)),
            
            # Premium限定データ
            morning_open=self._safe_decimal(quote_data.get("MorningOpen")),
            morning_high=self._safe_decimal(quote_data.get("MorningHigh")),
            morning_low=self._safe_decimal(quote_data.get("MorningLow")),
            morning_close=self._safe_decimal(quote_data.get("MorningClose")),
            morning_volume=self._safe_int(quote_data.get("MorningVolume")),
            morning_turnover_value=self._safe_int(quote_data.get("MorningTurnoverValue")),
            
            afternoon_open=self._safe_decimal(quote_data.get("AfternoonOpen")),
            afternoon_high=self._safe_decimal(quote_data.get("AfternoonHigh")),
            afternoon_low=self._safe_decimal(quote_data.get("AfternoonLow")),
            afternoon_close=self._safe_decimal(quote_data.get("AfternoonClose")),
            afternoon_volume=self._safe_int(quote_data.get("AfternoonVolume")),
            afternoon_turnover_value=self._safe_int(quote_data.get("AfternoonTurnoverValue")),
        )
    
    def _update_daily_quote(self, quote: DailyQuote, quote_data: Dict[str, Any]) -> None:
        """
        既存のDailyQuoteモデルを更新
        
        Args:
            quote: 更新対象のモデル
            quote_data: 株価データ
        """
        # 調整前価格データ
        quote.open_price = self._safe_decimal(quote_data.get("Open"))
        quote.high_price = self._safe_decimal(quote_data.get("High"))
        quote.low_price = self._safe_decimal(quote_data.get("Low"))
        quote.close_price = self._safe_decimal(quote_data.get("Close"))
        quote.volume = self._safe_int(quote_data.get("Volume"))
        quote.turnover_value = self._safe_int(quote_data.get("TurnoverValue"))
        
        # 調整後価格データ
        quote.adjustment_factor = self._safe_decimal(quote_data.get("AdjustmentFactor", 1.0))
        quote.adjustment_open = self._safe_decimal(quote_data.get("AdjustmentOpen"))
        quote.adjustment_high = self._safe_decimal(quote_data.get("AdjustmentHigh"))
        quote.adjustment_low = self._safe_decimal(quote_data.get("AdjustmentLow"))
        quote.adjustment_close = self._safe_decimal(quote_data.get("AdjustmentClose"))
        quote.adjustment_volume = self._safe_int(quote_data.get("AdjustmentVolume"))
        
        # 制限フラグ
        quote.upper_limit_flag = self._safe_bool(quote_data.get("UpperLimit", False))
        quote.lower_limit_flag = self._safe_bool(quote_data.get("LowerLimit", False))
        
        # Premium限定データ
        quote.morning_open = self._safe_decimal(quote_data.get("MorningOpen"))
        quote.morning_high = self._safe_decimal(quote_data.get("MorningHigh"))
        quote.morning_low = self._safe_decimal(quote_data.get("MorningLow"))
        quote.morning_close = self._safe_decimal(quote_data.get("MorningClose"))
        quote.morning_volume = self._safe_int(quote_data.get("MorningVolume"))
        quote.morning_turnover_value = self._safe_int(quote_data.get("MorningTurnoverValue"))
        
        quote.afternoon_open = self._safe_decimal(quote_data.get("AfternoonOpen"))
        quote.afternoon_high = self._safe_decimal(quote_data.get("AfternoonHigh"))
        quote.afternoon_low = self._safe_decimal(quote_data.get("AfternoonLow"))
        quote.afternoon_close = self._safe_decimal(quote_data.get("AfternoonClose"))
        quote.afternoon_volume = self._safe_int(quote_data.get("AfternoonVolume"))
        quote.afternoon_turnover_value = self._safe_int(quote_data.get("AfternoonTurnoverValue"))
        
        # updated_atは自動更新される
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """
        安全にDecimalに変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            Optional[Decimal]: 変換結果（変換できない場合はNone）
        """
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """
        安全にintに変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            Optional[int]: 変換結果（変換できない場合はNone）
        """
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_bool(self, value: Any) -> bool:
        """
        安全にboolに変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            bool: 変換結果
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        if isinstance(value, (int, float)):
            return bool(value)
        return False
    
    async def get_sync_history(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[DailyQuotesSyncHistory]:
        """
        同期履歴を取得
        
        Args:
            limit: 取得件数
            offset: オフセット
            status: ステータスフィルタ
            
        Returns:
            List[DailyQuotesSyncHistory]: 同期履歴リスト
        """
        # 基底クラスのメソッドが使える場合は使用
        if self._has_db and hasattr(super(), 'get_sync_history'):
            return await super().get_sync_history(limit, offset, status)
        
        # そうでない場合は独自実装
        async with async_session_maker() as session:
            stmt = select(DailyQuotesSyncHistory).order_by(DailyQuotesSyncHistory.started_at.desc())
            
            if status:
                stmt = stmt.where(DailyQuotesSyncHistory.status == status)
            
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            histories = result.scalars().all()
        return histories
    
    async def get_sync_status(self, sync_id: int) -> Optional[DailyQuotesSyncHistory]:
        """
        特定の同期履歴を取得
        
        Args:
            sync_id: 同期履歴ID
            
        Returns:
            Optional[DailyQuotesSyncHistory]: 同期履歴（見つからない場合はNone）
        """
        async with async_session_maker() as session:
            result = await session.execute(
                select(DailyQuotesSyncHistory).where(DailyQuotesSyncHistory.id == sync_id)
            )
            sync_history = result.scalar_one_or_none()
        return sync_history