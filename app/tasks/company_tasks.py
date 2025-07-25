"""
企業データ同期関連のCeleryタスク
"""

import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional
from celery import current_task

from app.core.celery_app import celery_app
from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.company_sync_service import CompanySyncService
from app.services.company_sync_service_v2 import CompanySyncServiceV2
from app.core.feature_flags import FeatureFlags
from app.models.api_endpoint import APIEndpointSchedule


def get_sync_service():
    """同期サービスインスタンスを取得（同期処理のため非async）"""
    # Celeryタスクは同期的に実行されるため、asyncio.run()を使用
    async def _get_service():
        db = get_db()
        data_source_service = DataSourceService(db)
        jquants_client_manager = JQuantsClientManager(data_source_service)
        return CompanySyncService(db, data_source_service, jquants_client_manager)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_get_service())
    finally:
        loop.close()


@celery_app.task(bind=True)
def sync_companies_task(
    self, 
    data_source_id: int,
    sync_date: Optional[str] = None,
    sync_type: str = "full",
    execution_type: str = "manual"
) -> Dict:
    """
    企業データ同期タスク
    
    Args:
        data_source_id: J-QuantsデータソースID
        sync_date: 同期対象日（YYYY-MM-DD形式、Noneの場合は当日）
        sync_type: 同期タイプ（full/incremental）
        
    Returns:
        Dict: 同期結果
    """
    print(f"Starting company sync task for data_source_id: {data_source_id}")
    
    try:
        # 進捗更新
        self.update_state(
            state="PROGRESS",
            meta={"message": "Initializing company sync service..."}
        )
        
        # 同期対象日を解析
        target_date = None
        if sync_date:
            try:
                target_date = datetime.strptime(sync_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format: {sync_date}. Expected YYYY-MM-DD")
        else:
            target_date = date.today()
        
        print(f"Sync date: {target_date}, sync type: {sync_type}")
        
        # 非同期処理を同期的に実行
        async def _sync():
            # 進捗更新
            self.update_state(
                state="PROGRESS",
                meta={"message": "Connecting to J-Quants API..."}
            )
            
            async with async_session_maker() as db:
                data_source_service = DataSourceService(db)
                jquants_client_manager = JQuantsClientManager(data_source_service)
                
                # フィーチャーフラグに基づいてサービスを選択
                if FeatureFlags.is_enabled("use_company_sync_service_v2"):
                    sync_service = CompanySyncServiceV2(db, data_source_service, jquants_client_manager)
                else:
                    sync_service = CompanySyncService(db, data_source_service, jquants_client_manager)
                
                # 進捗更新
                self.update_state(
                    state="PROGRESS",
                    meta={"message": f"Starting {sync_type} sync for {target_date}..."}
                )
                
                # 同期実行
                sync_history = await sync_service.sync_companies(
                    data_source_id=data_source_id,
                    sync_date=target_date,
                    sync_type=sync_type,
                    execution_type=execution_type
                )
                
                return {
                    "status": "success",
                    "sync_history_id": sync_history.id,
                    "sync_date": sync_history.sync_date.isoformat(),
                    "sync_type": sync_history.sync_type,
                    "total_companies": sync_history.total_companies,
                    "new_companies": sync_history.new_companies,
                    "updated_companies": sync_history.updated_companies,
                    "deleted_companies": sync_history.deleted_companies,
                    "started_at": sync_history.started_at.isoformat(),
                    "completed_at": sync_history.completed_at.isoformat() if sync_history.completed_at else None,
                    "message": f"Successfully synced {sync_history.total_companies} companies"
                }
        
        # 非同期処理を実行（新しいイベントループを作成）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_sync())
        finally:
            loop.close()
        
        print(f"Company sync completed successfully: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Company sync failed: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": str(e),
            "data_source_id": data_source_id,
            "sync_date": sync_date,
            "sync_type": sync_type
        }


@celery_app.task(bind=True, max_retries=3)
def sync_companies_with_retry(
    self,
    data_source_id: int,
    sync_date: Optional[str] = None,
    sync_type: str = "full"
) -> Dict:
    """
    リトライ機能付き企業データ同期タスク
    
    Args:
        data_source_id: J-QuantsデータソースID
        sync_date: 同期対象日（YYYY-MM-DD形式、Noneの場合は当日）
        sync_type: 同期タイプ（full/incremental）
        
    Returns:
        Dict: 同期結果
    """
    print(f"Company sync with retry for data_source_id: {data_source_id}")
    
    try:
        result = sync_companies_task.delay(data_source_id, sync_date, sync_type)
        return result.get()
        
    except Exception as e:
        print(f"Error in company sync, retrying... Error: {e}")
        
        # リトライ回数に応じて待機時間を調整
        retry_count = self.request.retries
        countdown = 60 * (retry_count + 1)  # 1分、2分、3分と増加
        
        raise self.retry(countdown=countdown, exc=e)


@celery_app.task(bind=True)
def sync_multiple_data_sources(self, data_source_ids: List[int], sync_date: Optional[str] = None) -> Dict:
    """
    複数のデータソースから企業データを同期
    
    Args:
        data_source_ids: J-QuantsデータソースIDのリスト
        sync_date: 同期対象日（YYYY-MM-DD形式、Noneの場合は当日）
        
    Returns:
        Dict: 全体の同期結果
    """
    print(f"Starting multi-source company sync: {data_source_ids}")
    
    results = {}
    total_sources = len(data_source_ids)
    successful_syncs = 0
    failed_syncs = 0
    
    for i, data_source_id in enumerate(data_source_ids):
        try:
            # 進捗更新
            progress = (i / total_sources) * 100
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": total_sources,
                    "progress": progress,
                    "message": f"Syncing data source {data_source_id} ({i+1}/{total_sources})"
                }
            )
            
            # 個別の同期を実行
            result = sync_companies_task.delay(data_source_id, sync_date, "full", "scheduled")
            sync_result = result.get()
            
            results[data_source_id] = sync_result
            
            if sync_result.get("status") == "success":
                successful_syncs += 1
            else:
                failed_syncs += 1
            
            print(f"Completed sync for data_source_id {data_source_id}: {sync_result.get('status')}")
            
        except Exception as e:
            failed_syncs += 1
            results[data_source_id] = {
                "status": "error",
                "error": str(e),
                "data_source_id": data_source_id
            }
            print(f"Failed sync for data_source_id {data_source_id}: {e}")
    
    return {
        "status": "completed",
        "total_sources": total_sources,
        "successful_syncs": successful_syncs,
        "failed_syncs": failed_syncs,
        "sync_date": sync_date,
        "results": results,
        "message": f"Multi-source sync completed: {successful_syncs} successful, {failed_syncs} failed"
    }


