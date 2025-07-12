"""
スケジュール管理サービス
"""
from datetime import datetime, time
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from celery.schedules import crontab

from app.models.api_endpoint import APIEndpointSchedule, APIEndpoint
from app.core.celery_app import celery_app


class ScheduleService:
    """スケジュール管理サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_schedule_by_endpoint_id(
        self, 
        endpoint_id: int
    ) -> Optional[APIEndpointSchedule]:
        """
        エンドポイントIDでスケジュールを取得
        
        Args:
            endpoint_id: エンドポイントID
            
        Returns:
            Optional[APIEndpointSchedule]: スケジュール
        """
        result = await self.db.execute(
            select(APIEndpointSchedule)
            .options(selectinload(APIEndpointSchedule.endpoint))
            .where(APIEndpointSchedule.endpoint_id == endpoint_id)
        )
        return result.scalar_one_or_none()
    
    async def create_schedule(
        self,
        endpoint_id: int,
        execution_time: time,
        schedule_type: str = "daily",
        is_enabled: bool = True
    ) -> APIEndpointSchedule:
        """
        新しいスケジュールを作成
        
        Args:
            endpoint_id: エンドポイントID
            execution_time: 実行時間
            schedule_type: スケジュールタイプ（デフォルト: daily）
            is_enabled: 有効フラグ（デフォルト: True）
            
        Returns:
            APIEndpointSchedule: 作成されたスケジュール
        """
        # 既存のスケジュールがないか確認
        existing = await self.get_schedule_by_endpoint_id(endpoint_id)
        if existing:
            raise ValueError(f"Schedule already exists for endpoint_id: {endpoint_id}")
        
        # 新しいスケジュールを作成
        schedule = APIEndpointSchedule(
            endpoint_id=endpoint_id,
            is_enabled=is_enabled,
            schedule_type=schedule_type,
            execution_time=execution_time,
            timezone="Asia/Tokyo"
        )
        
        self.db.add(schedule)
        
        # Celery Beatのスケジュールを設定
        if is_enabled:
            self._update_celery_beat_schedule(endpoint_id, execution_time)
        
        await self.db.commit()
        await self.db.refresh(schedule)
        
        return schedule
    
    async def update_schedule_time(
        self, 
        endpoint_id: int, 
        execution_time: time
    ) -> APIEndpointSchedule:
        """
        実行時間を更新
        
        Args:
            endpoint_id: エンドポイントID
            execution_time: 新しい実行時間
            
        Returns:
            APIEndpointSchedule: 更新されたスケジュール
        """
        schedule = await self.get_schedule_by_endpoint_id(endpoint_id)
        
        if not schedule:
            raise ValueError(f"Schedule not found for endpoint_id: {endpoint_id}")
        
        schedule.execution_time = execution_time
        schedule.updated_at = datetime.utcnow()
        
        # Celery Beatのスケジュールを更新
        self._update_celery_beat_schedule(endpoint_id, execution_time)
        
        await self.db.commit()
        await self.db.refresh(schedule)
        
        return schedule
    
    async def toggle_schedule(
        self,
        endpoint_id: int,
        is_enabled: bool
    ) -> APIEndpointSchedule:
        """
        スケジュールの有効/無効を切り替え
        
        Args:
            endpoint_id: エンドポイントID
            is_enabled: 有効フラグ
            
        Returns:
            APIEndpointSchedule: 更新されたスケジュール
        """
        schedule = await self.get_schedule_by_endpoint_id(endpoint_id)
        
        if not schedule:
            raise ValueError(f"Schedule not found for endpoint_id: {endpoint_id}")
        
        schedule.is_enabled = is_enabled
        schedule.updated_at = datetime.utcnow()
        
        # Celery Beatのスケジュールを更新
        if is_enabled:
            self._update_celery_beat_schedule(endpoint_id, schedule.execution_time)
        else:
            self._remove_celery_beat_schedule(endpoint_id)
        
        await self.db.commit()
        await self.db.refresh(schedule)
        
        return schedule
    
    async def get_schedule_status(
        self,
        endpoint_id: int
    ) -> Dict[str, Any]:
        """
        スケジュールの実行状況を取得
        
        Args:
            endpoint_id: エンドポイントID
            
        Returns:
            Dict[str, Any]: スケジュール状況
        """
        schedule = await self.get_schedule_by_endpoint_id(endpoint_id)
        
        if not schedule:
            return {
                "status": "not_found",
                "message": "Schedule not found"
            }
        
        # 次回実行時刻を計算
        next_execution = self._calculate_next_execution(
            schedule.execution_time,
            schedule.timezone
        )
        
        return {
            "is_enabled": schedule.is_enabled,
            "schedule_type": schedule.schedule_type,
            "execution_time": schedule.execution_time.strftime("%H:%M"),
            "timezone": schedule.timezone,
            "next_execution": next_execution.isoformat() if next_execution else None,
            "last_execution_at": schedule.last_execution_at.isoformat() if schedule.last_execution_at else None,
            "last_execution_status": schedule.last_execution_status,
            "last_sync_count": schedule.last_sync_count
        }
    
    def _update_celery_beat_schedule(self, endpoint_id: int, execution_time: time):
        """
        Celery Beatのスケジュールを動的更新
        
        Args:
            endpoint_id: エンドポイントID
            execution_time: 実行時間
        """
        schedule_name = f"sync_companies_{endpoint_id}"
        
        # Celery Beatのスケジュール設定を更新
        celery_app.conf.beat_schedule[schedule_name] = {
            'task': 'sync_listed_companies',
            'schedule': crontab(
                hour=execution_time.hour,
                minute=execution_time.minute
            ),
            'args': ['scheduled'],  # execution_typeをscheduledに設定
            'options': {
                'timezone': 'Asia/Tokyo'
            }
        }
    
    def _remove_celery_beat_schedule(self, endpoint_id: int):
        """
        Celery Beatからスケジュールを削除
        
        Args:
            endpoint_id: エンドポイントID
        """
        schedule_name = f"sync_companies_{endpoint_id}"
        
        if schedule_name in celery_app.conf.beat_schedule:
            del celery_app.conf.beat_schedule[schedule_name]
    
    def _calculate_next_execution(
        self,
        execution_time: time,
        timezone: str
    ) -> Optional[datetime]:
        """
        次回実行時刻を計算
        
        Args:
            execution_time: 実行時間
            timezone: タイムゾーン
            
        Returns:
            Optional[datetime]: 次回実行時刻
        """
        # TODO: タイムゾーンを考慮した計算を実装
        # 簡易実装として、今日または明日の実行時刻を返す
        now = datetime.now()
        today_execution = datetime.combine(now.date(), execution_time)
        
        if today_execution > now:
            return today_execution
        else:
            # 明日の実行時刻
            from datetime import timedelta
            return today_execution + timedelta(days=1)