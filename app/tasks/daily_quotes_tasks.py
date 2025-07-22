"""
株価データ同期関連のCeleryタスク
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from celery import current_task

from app.core.celery_app import celery_app
from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.daily_quotes_sync_service import DailyQuotesSyncService


@celery_app.task(bind=True)
def sync_daily_quotes_task(
    self,
    data_source_id: int,
    sync_type: str = "single_date",
    target_date: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    codes: Optional[List[str]] = None,
    execution_type: str = "manual"
) -> Dict:
    """
    株価データ同期タスク
    
    Args:
        data_source_id: J-QuantsデータソースID
        sync_type: 同期タイプ（single_date/date_range/by_code/full）
        target_date: 対象日（YYYY-MM-DD形式、single_dateの場合）
        from_date: 開始日（YYYY-MM-DD形式、date_range/by_codeの場合）
        to_date: 終了日（YYYY-MM-DD形式、date_range/by_codeの場合）
        codes: 銘柄コードリスト（by_codeの場合）
        
    Returns:
        Dict: 同期結果
    """
    print(f"Starting daily quotes sync task for data_source_id: {data_source_id}")
    
    try:
        # 進捗更新
        self.update_state(
            state='PROGRESS',
            meta={'message': f'Initializing sync service...'}
        )
        
        # 日付の変換
        target_date_obj = date.fromisoformat(target_date) if target_date else None
        from_date_obj = date.fromisoformat(from_date) if from_date else None
        to_date_obj = date.fromisoformat(to_date) if to_date else None
        
        # 非同期関数を同期的に実行
        async def _sync():
            # 各タスク実行で新しいセッションメーカーを作成
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
            from sqlalchemy.pool import NullPool
            from app.config import settings
            
            # 新しい非同期エンジンを作成
            task_async_engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                echo=False,
                future=True,
                poolclass=NullPool,  # 接続プーリングを無効化
                pool_pre_ping=True,
            )
            
            # 新しいセッションメーカーを作成
            task_session_maker = async_sessionmaker(
                task_async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            try:
                async with task_session_maker() as db:
                    # サービスの初期化
                    data_source_service = DataSourceService(db)
                    jquants_client_manager = JQuantsClientManager(data_source_service)
                    sync_service = DailyQuotesSyncService(data_source_service, jquants_client_manager)
                    
                    # 進捗更新
                    current_task.update_state(
                        state='PROGRESS',
                        meta={'message': f'Starting {sync_type} sync...'}
                    )
                    
                    # 同期実行
                    sync_history = await sync_service.sync_daily_quotes(
                        data_source_id=data_source_id,
                        sync_type=sync_type,
                        target_date=target_date_obj,
                        from_date=from_date_obj,
                        to_date=to_date_obj,
                        specific_codes=codes,
                        execution_type=execution_type
                    )
                    
                    # 結果を辞書形式で返す
                    if sync_history:
                        return {
                            'sync_history_id': sync_history.id,
                            'status': sync_history.status,
                            'sync_type': sync_history.sync_type,
                            'from_date': sync_history.from_date.isoformat() if sync_history.from_date else None,
                            'to_date': sync_history.to_date.isoformat() if sync_history.to_date else None,
                            'total_records': sync_history.total_records,
                            'new_records': sync_history.new_records,
                            'updated_records': sync_history.updated_records,
                            'skipped_records': sync_history.skipped_records,
                            'error_message': sync_history.error_message,
                            'started_at': sync_history.started_at.isoformat(),
                            'completed_at': sync_history.completed_at.isoformat() if sync_history.completed_at else None
                        }
                    else:
                        raise Exception("Sync history creation failed")
            finally:
                # エンジンをクリーンアップ
                await task_async_engine.dispose()
        
        # 非同期処理を実行（新しいイベントループを作成）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_sync())
        finally:
            loop.close()
        
        print(f"Daily quotes sync completed: {result}")
        return result
        
    except Exception as e:
        print(f"Error in sync_daily_quotes_task: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー情報を含めて返す
        return {
            'error': str(e),
            'status': 'failed',
            'sync_type': sync_type,
            'data_source_id': data_source_id
        }


@celery_app.task(bind=True)
def daily_quotes_cleanup_task(self, days_to_keep: int = 365) -> Dict:
    """
    古い株価データをクリーンアップするタスク
    
    Args:
        days_to_keep: 保持する日数（デフォルト: 365日）
        
    Returns:
        Dict: クリーンアップ結果
    """
    print(f"Starting daily quotes cleanup task (keeping {days_to_keep} days)")
    
    try:
        # 進捗更新
        self.update_state(
            state='PROGRESS',
            meta={'message': 'Starting cleanup...'}
        )
        
        # 非同期関数を同期的に実行
        async def _cleanup():
            # 各タスク実行で新しいセッションメーカーを作成
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
            from sqlalchemy.pool import NullPool
            from app.config import settings
            
            # 新しい非同期エンジンを作成
            task_async_engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                echo=False,
                future=True,
                poolclass=NullPool,  # 接続プーリングを無効化
                pool_pre_ping=True,
            )
            
            # 新しいセッションメーカーを作成
            task_session_maker = async_sessionmaker(
                task_async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            try:
                async with task_session_maker() as db:
                    from sqlalchemy import delete
                    from app.models.daily_quote import DailyQuote
                    
                    # 削除対象の日付を計算
                    cutoff_date = date.today() - timedelta(days=days_to_keep)
                    
                    # 削除前のレコード数を取得
                    from sqlalchemy import select, func
                    result = await db.execute(
                        select(func.count(DailyQuote.id))
                        .where(DailyQuote.trade_date < cutoff_date)
                    )
                    records_to_delete = result.scalar()
                    
                    # 削除実行
                    if records_to_delete > 0:
                        await db.execute(
                            delete(DailyQuote)
                            .where(DailyQuote.trade_date < cutoff_date)
                        )
                        await db.commit()
                    
                    return {
                        'records_deleted': records_to_delete,
                        'cutoff_date': cutoff_date.isoformat(),
                        'status': 'success'
                    }
            finally:
                # エンジンをクリーンアップ
                await task_async_engine.dispose()
        
        # 非同期処理を実行（新しいイベントループを作成）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_cleanup())
        finally:
            loop.close()
        
        print(f"Daily quotes cleanup completed: {result}")
        return result
        
    except Exception as e:
        print(f"Error in daily_quotes_cleanup_task: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'error': str(e),
            'status': 'failed'
        }


@celery_app.task
def daily_quotes_health_check() -> Dict:
    """
    株価データの健全性チェックタスク
    
    Returns:
        Dict: チェック結果
    """
    print("Starting daily quotes health check")
    
    try:
        # 非同期関数を同期的に実行
        async def _check():
            # 各タスク実行で新しいセッションメーカーを作成
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
            from sqlalchemy.pool import NullPool
            from app.config import settings
            
            # 新しい非同期エンジンを作成
            task_async_engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                echo=False,
                future=True,
                poolclass=NullPool,  # 接続プーリングを無効化
                pool_pre_ping=True,
            )
            
            # 新しいセッションメーカーを作成
            task_session_maker = async_sessionmaker(
                task_async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            try:
                async with task_session_maker() as db:
                    from sqlalchemy import select, func
                    from app.models.daily_quote import DailyQuote
                    from app.models.company import Company
                    
                    # 1. 総レコード数
                    result = await db.execute(select(func.count(DailyQuote.id)))
                    total_records = result.scalar()
                    
                    # 2. 最新の取引日
                    result = await db.execute(select(func.max(DailyQuote.trade_date)))
                    latest_date = result.scalar()
                    
                    # 3. 最古の取引日
                    result = await db.execute(select(func.min(DailyQuote.trade_date)))
                    oldest_date = result.scalar()
                    
                    # 4. ユニークな銘柄数
                    result = await db.execute(
                        select(func.count(func.distinct(DailyQuote.code)))
                    )
                    unique_codes = result.scalar()
                    
                    # 5. アクティブな企業数
                    result = await db.execute(
                        select(func.count(Company.id))
                        .where(Company.is_active == True)
                    )
                    active_companies = result.scalar()
                    
                    return {
                        'status': 'healthy',
                        'total_records': total_records,
                        'latest_date': latest_date.isoformat() if latest_date else None,
                        'oldest_date': oldest_date.isoformat() if oldest_date else None,
                        'unique_codes': unique_codes,
                        'active_companies': active_companies,
                        'coverage_rate': f"{(unique_codes / active_companies * 100):.1f}%" if active_companies > 0 else "0%",
                        'checked_at': datetime.now().isoformat()
                    }
            finally:
                # エンジンをクリーンアップ
                await task_async_engine.dispose()
        
        # 非同期処理を実行（新しいイベントループを作成）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_check())
        finally:
            loop.close()
        
        print(f"Daily quotes health check completed: {result}")
        return result
        
    except Exception as e:
        print(f"Error in daily_quotes_health_check: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'status': 'unhealthy',
            'error': str(e),
            'checked_at': datetime.now().isoformat()
        }


@celery_app.task(bind=True, name="sync_daily_quotes_scheduled")
def sync_daily_quotes_scheduled(
    self,
    schedule_id: int,
    sync_type: str,
    data_source_id: int,
    relative_preset: Optional[str] = None
) -> Dict:
    """
    定期実行用の株価データ同期タスク
    
    Args:
        schedule_id: スケジュールID
        sync_type: 同期タイプ（full/incremental）
        data_source_id: データソースID
        relative_preset: 相対日付プリセット（last7days等）
        
    Returns:
        Dict: 同期結果
    """
    print(f"Starting scheduled daily quotes sync for schedule_id: {schedule_id}")
    
    try:
        # 日付を計算
        from app.services.daily_quotes_schedule_service import DailyQuotesScheduleService
        import pytz
        
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)
        
        # 相対日付から実際の日付を計算
        if relative_preset:
            service = DailyQuotesScheduleService(None)  # 日付計算のみなのでDBは不要
            from_date, to_date = service.calculate_dates_from_preset(relative_preset, now)
            
            # 通常のタスクを同期的に実行
            # apply()を使って同期実行（throwパラメータでエラーを伝播）
            task_result = sync_daily_quotes_task.apply(
                args=[data_source_id, sync_type],
                kwargs={
                    'target_date': to_date.isoformat() if sync_type == 'incremental' else None,
                    'from_date': from_date.isoformat() if sync_type == 'full' else None,
                    'to_date': to_date.isoformat() if sync_type == 'full' else None,
                    'codes': None,
                    'execution_type': 'scheduled'
                },
                throw=True
            )
            return task_result.result
        else:
            # プリセットなしの場合は昨日のデータを取得
            yesterday = (now - timedelta(days=1)).date()
            task_result = sync_daily_quotes_task.apply(
                args=[data_source_id, sync_type],
                kwargs={
                    'target_date': yesterday.isoformat() if sync_type == 'incremental' else None,
                    'from_date': yesterday.isoformat() if sync_type == 'full' else None,
                    'to_date': yesterday.isoformat() if sync_type == 'full' else None,
                    'codes': None,
                    'execution_type': 'scheduled'
                },
                throw=True
            )
            return task_result.result
            
    except Exception as e:
        print(f"Error in sync_daily_quotes_scheduled: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'error': str(e),
            'status': 'failed',
            'schedule_id': schedule_id
        }