@celery_app.task(bind=True)
def daily_company_sync(self, data_source_ids: List[int]) -> Dict:
    """
    日次企業データ同期タスク（スケジュール実行用）
    
    Args:
        data_source_ids: J-QuantsデータソースIDのリスト
        
    Returns:
        Dict: 同期結果
    """
    today = date.today().isoformat()
    print(f"Running daily company sync for {today}")
    
    # 複数データソース同期を実行
    return sync_multiple_data_sources.delay(data_source_ids, today).get()


@celery_app.task(bind=True)
def test_jquants_connection(self, data_source_id: int) -> Dict:
    """
    J-Quants API接続テストタスク
    
    Args:
        data_source_id: J-QuantsデータソースID
        
    Returns:
        Dict: テスト結果
    """
    print(f"Testing J-Quants connection for data_source_id: {data_source_id}")
    
    try:
        async def _test():
            async with async_session_maker() as db:
                data_source_service = DataSourceService(db)
                jquants_client_manager = JQuantsClientManager(data_source_service)
                
                client = await jquants_client_manager.get_client(data_source_id)
                connection_ok = await client.test_connection()
                
                return {
                    "status": "success" if connection_ok else "failed",
                    "data_source_id": data_source_id,
                    "connected": connection_ok,
                    "tested_at": datetime.utcnow().isoformat(),
                    "message": "J-Quants API connection test completed"
                }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_test())
        finally:
            loop.close()
        print(f"Connection test result: {result}")
        return result
        
    except Exception as e:
        error_msg = f"J-Quants connection test failed: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": str(e),
            "data_source_id": data_source_id,
            "connected": False,
            "tested_at": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, name="sync_listed_companies")
