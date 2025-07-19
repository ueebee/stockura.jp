"""
同期サービスの基底クラス

全ての同期サービスが継承する抽象基底クラス
共通のロギング、エラーハンドリング、統計情報管理機能を提供
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import declarative_base

# 型変数の定義（履歴モデルの型を指定するため）
HistoryModel = TypeVar('HistoryModel')


class BaseSyncService(ABC, Generic[HistoryModel]):
    """同期サービスの基底クラス"""
    
    def __init__(self, db: AsyncSession):
        """
        初期化
        
        Args:
            db: データベースセッション
        """
        self.db = db
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        ロガーのセットアップ
        
        Returns:
            logging.Logger: 設定されたロガー
        """
        return logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        同期処理の実装（サブクラスで実装）
        
        Args:
            **kwargs: 同期処理に必要なパラメータ
            
        Returns:
            Dict[str, Any]: 同期結果
        """
        pass
    
    @abstractmethod
    def get_history_model(self) -> type:
        """
        履歴モデルクラスを返す（サブクラスで実装）
        
        Returns:
            type: 履歴モデルクラス
        """
        pass
    
    async def get_sync_history(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[HistoryModel]:
        """
        同期履歴の取得（共通実装）
        
        Args:
            limit: 取得件数制限
            offset: オフセット
            status: ステータスフィルタ
            
        Returns:
            List[HistoryModel]: 同期履歴リスト
        """
        history_model = self.get_history_model()
        
        # クエリを構築
        query = select(history_model)
        
        # ステータスフィルタ
        if status and hasattr(history_model, 'status'):
            query = query.where(history_model.status == status)
        
        # ソートとページネーション
        if hasattr(history_model, 'started_at'):
            query = query.order_by(history_model.started_at.desc())
        
        query = query.offset(offset).limit(limit)
        
        # 実行
        result = await self.db.execute(query)
        histories = result.scalars().all()
        
        return histories
    
    async def get_latest_sync_status(self) -> Optional[HistoryModel]:
        """
        最新の同期ステータスを取得
        
        Returns:
            Optional[HistoryModel]: 最新の同期履歴
        """
        history_model = self.get_history_model()
        
        result = await self.db.execute(
            select(history_model)
            .order_by(history_model.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        エラーハンドリング（共通実装）
        
        Args:
            error: 発生したエラー
            context: エラーコンテキスト情報
        """
        error_message = f"{self.__class__.__name__} sync error: {str(error)}"
        
        # ロギング
        self.logger.error(error_message, extra=context, exc_info=True)
        
        # 必要に応じて追加のエラー処理
        # - メトリクスの送信
        # - 通知の送信
        # - エラートラッキングサービスへの送信
    
    async def create_sync_history(
        self,
        sync_type: str,
        **kwargs
    ) -> HistoryModel:
        """
        同期履歴レコードを作成
        
        Args:
            sync_type: 同期タイプ
            **kwargs: 追加のフィールド
            
        Returns:
            HistoryModel: 作成された履歴レコード
        """
        history_model = self.get_history_model()
        
        # 基本フィールドを設定
        history_data = {
            "sync_type": sync_type,
            "status": "running",
            "started_at": datetime.utcnow(),
            **kwargs
        }
        
        # 履歴レコードを作成
        history = history_model(**history_data)
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        
        return history
    
    async def update_sync_history_success(
        self,
        history: HistoryModel,
        **stats
    ) -> HistoryModel:
        """
        同期成功時の履歴更新
        
        Args:
            history: 更新対象の履歴レコード
            **stats: 統計情報
            
        Returns:
            HistoryModel: 更新された履歴レコード
        """
        history.status = "completed"
        history.completed_at = datetime.utcnow()
        
        # 統計情報を設定
        for key, value in stats.items():
            if hasattr(history, key):
                setattr(history, key, value)
        
        await self.db.commit()
        await self.db.refresh(history)
        
        return history
    
    async def update_sync_history_failure(
        self,
        history: HistoryModel,
        error: Exception
    ) -> HistoryModel:
        """
        同期失敗時の履歴更新
        
        Args:
            history: 更新対象の履歴レコード
            error: 発生したエラー
            
        Returns:
            HistoryModel: 更新された履歴レコード
        """
        history.status = "failed"
        history.completed_at = datetime.utcnow()
        
        if hasattr(history, 'error_message'):
            history.error_message = str(error)
        
        await self.db.commit()
        await self.db.refresh(history)
        
        return history
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """
        同期の統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        history_model = self.get_history_model()
        
        # 全体の統計を取得
        total_count = await self.db.scalar(
            select(func.count(history_model.id))
        )
        
        # ステータス別の統計
        status_stats = {}
        if hasattr(history_model, 'status'):
            result = await self.db.execute(
                select(
                    history_model.status,
                    func.count(history_model.id)
                )
                .group_by(history_model.status)
            )
            status_stats = dict(result.all())
        
        # 最新の同期情報
        latest = await self.get_latest_sync_status()
        
        return {
            "total_syncs": total_count,
            "status_breakdown": status_stats,
            "latest_sync": {
                "status": getattr(latest, 'status', None),
                "started_at": getattr(latest, 'started_at', None),
                "completed_at": getattr(latest, 'completed_at', None)
            } if latest else None
        }