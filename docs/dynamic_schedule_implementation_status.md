# 動的スケジュール管理機能 実装状況

## 概要
Celery Beatの定期実行スケジュールをUIから動的に管理できる機能を実装しました。

## 実装日
- 初回実装: 2025-07-13（上場企業一覧同期）
- 拡張実装: 2025-07-18（日次株価データ同期）
- UI統合改善: 2025-07-18（エンドポイント一覧UI改善、上場企業一覧詳細画面改修）

## 実装内容

### 1. Redbeat統合
- `celery-redbeat` パッケージを導入
- RedBeatSchedulerを使用してRedisベースの動的スケジュール管理を実現
- サービス再起動なしでスケジュール変更が可能に

### 2. スケジュール管理サービス
- `RedbeatScheduleService` を実装
- タイムゾーン対応（内部UTC、表示JST）
- スケジュールのCRUD操作をサポート

### 3. UI統合
- APIエンドポイント管理画面から定期実行時刻を設定可能
- 実行履歴で「manual」と「scheduled」を区別して表示
- 実行モード表示をスケジュール設定に基づいて動的に更新
- エンドポイント一覧の操作ボタンを削除し、詳細パネルに機能を統合（2025-07-18）
- 行クリックで詳細表示、視覚的フィードバックを追加

### 4. 動作確認済み機能

#### 上場企業一覧同期
- UIからの定期実行時刻設定（例：8:47に設定）
- 設定時刻での自動実行（8:47:00に正確に実行）
- 実行履歴への記録（実行タイプ: scheduled）
- 実行モード表示の動的更新（定期実行/手動のみ）
- 詳細画面にスケジュール管理機能を統合（2025-07-18）
  - スケジュールの作成、編集、削除、有効/無効切り替え
  - 実行履歴の表示とリアルタイム更新
  - 手動同期の進捗表示

#### 日次株価データ同期（2025-07-18追加）
- 独立したスケジュール管理機能を実装
- 複数のスケジュールを同時に管理可能
- 相対日付プリセット機能（過去7日、30日、90日、今月、先月、年初来）
- 実行時に日付を動的計算（実行時点から相対的に計算）
- スケジュールの有効/無効切り替え
- 16:08に設定したスケジュールが正確に実行されることを確認
- 編集・削除がRedBeatに即座に反映されることを確認

## 技術詳細

### アーキテクチャ
```
UI (HTMX) → FastAPI → RedbeatScheduleService → Redis (Redbeat)
                                                    ↓
                                              Celery Beat
```

### 主要コンポーネント
1. **RedbeatScheduleService** (`app/services/redbeat_schedule_service.py`)
   - スケジュール管理のビジネスロジック
   - タイムゾーン変換（JST ↔ UTC）

2. **DailyQuotesScheduleService** (`app/services/daily_quotes_schedule_service.py`)
   - 日次株価データ専用のスケジュール管理サービス
   - 相対日付プリセットの動的計算機能
   - RedBeatエントリーの作成・更新・削除

3. **APIエンドポイント**
   - 上場企業: PUT /api/v1/companies/sync/schedule
   - 日次株価: /api/v1/daily-quotes/schedules (CRUD操作)

4. **UI更新**
   - 上場企業: 実行モード表示の動的判定
   - 日次株価: 専用のスケジュール管理画面（一覧、作成、編集、削除）

### データモデル
- `APIEndpointSchedule`: 上場企業同期のスケジュール設定を保存
- `DailyQuoteSchedule`: 日次株価データ同期のスケジュール設定を保存
- Redbeat: Redisにスケジュール情報を保存（キー形式: `stockura:schedule:{name}`）

## 今後の拡張可能性
1. ~~Cron形式でのスケジュール指定~~ → 日次株価で実装済み（日次、週次、月次対応）
2. ~~複数のスケジュールパターン（週次、月次など）~~ → 日次株価で実装済み
3. スケジュール実行条件の追加（特定条件下でのみ実行など）
4. スケジュール実行結果の通知機能
5. スケジュール依存関係の管理

## 関連ファイル

### 共通
- `/app/core/celery_app.py` - Celery設定（Redbeat統合）
- `/docker-compose.yml` - Beat設定更新
- `/requirements.txt` - celery-redbeat追加

### 上場企業一覧同期
- `/app/services/redbeat_schedule_service.py` - スケジュール管理サービス
- `/app/api/v1/endpoints/companies.py` - スケジュール更新API
- `/app/api/v1/views/api_endpoints.py` - UI表示ロジック

### 日次株価データ同期
- `/app/models/daily_quote_schedule.py` - スケジュールモデル
- `/app/services/daily_quotes_schedule_service.py` - スケジュール管理サービス
- `/app/api/v1/endpoints/daily_quotes_schedules.py` - スケジュールCRUD API
- `/app/tasks/daily_quotes_tasks.py` - スケジュール実行タスク
- `/app/templates/partials/api_endpoints/daily_quotes_schedule_*.html` - UI部品

### UI改善（2025-07-18）
- `/app/templates/partials/api_endpoints/endpoint_row.html` - エンドポイント一覧の行表示
- `/app/templates/partials/api_endpoints/endpoint_details_companies.html` - 上場企業一覧詳細画面
- `/app/api/v1/views/api_endpoints.py` - 共通関数による統計情報取得

## 注意点

### 共通
- タイムゾーンは内部処理でUTC、UI表示でJSTに統一
- Redisが必須（Redbeatがスケジュール情報を保存）
- Celery Beatコンテナの起動が必要（`docker compose up -d beat`）

### 上場企業一覧同期
- execution_modeフィールドは使用せず、スケジュール設定の有無で判定
- APIEndpointExecutionLogテーブルから実行統計を取得

### 日次株価データ同期
- 相対日付プリセットは実行時点で動的に計算される
- スケジュールの編集・削除は即座にRedBeatに反映される
- is_enabledをfalseにするとRedisからスケジュールが削除される
- Workerを再起動した場合、タスクの再登録が必要
- DailyQuotesSyncHistoryテーブルから実行統計を計算

### UI設計の原則
- エンドポイント一覧はシンプルに保ち、詳細機能は詳細パネルに集約
- 異なるエンドポイントタイプでも統一された体験を提供
- 共通関数により将来の拡張性を確保

## 動作確認結果（2025-07-18）

### 日次株価データ同期のテスト
1. 16:08にスケジュールを設定
2. Celery Beatコンテナを起動
3. 16:08:00に自動実行されることを確認
4. 実行履歴の記録を確認（22,053件処理、約43秒）
5. 次回実行予定が翌日16:08に設定されていることを確認
6. スケジュール編集（時刻変更、有効/無効切り替え）がRedisに反映されることを確認
7. スケジュール削除でRedisからも削除されることを確認

### UI統合改善の実装
1. エンドポイント一覧から実行ボタンと設定ボタンを削除
2. 詳細パネルに全機能を統合
3. 実行モード表示の共通化実装
   - `_get_endpoint_schedule_info()` - スケジュール情報取得
   - `_get_endpoint_execution_stats()` - 実行統計情報取得
4. 日次株価データの統計情報表示を実装
   - 最終実行、データ件数、成功率が正しく表示されることを確認
5. 上場企業一覧詳細画面の改修
   - 日次株価データと同様のスケジュール管理UIを実装
   - スケジュールの作成、編集、削除、有効/無効切り替えが動作することを確認
