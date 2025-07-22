# APIエンドポイント管理のリグレッションテスト 設計ファイル

## 1. システムアーキテクチャ

### 1.1 全体構成
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  regression_    │────▶│   Regression     │────▶│   Individual    │
│   test.py       │     │   Test Suite     │     │    Tests        │
│  (Entry Point)  │     │   (Orchestrator) │     │  (Test Cases)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Config        │     │   Browser        │     │   Database      │
│   Manager       │     │   Controller     │     │   Manager       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         └───────────────────────┴─────────────────────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │    Reporter      │
                         │  (Test Results)  │
                         └──────────────────┘
```

### 1.2 モジュール設計

#### 1.2.1 エントリポイント (regression_test.py)
- 責務：CLIインターフェースの提供
- 機能：
  - コマンドライン引数の解析
  - 設定の初期化
  - テストスイートの実行
  - 結果の表示

#### 1.2.2 設定管理 (config.py)
```python
class TestConfig:
    base_url: str
    docker_compose_file: str
    test_timeout: int
    schedule_wait_minutes: int
    headless: bool
    parallel_execution: bool
    test_data_source: str  # "production" or "test"
```

#### 1.2.3 ブラウザ制御 (browser.py)
```python
class BrowserController:
    async def setup(config: TestConfig) -> Browser
    async def create_page() -> Page
    async def safe_click(selector: str) -> bool
    async def safe_fill(selector: str, value: str) -> bool
    async def wait_for_element(selector: str) -> bool
    async def take_screenshot(name: str) -> str
```

#### 1.2.4 データベース管理 (database.py)
```python
class DatabaseManager:
    def __init__(self, docker_compose_file: str)
    def reset_database() -> bool:
        """
        1. docker compose down
        2. docker volume rm stockurajp_postgres_data
        3. docker compose up -d
        4. 起動待機
        5. alembic upgrade head
        """
    def wait_for_services() -> bool  # サービスの起動を待機
    def run_command(command: str, retry_count: int) -> bool  # リトライ機能付きコマンド実行
```

#### 1.2.5 テスト基底クラス (tests/base.py)
```python
class BaseRegressionTest:
    def __init__(browser: BrowserController, config: TestConfig)
    async def setup() -> None
    async def teardown() -> None
    async def execute() -> TestResult
    def log(message: str, level: str) -> None
```

#### 1.2.6 個別テストケース
- **UIテスト (tests/ui_test.py)**
  ```python
  class APIEndpointUITest(BaseRegressionTest):
      async def test_endpoint_list_display()
      async def test_endpoint_detail_view()
      async def test_manual_sync_functionality()
      async def test_schedule_crud_operations()
      async def test_execution_history_display()
  ```

- **企業同期テスト (tests/company_sync_test.py)**
  ```python
  class CompanySyncTest(BaseRegressionTest):
      async def test_manual_sync()
      async def test_scheduled_sync()
      async def verify_sync_results()
  ```

- **日次株価テスト (tests/daily_quotes_test.py)**
  ```python
  class DailyQuotesTest(BaseRegressionTest):
      async def test_manual_sync()
      async def test_scheduled_sync()
      async def test_date_range_selection()
  ```

- **スケジュール管理テスト (tests/schedule_crud_test.py)**
  ```python
  class ScheduleCRUDTest(BaseRegressionTest):
      async def test_create_schedule()
      async def test_update_schedule()
      async def test_delete_schedule()
      async def test_schedule_execution()
  ```

#### 1.2.7 レポート生成 (reporter.py)
```python
class TestReporter:
    def add_result(test_name: str, result: TestResult)
    def generate_summary() -> Dict
    def save_report(format: str) -> str
    def print_console_summary() -> None
```

## 2. データフロー設計

### 2.1 テスト実行フロー
```
1. CLI引数解析
   ↓
2. 設定ロード（環境変数、設定ファイル、CLI引数の優先順位）
   ↓
3. データベース初期化（オプション）
   - Docker環境の停止
   - PostgreSQLボリュームの削除
   - Docker環境の再起動
   - Alembicマイグレーションの実行
   ↓
4. ブラウザ初期化（Playwright）
   ↓
5. テストスイート実行
   - 並列実行モード：複数のブラウザインスタンス
   - 順次実行モード：単一のブラウザインスタンス
   ↓
6. 結果収集・レポート生成
   ↓
7. クリーンアップ
```

### 2.2 エラーハンドリング戦略
- **リトライメカニズム**
  - ネットワークエラー：3回まで自動リトライ
  - 要素待機タイムアウト：設定可能な待機時間
  - データベース接続エラー：指数バックオフ

- **エラー分類**
  - Critical：テスト続行不可（例：ブラウザ起動失敗）
  - Error：該当テスト失敗（例：要素が見つからない）
  - Warning：テスト継続可能（例：スクリーンショット保存失敗）

## 3. テストデータ管理

### 3.1 現在の実装方針
- Dockerコンテナの完全リセットによるクリーンな環境
- マイグレーション実行後の初期状態からテスト開始
- テストデータは各テスト内で必要に応じて作成

### 3.2 将来の拡張計画
- 本番データダンプのリストア機能
- テストフィクスチャの管理
- データのスナップショット/リストア機能

## 4. 並列実行設計

### 4.1 テストの独立性
- 各テストは独立したブラウザコンテキストで実行
- データベーストランザクションの分離
- テスト間の依存関係なし

### 4.2 リソース管理
- 最大並列数の制限（デフォルト：4）
- メモリ使用量の監視
- タイムアウト管理

## 5. ログとモニタリング

### 5.1 ログレベル
- DEBUG：詳細な実行情報
- INFO：主要なステップ
- WARNING：非致命的な問題
- ERROR：テスト失敗
- CRITICAL：システムエラー

### 5.2 ログ出力
- コンソール：リアルタイム表示
- ファイル：詳細ログの永続化
- 構造化ログ：JSON形式での出力オプション

## 6. 拡張性設計

### 6.1 プラグインアーキテクチャ
- カスタムテストの追加が容易
- 新しいレポート形式の追加
- 外部システムとの統合

### 6.2 設定の外部化
- YAML/JSON設定ファイルのサポート
- 環境別設定の管理
- シークレット管理との統合

## 7. パフォーマンス最適化

### 7.1 キャッシング
- ブラウザインスタンスの再利用
- 静的リソースのキャッシュ
- テスト結果のキャッシュ

### 7.2 並列化戦略
- テストケースレベルの並列化
- ブラウザコンテキストの効率的な管理
- データベース接続プーリング

## 8. セキュリティ考慮事項

### 8.1 認証情報管理
- 環境変数での管理
- シークレットマネージャーとの統合
- ログからの機密情報除外

### 8.2 本番データ保護
- 読み取り専用アクセス
- データマスキング
- アクセスログの記録