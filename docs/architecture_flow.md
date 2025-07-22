# Stockura アーキテクチャ図 - 処理フロー

## 1. 手動同期実行フロー（上場企業一覧）

```mermaid
sequenceDiagram
    participant B as Browser
    participant W as Web (FastAPI)
    participant R as Redis
    participant C as Celery Worker
    participant DB as PostgreSQL
    participant API as J-Quants API

    B->>W: POST /data-sources/{id}/endpoints/{id}/execute
    Note over W: app/api/v1/views/api_endpoints/companies.py
    W->>W: execute_companies_endpoint()
    W->>DB: APIEndpointExecutionLog作成
    W->>R: sync_listed_companies.delay("manual")
    W-->>B: 実行結果HTML返却

    R->>C: タスク取得
    Note over C: app/tasks/company_tasks.py
    C->>C: sync_listed_companies(execution_type="manual")
    C->>DB: DataSourceService経由でデータソース取得
    C->>C: CompanySyncService初期化
    Note over C: app/services/company_sync_service.py
    C->>C: sync_companies()
    C->>DB: CompanySyncHistory作成 (status="running")
    
    C->>API: get_all_listed_companies()
    API-->>C: 企業データ (4,416件)
    
    C->>C: _save_companies_data()
    loop 各企業データ
        C->>DB: Company upsert
    end
    
    C->>DB: CompanySyncHistory更新 (status="completed")
    C->>DB: APIEndpointの統計情報更新
    
    B->>W: HTMXで実行履歴更新
    W->>DB: CompanySyncHistory取得
    W-->>B: 実行履歴HTML返却
```

## 2. 定期実行スケジュール設定フロー

```mermaid
sequenceDiagram
    participant B as Browser
    participant W as Web (FastAPI)
    participant DB as PostgreSQL
    participant R as Redis (RedBeat)

    B->>W: POST /api/v1/companies/sync/schedule
    Note over W: app/api/v1/endpoints/companies.py
    W->>W: create_company_sync_schedule()
    W->>DB: APIEndpoint取得 (data_type="listed_companies")
    W->>W: RedbeatScheduleService.create_or_update_schedule()
    Note over W: app/services/redbeat_schedule_service.py
    
    W->>DB: APIEndpointSchedule作成/更新
    W->>R: RedBeatSchedulerEntry作成
    Note over R: sync_companies_1タスク登録
    R-->>W: 登録完了
    
    W-->>B: スケジュール作成結果JSON
    B->>B: ページリロード
```

## 3. 定期実行フロー（Celery Beat）

```mermaid
sequenceDiagram
    participant B as Celery Beat
    participant R as Redis
    participant C as Celery Worker
    participant DB as PostgreSQL
    participant API as J-Quants API

    loop 毎分チェック
        B->>R: スケジュール確認
        R-->>B: sync_companies_1 (21:58 JST)
    end
    
    Note over B: 実行時刻到達
    B->>R: sync_listed_companies("scheduled")
    
    R->>C: タスク取得
    C->>C: sync_listed_companies(execution_type="scheduled")
    Note over C: 以降は手動実行と同じフロー
    C->>DB: CompanySyncHistory作成 (execution_type="scheduled")
    C->>API: 企業データ取得
    C->>DB: データ更新
```

## 4. 実行履歴表示フロー

```mermaid
sequenceDiagram
    participant B as Browser
    participant W as Web (FastAPI)
    participant DB as PostgreSQL

    B->>W: GET /data-sources/{id}/endpoints/{id}/execution-history
    Note over W: app/api/v1/views/api_endpoints_main.py
    W->>W: get_endpoint_execution_history()
    
    alt endpoint.data_type == "listed_companies"
        W->>DB: CompanySyncHistory取得 (ORDER BY started_at DESC)
        W->>W: companies_sync_history_rows.htmlレンダリング
    else その他のエンドポイント
        W->>DB: APIEndpointExecutionLog取得
        W->>W: execution_history_rows.htmlレンダリング
    end
    
    W-->>B: 実行履歴HTML (HTMXレスポンス)
    Note over B: 同期タイプ/実行タイプの2段バッジ表示
```

