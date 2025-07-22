"""
統一されたエラーハンドリング
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    SyncError, APIError, DataValidationError, 
    RateLimitError, AuthenticationError
)


class ErrorHandler:
    """統一されたエラーハンドラー"""
    
    @staticmethod
    def get_logger(service_name: str) -> logging.Logger:
        """サービス用のロガーを取得"""
        return logging.getLogger(f"app.services.{service_name}")
    
    @staticmethod
    async def handle_sync_error(
        error: Exception,
        service_name: str,
        context: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        sync_history_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        統一されたエラーハンドリング
        
        Args:
            error: 発生したエラー
            service_name: サービス名
            context: エラーコンテキスト（sync_type, data_source_id等）
            db: データベースセッション（エラー記録用）
            sync_history_id: 同期履歴ID（履歴更新用）
            
        Returns:
            エラー情報を含む辞書
        """
        logger = ErrorHandler.get_logger(service_name)
        
        # エラーの詳細情報を構築
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "service_name": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }
        
        # エラータイプに応じた処理
        if isinstance(error, SyncError):
            error_info["error_code"] = error.code
            error_info["error_details"] = error.details
            log_level = logging.ERROR
            
            if isinstance(error, RateLimitError):
                log_level = logging.WARNING
                error_info["retry_after"] = error.retry_after
                
            elif isinstance(error, AuthenticationError):
                log_level = logging.CRITICAL
                
            elif isinstance(error, DataValidationError):
                log_level = logging.WARNING
                error_info["validation_field"] = error.field
                error_info["validation_value"] = error.value
                
        else:
            # 予期しないエラーの場合
            error_info["error_code"] = "UNEXPECTED_ERROR"
            error_info["traceback"] = traceback.format_exc()
            log_level = logging.ERROR
        
        # ログ出力
        logger.log(
            log_level,
            f"{service_name} error: {error_info['error_message']}",
            extra={
                "error_info": error_info,
                "sync_history_id": sync_history_id
            }
        )
        
        # データベースへのエラー記録（同期履歴がある場合）
        if db and sync_history_id:
            await ErrorHandler._update_sync_history_error(
                db, sync_history_id, error_info
            )
        
        # メトリクスの送信（将来的な実装用）
        # await ErrorHandler._send_error_metrics(error_info)
        
        # 通知の送信（重大なエラーの場合、将来的な実装用）
        # if log_level >= logging.CRITICAL:
        #     await ErrorHandler._send_error_notification(error_info)
        
        return error_info
    
    @staticmethod
    async def _update_sync_history_error(
        db: AsyncSession,
        sync_history_id: int,
        error_info: Dict[str, Any]
    ) -> None:
        """同期履歴にエラー情報を記録"""
        try:
            # 同期履歴モデルに応じて更新
            # 例: CompanySyncHistory または DailyQuotesSyncHistory
            from sqlalchemy import text
            
            error_message = f"{error_info['error_type']}: {error_info['error_message']}"
            error_details = {
                "code": error_info.get("error_code"),
                "details": error_info.get("error_details", {}),
                "traceback": error_info.get("traceback")
            }
            
            # 汎用的なSQL更新（テーブル名は後で特定）
            await db.execute(
                text("""
                    UPDATE daily_quotes_sync_history 
                    SET status = 'failed',
                        error_message = :error_message,
                        completed_at = :completed_at
                    WHERE id = :sync_history_id
                """),
                {
                    "error_message": error_message,
                    "completed_at": datetime.utcnow(),
                    "sync_history_id": sync_history_id
                }
            )
            await db.commit()
            
        except Exception as e:
            logger = ErrorHandler.get_logger("error_handler")
            logger.error(f"Failed to update sync history error: {e}")
    
    @staticmethod
    def format_error_response(error_info: Dict[str, Any]) -> Dict[str, Any]:
        """APIレスポンス用にエラー情報をフォーマット"""
        return {
            "error": True,
            "error_code": error_info.get("error_code", "UNKNOWN_ERROR"),
            "message": error_info.get("error_message", "An unexpected error occurred"),
            "details": error_info.get("error_details", {}),
            "timestamp": error_info.get("timestamp")
        }
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """エラーがリトライ可能かどうかを判定"""
        if isinstance(error, RateLimitError):
            return True
        
        if isinstance(error, APIError):
            # 5xx系のエラーはリトライ可能
            if error.status_code and 500 <= error.status_code < 600:
                return True
            # タイムアウトエラーもリトライ可能
            if "timeout" in str(error).lower():
                return True
        
        # ネットワーク関連のエラーはリトライ可能
        error_message = str(error).lower()
        retryable_keywords = ["connection", "timeout", "network", "temporary"]
        if any(keyword in error_message for keyword in retryable_keywords):
            return True
        
        return False