def sync_listed_companies(self, execution_type: str = "manual"):
    """
    上場企業一覧の同期タスク（シンプル版）
    
    Args:
        execution_type: 実行タイプ（manual/scheduled）
        
    Returns:
        Dict: 同期結果
    """
    print(f"Starting simple company sync task (execution_type: {execution_type})")
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"sync_listed_companies started with execution_type: {execution_type}")
    
    try:
        # タスクIDを記録（デバッグ用）
        task_id = self.request.id
        logger.info(f"Task ID: {task_id}")
        
        # 同期版のデータベースセッションを使用
        from app.db.session import SessionLocal
        from sqlalchemy import select
        from app.models.api_endpoint import APIEndpoint, APIEndpointExecutionLog
        
        # 実行開始時刻を記録
        start_time = datetime.utcnow()
        
        with SessionLocal() as db:
            try:
                # 上場企業一覧エンドポイントを取得
                endpoint = db.query(APIEndpoint).filter(
                    APIEndpoint.data_type == "listed_companies"
                ).first()
                
                logger.info(f"Found endpoint: {endpoint.id if endpoint else 'None'}")
                
                # 進捗を更新
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': 0,
                        'total': 1,
                        'message': '同期処理を準備中...'
                    }
                )
                
                # エンドポイントIDを保存（実行ログは非同期実行後に作成）
                endpoint_id = endpoint.id if endpoint else None
                
                # 非同期処理を同期的に実行
                async def _sync():
                    # 各タスク実行で新しいセッションメーカーを作成
                    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
                    from app.config import settings
                    
                    # 新しい非同期エンジンを作成
                    task_async_engine = create_async_engine(
                        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                        echo=False,
                        future=True,
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
                        async with task_session_maker() as async_db:
                            # サービス初期化
                            data_source_service = DataSourceService(async_db)
                            jquants_client_manager = JQuantsClientManager(data_source_service)
                            
                            # フィーチャーフラグに基づいてサービスを選択
                            if FeatureFlags.is_enabled("use_company_sync_service_v2"):
                                sync_service = CompanySyncServiceV2(async_db, data_source_service, jquants_client_manager)
                            else:
                                sync_service = CompanySyncService(async_db, data_source_service, jquants_client_manager)
                            
                            # データソースを取得
                            data_source = await data_source_service.get_jquants_source()
                            if not data_source:
                                raise Exception("No active J-Quants data source found")
                            
                            # 履歴を記録する sync_companies メソッドを使用
                            sync_history = await sync_service.sync_companies(
                                data_source_id=data_source.id,
                                sync_type="full",
                                execution_type=execution_type
                            )
                            
                            return {
                                "status": "success",
                                "sync_count": sync_history.total_companies,
                                "duration": (sync_history.completed_at - sync_history.started_at).total_seconds() if sync_history.completed_at else 0,
                                "executed_at": sync_history.started_at
                            }
                    finally:
                        # エンジンをクリーンアップ
                        await task_async_engine.dispose()
                
                # 新しいイベントループで実行
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 進捗を更新
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': 0,
                            'total': 1,
                            'message': '上場企業データを取得中...'
                        }
                    )
                    result = loop.run_until_complete(_sync())
                finally:
                    loop.close()
                
                # 実行ログを作成（同期セッションで）
                if endpoint_id:
                    completed_at = datetime.utcnow()
                    duration = (completed_at - start_time).total_seconds()
                    
                    logger.info(f"Creating execution log for endpoint_id={endpoint_id}, start_time={start_time}")
                    execution_log = APIEndpointExecutionLog(
                        endpoint_id=endpoint_id,
                        execution_type=execution_type,
                        started_at=start_time,
                        completed_at=completed_at,
                        success=result["status"] == "success",
                        response_time_ms=int(duration * 1000),
                        data_count=result.get("sync_count", 0),
                        error_message=result.get("error") if result["status"] != "success" else None,
                        parameters_used={"task_id": task_id}
                    )
                    db.add(execution_log)
                    db.commit()
                    logger.info(f"Created execution log: id={execution_log.id}, success={execution_log.success}, data_count={execution_log.data_count}")
                    
                    # APIEndpointの統計情報を更新
                    # endpointを再取得（同じトランザクション内で最新の状態を取得）
                    endpoint = db.query(APIEndpoint).filter(
                        APIEndpoint.data_type == "listed_companies"
                    ).first()
                    
                    if endpoint:
                        endpoint.last_execution_at = execution_log.started_at
                        endpoint.total_executions += 1
                        
                        if execution_log.success:
                            endpoint.last_success_at = execution_log.completed_at
                            endpoint.successful_executions += 1
                            endpoint.last_data_count = execution_log.data_count
                        else:
                            endpoint.last_error_at = execution_log.completed_at
                            endpoint.failed_executions += 1
                            endpoint.last_error_message = execution_log.error_message
                        
                        # 平均応答時間を更新（簡易計算）
                        if execution_log.response_time_ms and endpoint.average_response_time_ms:
                            endpoint.average_response_time_ms = (
                                (endpoint.average_response_time_ms * (endpoint.total_executions - 1) + execution_log.response_time_ms) 
                                / endpoint.total_executions
                            )
                        elif execution_log.response_time_ms:
                            endpoint.average_response_time_ms = float(execution_log.response_time_ms)
                        
                        db.commit()
                        logger.info(f"Updated endpoint statistics for endpoint ID {endpoint.id}")
                
                # スケジュール履歴更新
                schedule = db.query(APIEndpointSchedule).join(
                    APIEndpoint
                ).filter(
                    APIEndpoint.data_type == "listed_companies"
                ).first()
                
                if schedule:
                    schedule.last_execution_at = result["executed_at"]
                    schedule.last_execution_status = result["status"]
                    schedule.last_sync_count = result.get("sync_count", 0)
                    db.commit()
                
                print(f"Simple company sync completed: {result}")
                return result
                
            except Exception as e:
                db.rollback()
                raise
        
    except Exception as e:
        error_msg = f"Simple company sync failed: {str(e)}"
        print(error_msg)
        return {
            "status": "failed",
            "error": str(e),
            "executed_at": datetime.utcnow()
        }