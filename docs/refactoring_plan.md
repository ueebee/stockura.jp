# リファクタリング改善計画書

## 概要

本ドキュメントは、Stockuraプロジェクトの現在の実装を分析し、コードの品質、保守性、パフォーマンスを向上させるためのリファクタリング項目をまとめたものです。

## 実装手順

- 本ドキュメントに基づき順番に実装を行うこと
- 実装が完了したらテストを実行すること
- テストの中にはデータ取得に関わる部分が存在するため、ブラウザ経由での動作確認を挟むこと
- 実装が完了したら本ドキュメントを更新すること
    - どこまで実装したか記載すること

## 1. 重複コードの統合

### 1.1 エンドポイント詳細テンプレートの共通化 ✅ 完了 (2025-07-19)

**実装済み内容**
- 共通ベーステンプレート `endpoint_details_base.html` を作成
- `endpoint_details_companies.html` と `endpoint_details_daily_quotes.html` を共通ベースを継承する形に変更
- 共通部分（ヘッダー、定期実行スケジュール、実行履歴）を基底テンプレートに統合
- データタイプ固有の部分はブロック定義で実装

**実装したファイル**
```
app/templates/partials/api_endpoints/
├── endpoint_details_base.html         # 共通ベーステンプレート（新規作成）
├── endpoint_details_companies.html    # 企業同期用（共通ベース継承に変更）
└── endpoint_details_daily_quotes.html  # 日次株価用（共通ベース継承に変更）
```

**効果**
- コードの重複を約60%削減
- メンテナンス性の向上
- 新しいエンドポイントタイプの追加が容易に

**動作確認済み**
- 企業同期エンドポイントの詳細表示 ✓
- 日次株価エンドポイントの詳細表示 ✓
- HTMXによる動的読み込み ✓

### 1.2 スケジュール管理UIの統一

**現状の問題点**
- 企業同期と日次株価で異なるスケジュール管理UI
- 類似機能で異なる実装

**改善案**
- 共通のスケジュールコンポーネント `schedule_manager.html` を作成
- パラメータでカスタマイズ可能な設計

## 2. サービスレイヤーの改善

### 2.1 基底クラスの導入

**現状の問題点**
- 各サービスクラスが独立して同様の機能を実装
- コードの重複とメンテナンスコストの増大

**改善案**
```python
# app/services/base_sync_service.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

class BaseSyncService(ABC):
    """同期サービスの基底クラス"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """ロガーのセットアップ"""
        import logging
        return logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """同期処理の実装（サブクラスで実装）"""
        pass

    def get_sync_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """同期履歴の取得（共通実装）"""
        # 共通の履歴取得ロジック
        pass

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """エラーハンドリング（共通実装）"""
        self.logger.error(f"Sync error: {error}", extra=context)
        # 共通のエラー記録処理
```

### 2.2 エラーハンドリングの統一

**現状の問題点**
- 各サービスで独自のエラーハンドリング実装
- ログフォーマットの不統一

**改善案**
```python
# app/core/exceptions.py
class SyncError(Exception):
    """同期処理の基底例外クラス"""
    pass

class APIError(SyncError):
    """API関連のエラー"""
    pass

class DataValidationError(SyncError):
    """データ検証エラー"""
    pass

# app/core/error_handler.py
class ErrorHandler:
    @staticmethod
    def handle_sync_error(error: Exception, service_name: str, context: Dict[str, Any]):
        """統一されたエラーハンドリング"""
        # エラーログの記録
        # メトリクスの送信
        # 通知の送信（必要に応じて）
```

## 3. API Viewsの整理

### 3.1 大規模ファイルの分割

**現状の問題点**
- `api_endpoints.py`が400行以上で可読性が低い
- 複数の責務が1つのファイルに集中

**改善案**
```
app/api/v1/views/
├── api_endpoints/
│   ├── __init__.py
│   ├── base.py              # 共通機能
│   ├── companies.py         # 企業関連
│   ├── daily_quotes.py      # 日次株価関連
│   └── common.py            # 共通ユーティリティ
```

### 3.2 統計情報取得の最適化

**現状の問題点**
```python
# 複数のクエリで統計情報を取得
latest_history = db.query(DailyQuotesSyncHistory).order_by(...).first()
latest_success = db.query(DailyQuotesSyncHistory).filter(...).first()
latest_error = db.query(DailyQuotesSyncHistory).filter(...).first()
```

**改善案**
```python
# 1つのクエリで必要な情報を取得
from sqlalchemy import func, case

stats = db.query(
    func.max(DailyQuotesSyncHistory.started_at).label('last_execution'),
    func.max(case(
        (DailyQuotesSyncHistory.status == 'completed', DailyQuotesSyncHistory.started_at),
        else_=None
    )).label('last_success'),
    func.count(DailyQuotesSyncHistory.id).label('total_executions'),
    func.sum(case(
        (DailyQuotesSyncHistory.status == 'completed', 1),
        else_=0
    )).label('successful_executions')
).first()
```

## 4. フロントエンドの改善

### 4.1 JavaScriptコードの整理

**現状の問題点**
- テンプレート内にインラインJavaScriptが散在
- 再利用性が低い

**改善案**
```
app/static/js/
├── modules/
│   ├── schedule-manager.js    # スケジュール管理
│   ├── sync-handler.js        # 同期処理
│   └── progress-tracker.js    # 進捗表示
└── main.js                    # エントリーポイント
```

