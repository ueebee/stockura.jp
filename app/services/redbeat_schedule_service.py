"""
Redbeat対応のスケジュールサービス
"""

import asyncio
from datetime import datetime, time as datetime_time
from typing import Dict, Optional
import pytz
import redis
from redbeat import RedBeatSchedulerEntry
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.api_endpoint import APIEndpointSchedule
from app.core.celery_app import celery_app
from app.core.config import settings


class RedbeatScheduleService:
    """Redbeat対応のスケジュール管理サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.jst = pytz.timezone('Asia/Tokyo')
        self.utc = pytz.UTC
    
    async def create_or_update_schedule(
        self,
        endpoint_id: int,
        execution_time: datetime_time,
        is_enabled: bool = True
    ) -> APIEndpointSchedule:
        """スケジュールの作成または更新（即座に反映）"""
        
        # データベースに保存
        schedule = await self._save_to_database(endpoint_id, execution_time, is_enabled)
        
        # Redbeatに登録/更新
        if is_enabled:
            await self._update_redbeat_schedule(endpoint_id, execution_time)
        else:
            await self._remove_redbeat_schedule(endpoint_id)
        
        return schedule
    
    async def toggle_schedule(self, endpoint_id: int) -> APIEndpointSchedule:
        """スケジュールの有効/無効を切り替え"""
        result = await self.db.execute(
            select(APIEndpointSchedule).where(APIEndpointSchedule.endpoint_id == endpoint_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise ValueError(f"Schedule not found for endpoint {endpoint_id}")
        
        # 状態を反転
        schedule.is_enabled = not schedule.is_enabled
        await self.db.commit()
        
        # Redbeatに反映
        if schedule.is_enabled:
            await self._update_redbeat_schedule(endpoint_id, schedule.execution_time)
        else:
            await self._remove_redbeat_schedule(endpoint_id)
        
        return schedule
    
    async def delete_schedule(self, endpoint_id: int):
        """スケジュールを削除"""
        # Redbeatから削除
        await self._remove_redbeat_schedule(endpoint_id)
        
        # データベースから削除
        result = await self.db.execute(
            select(APIEndpointSchedule).where(APIEndpointSchedule.endpoint_id == endpoint_id)
        )
        schedule = result.scalar_one_or_none()
        if schedule:
            await self.db.delete(schedule)
            await self.db.commit()
    
    async def get_schedule_status(self, endpoint_id: int) -> Dict:
        """スケジュールの状態を取得"""
        # DB情報
        result = await self.db.execute(
            select(APIEndpointSchedule).where(APIEndpointSchedule.endpoint_id == endpoint_id)
        )
        db_schedule = result.scalar_one_or_none()
        
        if not db_schedule:
            return {"exists": False}
        
        # Redbeat情報
        entry_name = f"sync_companies_{endpoint_id}"
        redbeat_info = await self._get_redbeat_entry_info(entry_name)
        
        # 次回実行時刻を計算
        next_execution = None
        if db_schedule.is_enabled and redbeat_info:
            next_execution = redbeat_info.get('next_run')
        
        return {
            "exists": True,
            "is_enabled": db_schedule.is_enabled,
            "schedule_type": db_schedule.schedule_type,
            "execution_time": db_schedule.execution_time.strftime("%H:%M"),
            "timezone": db_schedule.timezone,
            "next_execution": next_execution.isoformat() if next_execution else None,
            "last_execution_at": db_schedule.last_execution_at.isoformat() if db_schedule.last_execution_at else None,
            "last_execution_status": db_schedule.last_execution_status,
            "last_sync_count": db_schedule.last_sync_count,
            "redbeat_active": redbeat_info is not None
        }
    
    async def _save_to_database(
        self,
        endpoint_id: int,
        execution_time: datetime_time,
        is_enabled: bool
    ) -> APIEndpointSchedule:
        """データベースに保存"""
        result = await self.db.execute(
            select(APIEndpointSchedule).where(APIEndpointSchedule.endpoint_id == endpoint_id)
        )
        schedule = result.scalar_one_or_none()
        
        if schedule:
            # 更新
            schedule.execution_time = execution_time
            schedule.is_enabled = is_enabled
            schedule.updated_at = datetime.now(self.utc).replace(tzinfo=None)  # タイムゾーン情報を削除
        else:
            # 新規作成
            schedule = APIEndpointSchedule(
                endpoint_id=endpoint_id,
                execution_time=execution_time,
                is_enabled=is_enabled,
                schedule_type="daily",
                timezone="Asia/Tokyo"
            )
            self.db.add(schedule)
        
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule
    
    async def _update_redbeat_schedule(
        self,
        endpoint_id: int,
        execution_time: datetime_time
    ):
        """Redbeatスケジュールを更新（非同期ラッパー）"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._sync_update_redbeat_schedule,
            endpoint_id,
            execution_time
        )
    
    def _sync_update_redbeat_schedule(
        self,
        endpoint_id: int,
        execution_time: datetime_time
    ):
        """Redbeatスケジュールを更新（同期処理）"""
        entry_name = f"sync_companies_{endpoint_id}"
        
        # JSTをUTCに変換
        today = datetime.now(self.jst).date()
        jst_datetime = self.jst.localize(datetime.combine(today, execution_time))
        utc_datetime = jst_datetime.astimezone(self.utc)
        
        # Crontabスケジュール作成
        schedule = crontab(
            hour=utc_datetime.hour,
            minute=utc_datetime.minute
        )
        
        # RedBeatエントリー作成/更新
        entry = RedBeatSchedulerEntry(
            name=entry_name,
            task='sync_listed_companies',
            schedule=schedule,
            args=['scheduled'],
            options={
                'queue': 'default',
                'expires': 3600,
            },
            app=celery_app
        )
        entry.save()
        
        print(f"Updated Redbeat schedule: {entry_name} - JST {execution_time} -> UTC {utc_datetime.hour}:{utc_datetime.minute:02d}")
    
    async def _remove_redbeat_schedule(self, endpoint_id: int):
        """Redbeatスケジュールを削除（非同期ラッパー）"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._sync_remove_redbeat_schedule,
            endpoint_id
        )
    
    def _sync_remove_redbeat_schedule(self, endpoint_id: int):
        """Redbeatスケジュールを削除（同期処理）"""
        entry_name = f"sync_companies_{endpoint_id}"
        
        try:
            # Redisキーを直接構築
            key = f"{celery_app.conf.redbeat_key_prefix}{entry_name}"
            entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
            entry.delete()
            print(f"Removed Redbeat schedule: {entry_name}")
        except Exception as e:
            print(f"Schedule not found or already deleted: {entry_name} - {e}")
    
    async def _get_redbeat_entry_info(self, entry_name: str) -> Optional[Dict]:
        """Redbeatエントリーの情報を取得"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._sync_get_redbeat_entry_info,
            entry_name
        )
    
    def _sync_get_redbeat_entry_info(self, entry_name: str) -> Optional[Dict]:
        """Redbeatエントリーの情報を取得（同期処理）"""
        try:
            key = f"{celery_app.conf.redbeat_key_prefix}{entry_name}"
            entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
            
            # 次回実行時刻を計算
            now = datetime.now(self.utc)
            remaining = entry.schedule.remaining_estimate(entry.last_run_at or now)
            next_run = now + remaining
            next_run_jst = next_run.astimezone(self.jst)
            
            return {
                'name': entry.name,
                'task': entry.task,
                'schedule': str(entry.schedule),
                'last_run': entry.last_run_at,
                'total_runs': entry.total_run_count,
                'next_run': next_run_jst
            }
        except Exception:
            return None
    
    async def get_all_active_schedules(self) -> list:
        """すべてのアクティブなスケジュールを取得"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_get_all_active_schedules)
    
    def _sync_get_all_active_schedules(self) -> list:
        """すべてのアクティブなスケジュールを取得（同期処理）"""
        pattern = f"{celery_app.conf.redbeat_key_prefix}sync_companies_*"
        keys = self.redis_client.keys(pattern)
        
        schedules = []
        for key in keys:
            try:
                entry = RedBeatSchedulerEntry.from_key(key.decode(), app=celery_app)
                
                # 次回実行時刻を計算
                now = datetime.now(self.utc)
                remaining = entry.schedule.remaining_estimate(entry.last_run_at or now)
                next_run = now + remaining
                next_run_jst = next_run.astimezone(self.jst)
                
                schedules.append({
                    'name': entry.name,
                    'task': entry.task,
                    'schedule': str(entry.schedule),
                    'last_run': entry.last_run_at.isoformat() if entry.last_run_at else None,
                    'total_runs': entry.total_run_count,
                    'next_run': next_run_jst.isoformat()
                })
            except Exception as e:
                print(f"Error loading schedule from {key}: {e}")
        
        return schedules