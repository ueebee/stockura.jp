# 上場企業一覧同期機能 実装設計書

## 概要
上場企業一覧を毎日定期的に同期する機能の実装設計書です。シンプルで運用しやすい設計を目指します。

## 基本要件
- **定期実行**: 1日1回（デフォルト: JST 11:30）
- **手動実行**: UI上から任意のタイミングで実行可能
- **同期方式**: 毎日フル同期（差分取得なし）
- **パラメータ**: 最小限の設定のみ
- **実行時間変更**: ユーザーが設定画面から変更可能
- **リアルタイム進捗表示**: 同期実行中の進捗をリアルタイムで表示
- **動的実行履歴更新**: ページリロードなしで実行履歴を更新

## UI設計

### 1. データソース管理画面での表示
```
┌─────────────────────────────────────────────────────────┐
│ J-Quants - 上場企業一覧                                   │
├─────────────────────────────────────────────────────────┤
│ 状態: ● 有効                                             │
│                                                          │
│ 定期実行: 毎日 05:00 (JST)  [変更]                      │
│                                                          │
│ 最終同期: 2025-07-10 05:02:34                           │
│ 同期件数: 3,854 社                                      │
│ 次回実行: 2025-07-11 05:00:00                           │
│                                                          │
│ [今すぐ同期] [実行履歴を見る]                           │
└─────────────────────────────────────────────────────────┘
```

### 2. 定期実行時間の変更UI
```
┌─────────────────────────────────────────────────────────┐
│ 定期実行時間の設定                                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 実行時間: [05] : [00] (JST)                             │
│                                                          │
│ ※ 毎日指定時刻に自動実行されます                         │
│ ※ 処理時間を考慮して、取引時間外を推奨                   │
│                                                          │
│ [保存] [キャンセル]                                      │
└─────────────────────────────────────────────────────────┘
```

### 3. 実行状況モニタリング（実装済み）
```
┌─────────────────────────────────────────────────────────┐
│ 処理を開始しています...                                  │
├─────────────────────────────────────────────────────────┤
│ 🔄 上場企業データを取得中...                             │
│                                                          │
│ [プログレスバーまたはスピナーアニメーション]            │
│                                                          │
└─────────────────────────────────────────────────────────┘

↓ 完了後

┌─────────────────────────────────────────────────────────┐
│ ✅ 同期が完了しました                                    │
├─────────────────────────────────────────────────────────┤
│ 同期件数: 4,411件                                       │
│ 処理時間: 4.5秒                                         │
└─────────────────────────────────────────────────────────┘
```

## バックエンド設計

### 1. データモデル

#### ApiEndpointSchedule（新規追加）
```python
class ApiEndpointSchedule(Base):
    """APIエンドポイントの実行スケジュール"""
    __tablename__ = "api_endpoint_schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("api_endpoints.id"))
    
    # スケジュール設定
    is_enabled: Mapped[bool] = mapped_column(default=True)
    schedule_type: Mapped[str] = mapped_column(String(20), default="daily")  # daily only for now
    execution_time: Mapped[time] = mapped_column(Time, default=time(5, 0))  # デフォルト 5:00
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Tokyo")
    
    # 実行履歴
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_execution_status: Mapped[Optional[str]] = mapped_column(String(20))  # success/failed
    last_sync_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # メタデータ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    endpoint: Mapped["ApiEndpoint"] = relationship(back_populates="schedule")
```

### 2. サービス層

#### CompanySyncService（シンプル版）
```python
class CompanySyncService:
    """上場企業同期サービス（シンプル実装）"""
    
    def __init__(self, db: AsyncSession, jquants_client: JQuantsClient):
        self.db = db
        self.jquants_client = jquants_client
    
    async def sync_all_companies(self) -> Dict[str, Any]:
        """全上場企業を同期（フル同期）"""
        start_time = datetime.now()
        
        try:
            # 1. J-Quantsから全銘柄取得
            companies_data = await self.jquants_client.get_all_listed_companies()
            
            # 2. 既存の全企業を非アクティブ化
            await self.db.execute(
                update(Company).values(is_active=False)
            )
            
            # 3. 取得データを一括更新（upsert）
            sync_count = 0
            for company_data in companies_data:
                await self._upsert_company(company_data)
                sync_count += 1
            
            await self.db.commit()
            
            # 4. 実行履歴を更新
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "success",
                "sync_count": sync_count,
                "duration": duration,
                "executed_at": start_time
            }
            
        except Exception as e:
            await self.db.rollback()
            return {
                "status": "failed",
                "error": str(e),
                "executed_at": start_time
            }
    
    async def _upsert_company(self, company_data: Dict):
        """企業情報をupsert"""
        stmt = insert(Company).values(
            code=company_data["Code"],
            company_name=company_data["CompanyName"],
            company_name_english=company_data.get("CompanyNameEnglish"),
            sector17_code=company_data.get("Sector17Code"),
            sector33_code=company_data.get("Sector33Code"),
            scale_category=company_data.get("ScaleCategory"),
            market_code=company_data.get("MarketCode"),
            is_active=True,
            reference_date=datetime.now().date()
        ).on_conflict_do_update(
            index_elements=["code"],
            set_={
                "company_name": company_data["CompanyName"],
                "company_name_english": company_data.get("CompanyNameEnglish"),
                "sector17_code": company_data.get("Sector17Code"),
                "sector33_code": company_data.get("Sector33Code"),
                "scale_category": company_data.get("ScaleCategory"),
                "market_code": company_data.get("MarketCode"),
                "is_active": True,
                "reference_date": datetime.now().date(),
                "updated_at": datetime.now()
            }
        )
        await self.db.execute(stmt)
```

