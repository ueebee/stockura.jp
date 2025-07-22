"""
日次株価データ定期実行スケジュールサービス
"""

import asyncio
from datetime import datetime, time as datetime_time, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
import redis
from redbeat import RedBeatSchedulerEntry
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.daily_quote_schedule import DailyQuoteSchedule
from app.core.celery_app import celery_app
from app.core.config import settings


class DailyQuotesScheduleService:
    """日次株価データ定期実行スケジュール管理サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.jst = pytz.timezone('Asia/Tokyo')
        self.utc = pytz.UTC
    
    def calculate_dates_from_preset(self, preset: str, base_date: datetime = None) -> Tuple[datetime.date, datetime.date]:
        """プリセット名から実行時点の日付を動的に計算"""
        if base_date is None:
            base_date = datetime.now(self.jst)
        
        # 昨日を基準とする（当日のデータは通常まだ存在しないため）
        yesterday = base_date - timedelta(days=1)
        
        if preset == "last7days":
            from_date = yesterday - timedelta(days=6)
            to_date = yesterday
        elif preset == "last30days":
            from_date = yesterday - timedelta(days=29)
            to_date = yesterday
        elif preset == "last90days":
            from_date = yesterday - timedelta(days=89)
            to_date = yesterday
        elif preset == "thisMonth":
            from_date = datetime(yesterday.year, yesterday.month, 1, tzinfo=self.jst)
            to_date = yesterday
        elif preset == "lastMonth":
            # 先月の1日と最終日を計算
            if yesterday.month == 1:
                first_day = datetime(yesterday.year - 1, 12, 1, tzinfo=self.jst)
                last_day = datetime(yesterday.year - 1, 12, 31, tzinfo=self.jst)
            else:
                first_day = datetime(yesterday.year, yesterday.month - 1, 1, tzinfo=self.jst)
                # 月末日を計算
                next_month = first_day.replace(day=28) + timedelta(days=4)
                last_day = next_month - timedelta(days=next_month.day)
            from_date = first_day
            to_date = last_day
        elif preset == "yesterday":
            from_date = yesterday
            to_date = yesterday
        else:
            # デフォルトは昨日のみ
            from_date = yesterday
            to_date = yesterday
        
        return from_date.date(), to_date.date()
    
    async def create_schedule(
        self,
        name: str,
        sync_type: str,
        relative_preset: str,
        data_source_id: int,
        schedule_type: str,
        execution_time: datetime_time,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None,
        description: Optional[str] = None,
        is_enabled: bool = True
    ) -> DailyQuoteSchedule:
        """スケジュールを作成"""
        
        # データベースに保存
        schedule = DailyQuoteSchedule(
            name=name,
            description=description,
            sync_type=sync_type,
            relative_preset=relative_preset,
            data_source_id=data_source_id,
            schedule_type=schedule_type,
            execution_time=execution_time,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            is_enabled=is_enabled
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        
        # Redbeatに登録
        if is_enabled:
            await self._update_redbeat_schedule(schedule)
        
        return schedule
    
    async def update_schedule(
        self,
        schedule_id: int,
        **kwargs
    ) -> DailyQuoteSchedule:
        """スケジュールを更新"""
        result = await self.db.execute(
            select(DailyQuoteSchedule).where(DailyQuoteSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        # 更新
        for key, value in kwargs.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        await self.db.commit()
        await self.db.refresh(schedule)
        
        # Redbeatに反映
        if schedule.is_enabled:
            await self._update_redbeat_schedule(schedule)
        else:
            await self._remove_redbeat_schedule(schedule.id)
        
        return schedule
    
    async def delete_schedule(self, schedule_id: int):
        """スケジュールを削除"""
        result = await self.db.execute(
            select(DailyQuoteSchedule).where(DailyQuoteSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        # Redbeatから削除
        await self._remove_redbeat_schedule(schedule_id)
        
        # データベースから削除
        await self.db.delete(schedule)
        await self.db.commit()
    
    async def get_schedule(self, schedule_id: int) -> Optional[DailyQuoteSchedule]:
        """スケジュールを取得"""
        result = await self.db.execute(
            select(DailyQuoteSchedule).where(DailyQuoteSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()
    
    async def list_schedules(self) -> List[DailyQuoteSchedule]:
        """すべてのスケジュールを取得"""
        result = await self.db.execute(
            select(DailyQuoteSchedule).order_by(DailyQuoteSchedule.created_at.desc())
        )
        return result.scalars().all()
    
    async def toggle_schedule(self, schedule_id: int) -> DailyQuoteSchedule:
        """スケジュールの有効/無効を切り替え"""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        schedule.is_enabled = not schedule.is_enabled
        await self.db.commit()
        
        # Redbeatに反映
        if schedule.is_enabled:
            await self._update_redbeat_schedule(schedule)
        else:
            await self._remove_redbeat_schedule(schedule_id)
        
        return schedule
    
    async def get_schedule_with_next_run(self, schedule_id: int) -> Dict:
        """スケジュールの詳細情報（次回実行時刻含む）を取得"""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            return None
        
        # 基本情報
        info = {
            "id": schedule.id,
            "name": schedule.name,
            "description": schedule.description,
            "sync_type": schedule.sync_type,
            "relative_preset": schedule.relative_preset,
            "data_source_id": schedule.data_source_id,
            "schedule_type": schedule.schedule_type,
            "execution_time": schedule.execution_time.strftime("%H:%M"),
            "day_of_week": schedule.day_of_week,
            "day_of_month": schedule.day_of_month,
            "is_enabled": schedule.is_enabled,
            "last_execution_at": schedule.last_execution_at.isoformat() if schedule.last_execution_at else None,
            "last_execution_status": schedule.last_execution_status,
            "last_sync_count": schedule.last_sync_count,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None
        }
        
        # デフォルト値を設定
        info["next_run"] = None
        info["next_run_date_range"] = None
        
        # 次回実行情報
        if schedule.is_enabled:
            entry_name = f"daily_quotes_schedule_{schedule.id}"
            redbeat_info = await self._get_redbeat_entry_info(entry_name)
            if redbeat_info:
                info["next_run"] = redbeat_info.get('next_run')
                
                # 次回実行時の日付範囲を計算
                if schedule.relative_preset:
                    next_run_dt = redbeat_info.get('next_run')
                    if next_run_dt:
                        from_date, to_date = self.calculate_dates_from_preset(
                            schedule.relative_preset,
                            base_date=next_run_dt
                        )
                        info["next_run_date_range"] = {
                            "from_date": from_date.isoformat(),
                            "to_date": to_date.isoformat()
                        }
        
        return info
    
    async def _update_redbeat_schedule(self, schedule: DailyQuoteSchedule):
        """Redbeatスケジュールを更新"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._sync_update_redbeat_schedule,
            schedule
        )
    
    def _sync_update_redbeat_schedule(self, schedule: DailyQuoteSchedule):
        """Redbeatスケジュールを更新（同期処理）"""
        entry_name = f"daily_quotes_schedule_{schedule.id}"
        
        # JSTをUTCに変換
        today = datetime.now(self.jst).date()
        jst_datetime = self.jst.localize(datetime.combine(today, schedule.execution_time))
        utc_datetime = jst_datetime.astimezone(self.utc)
        
        # スケジュール作成
        if schedule.schedule_type == "daily":
            schedule_obj = crontab(
                hour=utc_datetime.hour,
                minute=utc_datetime.minute
            )
        elif schedule.schedule_type == "weekly":
            # Celeryの曜日は0=日曜日、DBは0=月曜日なので変換
            celery_dow = (schedule.day_of_week + 1) % 7
            schedule_obj = crontab(
                hour=utc_datetime.hour,
                minute=utc_datetime.minute,
                day_of_week=celery_dow
            )
        elif schedule.schedule_type == "monthly":
            schedule_obj = crontab(
                hour=utc_datetime.hour,
                minute=utc_datetime.minute,
                day_of_month=schedule.day_of_month
            )
        else:
            raise ValueError(f"Unknown schedule type: {schedule.schedule_type}")
        
        # タスク引数を準備
        task_args = {
            'schedule_id': schedule.id,
            'sync_type': schedule.sync_type,
            'data_source_id': schedule.data_source_id,
            'relative_preset': schedule.relative_preset
        }
        
        # 既存のエントリを削除（存在する場合）
        try:
            key = f"{celery_app.conf.redbeat_key_prefix}{entry_name}"
            old_entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
            old_entry.delete()
            print(f"Deleted existing Redbeat schedule: {entry_name}")
        except Exception:
            # エントリが存在しない場合は無視
            pass
        
        # RedBeatエントリー作成/更新
        entry = RedBeatSchedulerEntry(
            name=entry_name,
            task='sync_daily_quotes_scheduled',
            schedule=schedule_obj,
            kwargs=task_args,
            options={
                'queue': 'jquants',
                'expires': 7200,  # 2時間で期限切れ
            },
            app=celery_app
        )
        entry.save()
        
        print(f"Updated Redbeat schedule: {entry_name} - {schedule.schedule_type} at JST {schedule.execution_time}")
    
    async def _remove_redbeat_schedule(self, schedule_id: int):
        """Redbeatスケジュールを削除"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._sync_remove_redbeat_schedule,
            schedule_id
        )
    
    def _sync_remove_redbeat_schedule(self, schedule_id: int):
        """Redbeatスケジュールを削除（同期処理）"""
        entry_name = f"daily_quotes_schedule_{schedule_id}"
        
        try:
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