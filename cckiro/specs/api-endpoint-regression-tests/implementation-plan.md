# APIエンドポイント管理のリグレッションテスト 実装計画ファイル

## 1. 実装フェーズと優先順位

### フェーズ1: 基盤構築（優先度：高）
1. **ディレクトリ構造の作成**
   - bin/regression_test/ディレクトリの作成
   - 各サブディレクトリの作成
   - __init__.pyファイルの配置

2. **設定管理モジュールの実装**
   - config.pyの作成
   - 環境変数の読み込み機能
   - デフォルト値の設定

3. **ユーティリティモジュールの実装**
   - utils.pyの作成
   - ログ出力機能
   - 時刻変換機能（JST対応）

### フェーズ2: コア機能の移植（優先度：高）
1. **データベース管理モジュール**
   - database.pyの作成
   - 既存のreset_database機能の移植
   - コマンド実行のリトライ機能

2. **ブラウザ制御モジュール**
   - browser.pyの作成
   - Playwright関連機能の移植
   - 安全な操作メソッド（safe_click, safe_fill等）

3. **テスト基底クラス**
   - tests/base.pyの作成
   - 共通のセットアップ/ティアダウン処理
   - ログ機能の統合

### フェーズ3: 既存テストの移植（優先度：中）
1. **企業同期テスト**
   - tests/company_sync_test.pyの作成
   - test_company_sync機能の移植とリファクタリング

2. **日次株価テスト**
   - tests/daily_quotes_test.pyの作成
   - test_daily_quotes_sync機能の移植

3. **スケジュール管理テスト**
   - tests/schedule_crud_test.pyの作成
   - test_schedule_crud機能の移植

### フェーズ4: 新規UIテストの実装（優先度：高）
1. **UIテストクラスの作成**
   - tests/ui_test.pyの作成
   - 本番データを使用したテストケースの実装

2. **テストケースの実装**
   - エンドポイント一覧表示テスト
   - 詳細画面遷移テスト
   - 同期機能テスト
   - スケジュール操作テスト
   - 実行履歴確認テスト

### フェーズ5: レポート機能とメインスクリプト（優先度：中）
1. **レポート生成モジュール**
   - reporter.pyの作成
   - JSON/HTML形式のレポート生成
   - コンソール出力の改善

2. **メインスクリプトの更新**
   - regression_test.pyのリファクタリング
   - 新しいモジュール構造の統合
   - 後方互換性の維持

## 2. 実装手順詳細

### 2.1 ディレクトリ構造作成
```bash
mkdir -p bin/regression_test/tests
touch bin/regression_test/__init__.py
touch bin/regression_test/tests/__init__.py
```

### 2.2 各モジュールの実装順序
1. config.py → utils.py → database.py → browser.py
2. tests/base.py
3. 各テストケース（並行して実装可能）
4. reporter.py
5. regression_test.pyの更新

### 2.3 テスト実行の確認
各フェーズ完了後に以下を確認：
- 単体テストの実行
- 既存機能との互換性
- パフォーマンスの比較

## 3. 技術的実装詳細

### 3.1 config.py
```python
@dataclass
class TestConfig:
    base_url: str = "http://localhost:8000"
    docker_compose_file: str = "docker-compose.yml"
    test_timeout: int = 60
    schedule_wait_minutes: int = 2
    headless: bool = True
    retry_count: int = 3
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        # 環境変数から設定を読み込む
```

### 3.2 database.py
```python
class DatabaseManager:
    def __init__(self, config: TestConfig):
        self.config = config
        self.compose_cmd = f"docker compose -f {config.docker_compose_file}"
    
    def reset_database(self) -> bool:
        # 既存のコードを移植・改善
```

### 3.3 browser.py
```python
class BrowserController:
    def __init__(self, config: TestConfig):
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup(self) -> bool:
        # Playwrightの初期化
```

### 3.4 tests/base.py
```python
class BaseRegressionTest(ABC):
    def __init__(self, browser: BrowserController, config: TestConfig):
        self.browser = browser
        self.config = config
        self.logger = self._setup_logger()
    
    @abstractmethod
    async def execute(self) -> TestResult:
        pass
```

## 4. 移行戦略

### 4.1 段階的移行
1. 新しいモジュール構造を作成
2. 既存のregression_test.pyから機能を段階的に移植
3. 両方のバージョンを並行して維持
4. 十分なテスト後に旧バージョンを廃止

### 4.2 互換性の維持
- CLIインターフェースは変更しない
- 環境変数名は維持
- 出力形式も既存と同じ

## 5. テスト計画

### 5.1 単体テスト
- 各モジュールに対するユニットテスト
- モックを使用した独立したテスト

### 5.2 統合テスト
- モジュール間の連携確認
- エンドツーエンドのテスト実行

### 5.3 回帰テスト
- 既存機能の動作確認
- パフォーマンス比較

## 6. リスクと対策

### 6.1 リスク
- 既存機能の破壊
- パフォーマンスの低下
- 新しいバグの導入

### 6.2 対策
- 段階的な移行
- 十分なテスト
- コードレビュー
- ロールバック計画

## 7. 完了基準

### 7.1 機能要件
- 全ての既存テストが新構造で動作
- 新規UIテストが実装され動作
- レポート機能が改善

### 7.2 非機能要件
- コードの可読性向上
- 保守性の改善
- テスト実行時間の維持または改善

## 8. スケジュール目安

- フェーズ1: 1日
- フェーズ2: 2日
- フェーズ3: 2日
- フェーズ4: 1日
- フェーズ5: 1日

合計: 約7日（並行作業により短縮可能）