### 3. Celeryタスク（実装済み - 重要な変更点あり）

#### tasks/company_tasks.py
```python
from app.core.celery_app import celery_app
from app.services.company_sync_service import CompanySyncService
from app.models.api_endpoint import ApiEndpointSchedule

@celery_app.task(bind=True, name="sync_listed_companies")
def sync_listed_companies(self, execution_type: str = "manual"):
    """上場企業一覧の同期タスク（シンプル版）"""
    
    async def _sync():
        # 重要: 各タスク実行で新しいセッションメーカーを作成
        # これにより、イベントループ間での接続再利用問題を回避
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
                sync_service = CompanySyncService(async_db, data_source_service, jquants_client_manager)
                
                # 進捗更新
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': 0,
                        'total': 1,
                        'message': '上場企業データを取得中...'
                    }
                )
                
                # 同期実行
                result = await sync_service.sync_all_companies_simple()
                return result
        finally:
            # エンジンをクリーンアップ
            await task_async_engine.dispose()
    
    # 新しいイベントループで実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_sync())
    finally:
        loop.close()
    
    # 実行ログの作成（同期セッションで実行）
    # ... 実行ログ作成処理 ...
    
    return result
```

#### 重要な実装上の注意点
1. **Celeryワーカーのプール設定**: `solo`モードを使用（docker-compose.yml）
   ```yaml
   worker:
     command: celery -A app.core.celery_app worker --loglevel=info --pool=solo
   ```

2. **非同期処理の分離**: 各タスク実行で独自のイベントループとデータベース接続を作成

### 4. スケジュール管理

#### ScheduleService
```python
class ScheduleService:
    """スケジュール管理サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_schedule_time(
        self, 
        endpoint_id: int, 
        execution_time: time
    ) -> ApiEndpointSchedule:
        """実行時間を更新"""
        schedule = await self.db.query(ApiEndpointSchedule).filter(
            ApiEndpointSchedule.endpoint_id == endpoint_id
        ).first()
        
        if not schedule:
            raise ValueError("Schedule not found")
        
        schedule.execution_time = execution_time
        schedule.updated_at = datetime.now()
        
        # Celery Beatのスケジュールを更新
        self._update_celery_beat_schedule(endpoint_id, execution_time)
        
        await self.db.commit()
        return schedule
    
    def _update_celery_beat_schedule(self, endpoint_id: int, execution_time: time):
        """Celery Beatのスケジュールを動的更新"""
        from celery.schedules import crontab
        
        # スケジュールエントリを更新
        schedule_name = f"sync_companies_{endpoint_id}"
        
        celery_app.conf.beat_schedule[schedule_name] = {
            'task': 'sync_listed_companies',
            'schedule': crontab(
                hour=execution_time.hour,
                minute=execution_time.minute
            ),
            'args': [],
            'options': {
                'timezone': 'Asia/Tokyo'
            }
        }
```

### 5. API エンドポイント（実装済み）

#### 手動実行エンドポイント（HTMXに対応）
```python
@router.post("/sync-companies-action")
async def sync_companies_action(
    request: Request,
    db: Session = Depends(get_db),
):
    """上場企業一覧を手動で同期（HTMX用）"""
    # Celeryタスクを即座に実行
    task = sync_listed_companies.delay(execution_type="manual")
    
    # HTMXレスポンスとしてタスクIDをJSONで返す
    return HTMLResponse(
        content=f'<div id="sync-task-response" data-task-id="{task.id}"></div>'
    )
```

