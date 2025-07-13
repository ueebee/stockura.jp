# 動的スケジュール管理の実装計画

## 1. celery-redbeat の導入

### インストール
```bash
pip install celery-redbeat
```

### Celery設定の変更
```python
# app/core/celery_app.py
celery_app.conf.update(
    beat_scheduler='redbeat.RedBeatScheduler',
    redbeat_redis_url=settings.REDIS_URL,
    redbeat_key_prefix='stockura:schedule:',
)
```

### Docker Compose更新
```yaml
# docker-compose.yml
beat:
  command: celery -A app.core.celery_app beat -S redbeat.RedBeatScheduler --loglevel=info
```

## 2. スケジュールモデルの拡張

```python
# app/models/api_endpoint.py
class APIEndpointSchedule(Base):
    # 既存フィールド...
    
    # Cron対応のため追加
    schedule_type: Mapped[str] = mapped_column(String(20), default="daily")  # daily, cron, interval
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "0 8 * * *"
    
    # 複数時刻対応
    execution_times: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)  # {"times": ["08:00", "12:00", "18:00"]}
```

## 3. スケジュールサービスの更新

```python
# app/services/schedule_service.py
from redbeat import RedBeatSchedulerEntry
from celery.schedules import crontab, schedule
import redis

class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = redis.from_url(settings.REDIS_URL)
    
    async def create_or_update_schedule(
        self,
        endpoint_id: int,
        schedule_config: Dict
    ) -> APIEndpointSchedule:
        """動的スケジュール作成/更新"""
        
        # DBに保存
        db_schedule = await self._save_to_database(endpoint_id, schedule_config)
        
        # Redbeatに登録
        await self._update_redbeat_schedule(endpoint_id, schedule_config)
        
        return db_schedule
    
    async def _update_redbeat_schedule(
        self,
        endpoint_id: int,
        config: Dict
    ):
        """Redbeatスケジュールを更新"""
        entry_name = f"sync_companies_{endpoint_id}"
        
        # スケジュールオブジェクト作成
        if config['schedule_type'] == 'cron':
            schedule_obj = crontab(
                minute=config.get('minute', '*'),
                hour=config.get('hour', '*'),
                day_of_week=config.get('day_of_week', '*'),
                day_of_month=config.get('day_of_month', '*'),
                month_of_year=config.get('month_of_year', '*')
            )
        elif config['schedule_type'] == 'daily':
            # JSTをUTCに変換
            jst_hour, jst_minute = map(int, config['time'].split(':'))
            utc_hour = (jst_hour - 9) % 24
            schedule_obj = crontab(hour=utc_hour, minute=jst_minute)
        
        # Redbeatエントリー作成/更新
        entry = RedBeatSchedulerEntry(
            name=entry_name,
            task='sync_listed_companies',
            schedule=schedule_obj,
            args=['scheduled'],
            options={
                'queue': 'default',
                'expires': 3600,
            },
            app=celery_app
        )
        entry.save()
    
    async def delete_schedule(self, endpoint_id: int):
        """スケジュール削除"""
        entry_name = f"sync_companies_{endpoint_id}"
        
        # Redbeatから削除
        try:
            entry = RedBeatSchedulerEntry.from_key(
                f"{celery_app.conf.redbeat_key_prefix}{entry_name}",
                app=celery_app
            )
            entry.delete()
        except KeyError:
            pass
        
        # DBから削除
        await self._delete_from_database(endpoint_id)
```

## 4. UI の拡張

### スケジュール設定フォーム
```html
<!-- templates/partials/schedule_form.html -->
<div class="schedule-form">
    <select name="schedule_type" hx-trigger="change" hx-post="/api/v1/schedule/preview">
        <option value="daily">毎日</option>
        <option value="weekly">毎週</option>
        <option value="monthly">毎月</option>
        <option value="cron">カスタム (Cron)</option>
    </select>
    
    <div id="schedule-config">
        <!-- 動的にフォームを切り替え -->
    </div>
    
    <div id="schedule-preview">
        <!-- 次回実行予定を表示 -->
    </div>
</div>
```

### Cron式ビルダー
```javascript
// static/js/cron-builder.js
class CronBuilder {
    constructor() {
        this.minute = '*';
        this.hour = '*';
        this.dayOfMonth = '*';
        this.month = '*';
        this.dayOfWeek = '*';
    }
    
    setDaily(time) {
        const [hour, minute] = time.split(':');
        this.hour = hour;
        this.minute = minute;
        return this.toString();
    }
    
    setWeekly(dayOfWeek, time) {
        const [hour, minute] = time.split(':');
        this.hour = hour;
        this.minute = minute;
        this.dayOfWeek = dayOfWeek;
        return this.toString();
    }
    
    toString() {
        return `${this.minute} ${this.hour} ${this.dayOfMonth} ${this.month} ${this.dayOfWeek}`;
    }
}
```

## 5. API エンドポイント

```python
# app/api/v1/endpoints/schedules.py
@router.post("/schedules")
async def create_schedule(
    request: ScheduleCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """スケジュール作成（即座に反映）"""
    service = ScheduleService(db)
    schedule = await service.create_or_update_schedule(
        endpoint_id=request.endpoint_id,
        schedule_config=request.config
    )
    return schedule

@router.get("/schedules/preview")
async def preview_schedule(
    cron_expression: str
):
    """Cron式から次回実行時刻を計算"""
    schedule = crontab(*cron_expression.split())
    next_runs = []
    
    current = datetime.now(pytz.UTC)
    for _ in range(5):  # 次の5回分
        next_run = schedule.remaining_estimate(current)
        current = current + next_run
        next_runs.append(current.astimezone(pytz.timezone('Asia/Tokyo')))
    
    return {"next_runs": next_runs}
```

## 6. 移行手順

1. **依存関係インストール**
   ```bash
   pip install celery-redbeat
   ```

2. **既存スケジュールの移行**
   ```python
   # migration script
   async def migrate_schedules():
       schedules = await get_all_schedules()
       for schedule in schedules:
           await create_redbeat_entry(schedule)
   ```

3. **Beat再起動**
   ```bash
   docker-compose down beat
   docker-compose up -d beat
   ```

## 7. 監視とログ

```python
# app/services/schedule_monitor.py
class ScheduleMonitor:
    async def get_active_schedules(self):
        """アクティブなスケジュール一覧"""
        pattern = f"{celery_app.conf.redbeat_key_prefix}*"
        keys = self.redis_client.keys(pattern)
        
        schedules = []
        for key in keys:
            entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
            schedules.append({
                'name': entry.name,
                'task': entry.task,
                'schedule': str(entry.schedule),
                'last_run': entry.last_run_at,
                'total_runs': entry.total_run_count
            })
        return schedules
```

## まとめ

この実装により：
- ✅ UIから動的にスケジュール設定可能
- ✅ 変更が即座に反映（再起動不要）
- ✅ Cron形式の複雑なスケジュールに対応
- ✅ 既存のRedisインフラを活用
- ✅ スケジュールの可視化と監視が容易