## 5. コンポーネント関係図

```mermaid
graph TB
    subgraph "Frontend Layer"
        HTML[HTML/HTMX]
        JS[JavaScript]
    end
    
    subgraph "Web Layer (FastAPI)"
        Router[APIRouter]
        Views[Views]
        Templates[Jinja2 Templates]
    end
    
    subgraph "Service Layer"
        DSS[DataSourceService]
        CSS[CompanySyncService]
        DQS[DailyQuotesSyncService]
        RSS[RedbeatScheduleService]
        BSS[BaseSyncService]
    end
    
    subgraph "Task Layer (Celery)"
        CT[company_tasks.py]
        DQT[daily_quotes_tasks.py]
        Beat[Celery Beat]
    end
    
    subgraph "Model Layer"
        Company[Company]
        CSH[CompanySyncHistory]
        AE[APIEndpoint]
        AES[APIEndpointSchedule]
        AEL[APIEndpointExecutionLog]
    end
    
    subgraph "External"
        JQ[J-Quants API]
        Redis[(Redis)]
        PG[(PostgreSQL)]
    end
    
    HTML --> Router
    Router --> Views
    Views --> Templates
    Views --> DSS
    Views --> RSS
    
    CT --> CSS
    CT --> DSS
    CSS --> BSS
    DQS --> BSS
    
    Beat --> Redis
    CT --> Redis
    
    CSS --> Company
    CSS --> CSH
    Views --> AE
    Views --> AES
    Views --> AEL
    
    CSS --> JQ
    
    DSS --> PG
    CSS --> PG
    RSS --> Redis
```

## 6. ファイル構成と責務

### Web層
- `app/api/v1/views/api_endpoints_main.py` - メインルーター、共通処理
- `app/api/v1/views/api_endpoints/companies.py` - 企業エンドポイント固有処理
- `app/api/v1/endpoints/companies.py` - 企業API（同期実行、スケジュール管理）

### サービス層
- `app/services/base_sync_service.py` - 同期サービス基底クラス
- `app/services/company_sync_service.py` - 企業データ同期ロジック
- `app/services/redbeat_schedule_service.py` - スケジュール管理

### タスク層
- `app/tasks/company_tasks.py` - 企業同期Celeryタスク
- `app/core/celery_app.py` - Celery設定

### モデル層
- `app/models/company.py` - Company, CompanySyncHistory
- `app/models/api_endpoint.py` - APIEndpoint, APIEndpointSchedule, APIEndpointExecutionLog

### テンプレート層
- `app/templates/partials/api_endpoints/endpoint_details_companies.html` - 企業詳細画面
- `app/templates/partials/api_endpoints/companies_sync_history_rows.html` - 実行履歴行

## 7. データフロー

1. **ユーザー操作** → HTMX → FastAPI View
2. **View** → Service層（ビジネスロジック）
3. **Service** → Celeryタスク（非同期実行）
4. **Celeryタスク** → 外部API/DB操作
5. **結果** → DB保存 → HTMX更新 → 画面反映

## 8. 重要な処理ポイント

### execution_typeの流れ
1. 手動実行: `sync_listed_companies.delay("manual")`
2. 定期実行: Celery Beatが`sync_listed_companies("scheduled")`を実行
3. タスク内で`CompanySyncService.sync_companies(execution_type=...)`
4. `CompanySyncHistory`に`execution_type`が記録される
5. 実行履歴画面で2段バッジ（sync_type/execution_type）として表示

### スケジュール管理
1. `APIEndpointSchedule` - DB上のスケジュール設定
2. `RedBeatSchedulerEntry` - Redis上のCelery Beat用エントリ
3. 両者を`RedbeatScheduleService`が同期管理