"""TradesSpec 取得 Celery タスク（非同期版）"""
import asyncio
from datetime import date, datetime
from typing import Dict, Optional, Any
from uuid import UUID, uuid4

from celery import Task
from celery.utils.log import get_task_logger

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.worker_hooks import get_or_create_event_loop
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.repositories.task_log_repository import TaskLogRepository


logger = get_task_logger(__name__)


class FetchTradesSpecTask(Task):
    """TradesSpec 取得タスクのベースクラス"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """タスク失敗時のコールバック"""
        logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
        
    def on_success(self, retval, task_id, args, kwargs):
        """タスク成功時のコールバック"""
        logger.info(f"Task {task_id} succeeded with result: {retval}")
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(bind=True, base=FetchTradesSpecTask, name="fetch_trades_spec_task_asyncpg")
def fetch_trades_spec_task_asyncpg(
    self,
    section: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max_pages: Optional[int] = None,
    schedule_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    TradesSpec データを取得する Celery タスク（非同期版）
    
    Args:
        section: 市場区分
        from_date: 開始日（YYYY-MM-DD 形式）
        to_date: 終了日（YYYY-MM-DD 形式）
        max_pages: 最大取得ページ数
        schedule_id: スケジュール ID（定期実行の場合）
        
    Returns:
        実行結果の辞書
    """
    # タスクIDの取得（self.requestがNoneの場合も考慮）
    task_id = self.request.id if self.request else None
    
    # イベントループ内で非同期関数を実行
    loop = get_or_create_event_loop()
    
    try:
        result = loop.run_until_complete(
            _fetch_trades_spec_async(
                section=section,
                from_date=from_date,
                to_date=to_date,
                max_pages=max_pages,
                schedule_id=schedule_id,
                task_id=task_id,
            )
        )
        return result
    except Exception as e:
        logger.error(f"Error in fetch_trades_spec_task_asyncpg: {e}", exc_info=True)
        raise


async def _fetch_trades_spec_async(
    section: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max_pages: Optional[int] = None,
    schedule_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    非同期で TradesSpec データを取得する内部関数
    
    Args:
        section: 市場区分
        from_date: 開始日文字列
        to_date: 終了日文字列
        max_pages: 最大取得ページ数
        schedule_id: スケジュール ID
        task_id: Celery タスク ID
        
    Returns:
        実行結果の辞書
    """
    task_execution_id = uuid4()
    started_at = datetime.utcnow()
    
    # 日付文字列を date オブジェクトに変換
    from_date_obj = date.fromisoformat(from_date) if from_date else None
    to_date_obj = date.fromisoformat(to_date) if to_date else None
    
    base_client = None
    
    async with get_async_session_context() as session:
        # タスクログリポジトリ
        task_log_repo = TaskLogRepository(session)
        
        # Create task log entry
        from app.domain.entities.task_log import TaskExecutionLog
        
        task_log = TaskExecutionLog(
            id=task_execution_id,
            schedule_id=UUID(schedule_id) if schedule_id else None,
            task_name="fetch_trades_spec_task_asyncpg",
            task_id=task_id,
            started_at=started_at,
            status="running",
        )
        
        await task_log_repo.create(task_log)
        
        try:
            # JQuantsClientFactory とリポジトリを初期化
            from app.infrastructure.jquants.client_factory import JQuantsClientFactory
            from app.infrastructure.repositories.trades_spec_repository_impl import (
                TradesSpecRepositoryImpl,
            )
            from app.application.use_cases.fetch_trades_spec import FetchTradesSpecUseCase
            
            factory = JQuantsClientFactory()
            # base_clientを取得
            base_client = await factory._get_base_client()
            client = await factory.create_trades_spec_client()
            repository = TradesSpecRepositoryImpl(session)
            use_case = FetchTradesSpecUseCase(client, repository)
            
            # データ取得実行
            result = await use_case.execute(
                section=section,
                from_date=from_date_obj,
                to_date=to_date_obj,
                max_pages=max_pages,
            )
            
            finished_at = datetime.utcnow()
            
            # 結果に基づいてステータスを決定
            if result.success:
                status = "success"
                result_data = {
                    "fetched_count": result.fetched_count,
                    "saved_count": result.saved_count,
                    "section": result.section,
                    "from_date": result.from_date.isoformat() if result.from_date else None,
                    "to_date": result.to_date.isoformat() if result.to_date else None,
                }
            else:
                status = "failed"
                result_data = {
                    "error": result.error_message,
                    "fetched_count": result.fetched_count,
                    "saved_count": result.saved_count,
                }
            
            # タスク完了ログ
            await task_log_repo.update_status(
                log_id=task_execution_id,
                status=status,
                finished_at=finished_at,
                result=result_data,
                error_message=result.error_message if not result.success else None,
            )
            
            await session.commit()
            
            logger.info(
                f"TradesSpec fetch completed: "
                f"fetched={result.fetched_count}, saved={result.saved_count}"
            )
            
            # base_client をクローズ
            if base_client:
                await base_client.close()
            
            return {
                "success": result.success,
                "task_execution_id": str(task_execution_id),
                **result_data,
            }
            
        except Exception as e:
            # エラー時の処理
            error_message = str(e)
            logger.error(f"Error fetching trades spec: {error_message}", exc_info=True)
            
            await task_log_repo.update_status(
                log_id=task_execution_id,
                status="failed",
                finished_at=datetime.utcnow(),
                error_message=error_message,
            )
            
            await session.commit()
            
            # エラー時も base_client をクローズ
            if base_client:
                await base_client.close()
            
            raise