#### タスク状態確認エンドポイント（実装済み）
```python
@router.get("/sync/task/{task_id}")
async def get_sync_task_status(task_id: str):
    """同期タスクの状態を取得（リアルタイム進捗表示用）"""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    if result.state == 'PENDING':
        response = {
            'state': result.state,
            'current': 0,
            'total': 1,
            'status': '処理待機中...'
        }
    elif result.state == 'PROGRESS':
        response = {
            'state': result.state,
            'current': result.info.get('current', 0),
            'total': result.info.get('total', 1),
            'status': result.info.get('message', '処理中...')
        }
    elif result.state == 'SUCCESS':
        response = {
            'state': result.state,
            'current': 1,
            'total': 1,
            'status': '同期完了',
            'result': result.info
        }
    else:  # FAILURE
        response = {
            'state': result.state,
            'current': 1,
            'total': 1,
            'status': f'エラー: {str(result.info)}',
            'error': str(result.info)
        }
    
    return response
```

#### 実行履歴取得エンドポイント（実装済み）
```python
@router.get("/data-sources/{data_source_id}/endpoints/{endpoint_id}/execution-history", 
           response_class=HTMLResponse)
async def get_endpoint_execution_history(
    request: Request,
    data_source_id: int,
    endpoint_id: int,
    db: Session = Depends(get_db),
):
    """エンドポイントの実行履歴のみを取得（HTMX用）"""
    # 実行履歴を取得してHTMLレスポンスを返す
    # ページリロードなしで実行履歴テーブルを更新
```

#### スケジュール更新エンドポイント
```python
@router.put("/api/v1/companies/schedule")
async def update_company_sync_schedule(
    execution_time: time,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """同期スケジュールを更新"""
    schedule_service = ScheduleService(db)
    
    updated_schedule = await schedule_service.update_schedule_time(
        endpoint_id=LISTED_COMPANIES_ENDPOINT_ID,
        execution_time=execution_time
    )
    
    return {
        "status": "success",
        "execution_time": updated_schedule.execution_time.strftime("%H:%M"),
        "timezone": updated_schedule.timezone
    }
```

## 実装の流れ

### フェーズ1: 基本機能実装（✅ 完了）
1. ApiEndpointScheduleモデルの追加
2. CompanySyncServiceの実装（シンプル版）
3. Celeryタスクの実装

### フェーズ2: UI実装（✅ 完了）
1. データソース画面での表示
2. 手動実行ボタンの実装
3. 実行履歴表示
4. リアルタイム進捗表示（JavaScript実装）
5. 動的実行履歴更新（HTMX対応）

### フェーズ3: スケジュール管理（✅ 完了）
1. スケジュール変更UIの実装
2. ScheduleServiceの実装
3. Celery Beat連携

### フェーズ4: モニタリング（✅ 完了）
1. 実行状況のリアルタイム表示
2. エラーハンドリング
3. 通知機能（オプション）

## 技術的考慮事項

### 1. Celery Beatの動的スケジュール更新
- Redisをバックエンドとして使用
- スケジュール変更時にBeatを再起動不要

### 2. 同期処理の最適化
- バルクインサート/アップデート
- トランザクション管理
- メモリ効率を考慮したバッチ処理

### 3. エラーハンドリング
- J-Quants API障害時のリトライ
- 部分的な失敗の処理
- ユーザーへの適切な通知

### 4. パフォーマンス
- 4,000件程度の企業データを5分以内で処理
- UIの応答性を保つための非同期処理
- 進捗状況のリアルタイム更新

### 5. 非同期処理の注意点（重要）
- **イベントループの競合問題**: Celeryワーカーで非同期処理を使用する際の問題
  - 問題: 複数のタスク実行で同じイベントループ/データベース接続が再利用される
  - 解決策: 各タスク実行で独自のイベントループとデータベース接続を作成
- **Celeryワーカープール**: `solo`モードを使用してシングルスレッド実行を保証
- **データベース接続管理**: タスク完了後に必ず接続をクリーンアップ

## 実装で遭遇した問題と解決策

### 1. リアルタイム進捗表示の実装
- **問題**: HTMXレスポンスがタスクIDを適切に処理できない
- **解決**: 
  - 専用の隠しdiv要素（`#sync-task-response`）でタスクIDを受け取る
  - JavaScriptのイベントリスナーでタスクIDを抽出して処理

### 2. 交互に成功・失敗を繰り返す問題
- **問題**: 「Task attached to a different loop」エラーが発生
- **原因**: 非同期データベース接続がイベントループ間で再利用される
- **解決**: 
  1. Celeryワーカーのプールモードを`fork`から`solo`に変更
  2. 各タスク実行で独自の非同期エンジンとセッションメーカーを作成
  3. タスク完了後に非同期エンジンを適切にdispose()

### 3. 実行履歴の動的更新
- **問題**: 同期完了後にページ全体をリロードしていた
- **解決**: 
  - 実行履歴部分のみを取得する専用エンドポイントを作成
  - HTMXを使用して部分的な更新を実現