# 動的スケジュール管理機能 実装状況

## 概要
Celery Beatの定期実行スケジュールをUIから動的に管理できる機能を実装しました。

## 実装日
2025-07-13

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

### 4. 動作確認済み機能
- UIからの定期実行時刻設定（例：8:47に設定）
- 設定時刻での自動実行（8:47:00に正確に実行）
- 実行履歴への記録（実行タイプ: scheduled）
- 実行モード表示の動的更新（定期実行/手動のみ）

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

2. **APIエンドポイント** (`app/api/v1/endpoints/companies.py`)
   - PUT /api/v1/companies/sync/schedule
   - スケジュール更新用エンドポイント

3. **UI更新** (`app/api/v1/views/api_endpoints.py`)
   - 実行モード表示の動的判定
   - スケジュール情報に基づいて「定期実行」または「手動のみ」を表示

### データモデル
- `APIEndpointSchedule`: スケジュール設定を保存
- Redbeat: Redisにスケジュール情報を保存

## 今後の拡張可能性
1. Cron形式でのスケジュール指定
2. 複数のスケジュールパターン（週次、月次など）
3. スケジュール実行条件の追加（特定条件下でのみ実行など）

## 関連ファイル
- `/app/services/redbeat_schedule_service.py` - スケジュール管理サービス
- `/app/core/celery_app.py` - Celery設定（Redbeat統合）
- `/app/api/v1/endpoints/companies.py` - スケジュール更新API
- `/app/api/v1/views/api_endpoints.py` - UI表示ロジック
- `/docker-compose.yml` - Beat設定更新
- `/requirements.txt` - celery-redbeat追加

## 注意点
- タイムゾーンは内部処理でUTC、UI表示でJSTに統一
- execution_modeフィールドは使用せず、スケジュール設定の有無で判定
- Redisが必須（Redbeatがスケジュール情報を保存）