**実装例**
```javascript
// app/static/js/modules/sync-handler.js
export class SyncHandler {
    constructor(endpoint) {
        this.endpoint = endpoint;
        this.progressElement = null;
    }

    async startSync() {
        this.showProgress();
        try {
            const response = await fetch(this.endpoint, { method: 'POST' });
            const result = await response.json();
            this.handleResult(result);
        } catch (error) {
            this.handleError(error);
        }
    }

    showProgress() {
        // 進捗表示の共通実装
    }
}
```

### 4.2 HTMXパターンの統一

**現状の問題点**
- 同様の処理で異なるHTMX属性の使い方
- 一貫性のない実装

**改善案**
```html
<!-- HTMXパターンガイドライン -->

<!-- パターン1: フォーム送信 -->
<form hx-post="/api/endpoint"
      hx-target="#result"
      hx-swap="innerHTML"
      hx-indicator="#spinner">
</form>

<!-- パターン2: 部分更新 -->
<div hx-get="/api/data"
     hx-trigger="every 30s"
     hx-target="this"
     hx-swap="outerHTML">
</div>

<!-- パターン3: モーダル操作 -->
<button hx-get="/modal/content"
        hx-target="#modal-container"
        hx-swap="innerHTML"
        hx-on::after-request="showModal()">
</button>
```

## 5. データベースクエリの最適化

### 5.1 N+1問題の解決

**現状の問題点**
```python
# エンドポイント一覧で関連データを個別に取得
endpoints = db.query(APIEndpoint).all()
for endpoint in endpoints:
    schedule = db.query(APIEndpointSchedule).filter_by(endpoint_id=endpoint.id).first()
    # N+1クエリ
```

**改善案**
```python
# Eager loadingを使用
from sqlalchemy.orm import joinedload

endpoints = db.query(APIEndpoint)\
    .options(joinedload(APIEndpoint.schedule))\
    .all()
```

### 5.2 インデックスの追加

**追加すべきインデックス**
```sql
-- 頻繁に使用されるクエリ用
CREATE INDEX idx_daily_quotes_sync_history_started_at
ON daily_quotes_sync_history(started_at DESC);

CREATE INDEX idx_daily_quotes_sync_history_status
ON daily_quotes_sync_history(status);

CREATE INDEX idx_api_endpoint_schedule_endpoint_id
ON api_endpoint_schedules(endpoint_id);

-- 複合インデックス
CREATE INDEX idx_daily_quotes_company_date
ON daily_quotes(company_id, quote_date DESC);
```

## 6. 設定管理の改善

### 6.1 スケジュール設定の一元化

**現状の問題点**
- 企業同期と日次株価で異なるスケジュール管理
- 設定の重複

**改善案**
```python
# app/models/base_schedule.py
class BaseSchedule(SQLModel):
    """スケジュールの基底モデル"""
    is_enabled: bool = Field(default=True)
    schedule_type: str = Field(...)  # daily, weekly, monthly
    execution_time: time = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """共通設定"""
        pass
```

## 7. テストの追加

### 7.1 サービスレイヤーのユニットテスト

**テスト構造**
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_company_sync_service.py
│   │   ├── test_daily_quotes_sync_service.py
│   │   └── test_base_sync_service.py
│   └── models/
│       └── test_schedule_models.py
└── integration/
    ├── test_sync_workflow.py
    └── test_schedule_execution.py
```

**テスト例**
```python
# tests/unit/services/test_company_sync_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.company_sync_service import CompanySyncService

class TestCompanySyncService:
    @pytest.fixture
    def service(self, db_session):
        return CompanySyncService(db_session)

    @patch('app.services.company_sync_service.JQuantsAPI')
    async def test_sync_companies_success(self, mock_api, service):
        # モックの設定
        mock_api.return_value.get_listed_companies.return_value = [
            {"code": "1234", "name": "Test Company"}
        ]

        # 実行
        result = await service.sync()

        # 検証
        assert result["status"] == "success"
        assert result["company_count"] == 1
```

## 8. 命名規則の統一

### 8.1 一貫性のある命名

**現状の問題点**
- `sync_history` vs `execution_log`
- `data_source` vs `datasource`
- `is_enabled` vs `is_active`

**命名規則ガイドライン**
```python
# モデル名: 単数形、PascalCase
class Company(SQLModel):
    pass

# テーブル名: 複数形、snake_case
__tablename__ = "companies"

# 関数名: 動詞で始まる、snake_case
def get_company_by_code(code: str):
    pass

# 変数名: 名詞、snake_case
company_count = 100
is_active = True  # ブール値は is_ prefix

# 定数: 大文字、snake_case
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
```

## 実装優先度

1. **高優先度**（1-2週間）
   - エラーハンドリングの統一
   - データベースクエリの最適化
   - 命名規則の統一

2. **中優先度**（2-4週間）
   - サービスレイヤーの基底クラス導入
   - API Viewsの分割
   - テストの追加

3. **低優先度**（1ヶ月以降）
   - フロントエンドのモジュール化
   - テンプレートの共通化
   - 設定管理の一元化

## まとめ

これらのリファクタリングを段階的に実装することで、コードの品質と保守性が大幅に向上します。各項目は独立して実装可能なため、優先度に応じて順次対応することができます。
