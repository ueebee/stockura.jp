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


def get_sync_service():
    """同期サービスインスタンスを取得（同期処理のため非async）"""
    # Celeryタスクは同期的に実行されるため、asyncio.run()を使用
    async def _get_service():
        db = get_db()
        data_source_service = DataSourceService(db)
        jquants_client_manager = JQuantsClientManager(data_source_service)
        return CompanySyncService(db, data_source_service, jquants_client_manager)
    
    return asyncio.run(_get_service())


@celery_app.task(bind=True)
def sync_companies_task(
    self, 
    data_source_id: int,
    sync_date: Optional[str] = None,
    sync_type: str = "full"
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
                    sync_type=sync_type
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
        
        # 非同期処理を実行
        result = asyncio.run(_sync())
        
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
            result = sync_companies_task.delay(data_source_id, sync_date, "full")
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
        
        result = asyncio.run(_test())
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