# Stockura.jp テスト設計ドキュメント

## 1. 概要

本ドキュメントは、Stockura.jpプロジェクトの包括的なテスト戦略と実装ガイドラインを定義します。現在のテストカバレッジを向上させ、システムの品質と信頼性を確保することを目的としています。

### 1.1 現状分析

#### 既存のテスト状況
- **テストフレームワーク**: pytest v7.2.2（pytest-asyncio, pytest-cov）
- **テストファイル数**: 12ファイル
- **主なテスト対象**: API、サービス層、J-Quantsクライアント
- **課題**: 
  - プロジェクトレベルのconftest.pyが存在しない
  - カバレッジ設定ファイルがない
  - テストヘルパーやフィクスチャの共通化が不十分
  - E2Eテストが未実装

### 1.2 目標

1. **カバレッジ目標**: 全体で80%以上（コア機能は90%以上）
2. **テストピラミッド**: 単体テスト（70%）、統合テスト（20%）、E2Eテスト（10%）
3. **CI/CD統合**: 全てのプルリクエストでテスト自動実行
4. **パフォーマンステスト**: 大量データ処理のベンチマーク

## 2. テスト種別と責務

### 2.1 単体テスト（Unit Tests）

#### 対象
- モデル（app/models/）
- スキーマ（app/schemas/）
- ユーティリティ（app/utils/）
- 個別のサービスメソッド

#### 方針
- 外部依存はモック化
- 1テスト1アサーション原則
- エッジケースを網羅
- テストケース名は日本語で記述可

### 2.2 統合テスト（Integration Tests）

#### 対象
- APIエンドポイント
- サービス層の複合処理
- データベーストランザクション
- 外部API連携（モック使用）

#### 方針
- TestClientを使用したAPI全体の動作確認
- データベースはテスト用DBを使用
- トランザクションロールバックで環境をクリーン保持

### 2.3 E2Eテスト（End-to-End Tests）

#### 対象
- ユーザーシナリオ全体
- 外部API実連携（開発環境）
- バックグラウンドタスクの動作

#### 方針
- Docker環境での実行
- 本番環境に近い設定
- 実行時間を考慮し、重要シナリオに限定

### 2.4 パフォーマンステスト

#### 対象
- 大量データの同期処理
- API応答時間
- データベースクエリ性能

#### 方針
- ベンチマーク基準の設定
- 継続的な性能監視
- ボトルネックの特定と改善

## 3. テスト実装ガイドライン

### 3.1 ディレクトリ構造

```
tests/
├── conftest.py                 # プロジェクト共通設定
├── fixtures/                   # 共通フィクスチャ
│   ├── __init__.py
│   ├── database.py            # DB関連フィクスチャ
│   ├── models.py              # モデルフィクスチャ
│   └── external_api.py        # 外部APIモック
├── unit/                      # 単体テスト
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── integration/               # 統合テスト
│   ├── api/
│   └── services/
├── e2e/                       # E2Eテスト
└── performance/               # パフォーマンステスト
```

### 3.2 共通フィクスチャ

#### データベース関連
```python
@pytest.fixture
async def db_session():
    """テスト用DBセッション"""
    
@pytest.fixture
async def clean_db(db_session):
    """クリーンなDB状態を保証"""
```

#### モデルファクトリー
```python
@pytest.fixture
def company_factory():
    """企業データのファクトリー"""
    
@pytest.fixture
def daily_quote_factory():
    """株価データのファクトリー"""
```

#### 外部APIモック
```python
@pytest.fixture
def mock_jquants_client():
    """J-Quants APIクライアントのモック"""
```

### 3.3 テストデータ管理

#### ファクトリーボーイの導入
```python
# tests/factories/company.py
class CompanyFactory(factory.Factory):
    class Meta:
        model = Company
    
    code = factory.Sequence(lambda n: f"{10000 + n}")
    company_name = factory.Faker('company', locale='ja_JP')
    market_code = factory.fuzzy.FuzzyChoice(['0111', '0112'])
```

#### テストデータセット
- 基本データセット: 最小限の正常系データ
- エッジケースセット: 境界値、異常値
- パフォーマンステスト用大量データ

### 3.4 アサーション戦略

#### 推奨アサーション
```python
# 明示的で読みやすいアサーション
assert actual_company.code == expected_code
assert len(companies) == 10
assert "エラー" in response.json()["detail"]

# 複雑な検証はヘルパー関数化
assert_valid_company_response(response)
assert_pagination_works(response, total=100, page_size=20)
```

### 3.5 非同期テストのベストプラクティス

```python
# 非同期テストマーカー
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None

# タイムアウト設定
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_long_running_sync():
    await sync_all_companies()
```

## 4. テスト実装の優先順位

### フェーズ1: 基盤整備（優先度: 最高）
1. プロジェクトレベルconftest.py作成
2. 共通フィクスチャの実装
3. カバレッジ設定とCI統合
4. テストユーティリティの作成

### フェーズ2: コアモデルのテスト強化（優先度: 高）
1. Companyモデルの完全なテスト
2. DailyQuoteモデルの完全なテスト
3. DataSourceモデルとセキュリティのテスト
4. モデル間のリレーションシップテスト

### フェーズ3: サービス層の網羅（優先度: 高）
1. CompanySyncServiceの詳細テスト
2. DailyQuotesSyncServiceの詳細テスト
3. EncryptionServiceのセキュリティテスト
4. エラーハンドリングとリトライロジック

### フェーズ4: API層の完全カバレッジ（優先度: 中）
1. 全エンドポイントの正常系テスト
2. エラーレスポンスの網羅
3. 認証・認可のテスト（将来実装時）
4. レート制限のテスト

### フェーズ5: E2Eとパフォーマンス（優先度: 中）
1. 主要ユーザーシナリオのE2E
2. 大量データ同期のパフォーマンステスト
3. 同時実行とロック機構のテスト
4. メモリ使用量とリソース管理

## 5. テスト実行とCI/CD

### 5.1 ローカル実行

```bash
# 全テスト実行
pytest

# カバレッジ付き実行
pytest --cov=app --cov-report=html --cov-report=term

# 特定のマーカーのみ実行
pytest -m "not slow"

# 並列実行
pytest -n auto

# 詳細出力
pytest -vv
```

### 5.2 Make/タスクランナー設定

```makefile
# Makefile
.PHONY: test test-unit test-integration test-e2e coverage

test:
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-e2e:
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

coverage:
	pytest --cov=app --cov-report=html --cov-fail-under=80
```

### 5.3 CI設定（GitHub Actions例）

```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Run tests
        run: |
          pip install -r requirements-test.txt
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 6. カバレッジ設定

### 6.1 .coveragerc

```ini
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov
```

### 6.2 pytest.ini

```ini
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    performance: marks tests as performance tests
addopts = 
    --strict-markers
    --tb=short
    --disable-warnings
```

## 7. テストデータとモック戦略

### 7.1 J-Quants APIモック

```python
# tests/mocks/jquants_responses.py
MOCK_LISTED_INFO = {
    "info": [
        {
            "Date": "2024-01-01",
            "Code": "72030",
            "CompanyName": "トヨタ自動車",
            "MarketCode": "0111",
            "Sector17Code": "16",
            "Sector33Code": "3050"
        }
    ]
}

MOCK_DAILY_QUOTES = {
    "daily_quotes": [
        {
            "Date": "2024-01-01",
            "Code": "72030",
            "Open": 2500.0,
            "High": 2550.0,
            "Low": 2480.0,
            "Close": 2520.0,
            "Volume": 1000000
        }
    ]
}
```

### 7.2 データベーステストデータ

```python
# tests/fixtures/test_data.py
@pytest.fixture
def sample_companies(db_session):
    """サンプル企業データセット"""
    companies = [
        Company(code="72030", company_name="トヨタ自動車"),
        Company(code="67580", company_name="ソニーグループ"),
        # ... 他の企業
    ]
    db_session.add_all(companies)
    await db_session.commit()
    return companies
```

## 8. モニタリングとメトリクス

### 8.1 追跡すべきメトリクス

- テスト実行時間
- カバレッジ率の推移
- 失敗率とフレーキーテストの検出
- パフォーマンステストの結果推移

### 8.2 レポーティング

- カバレッジレポートの自動生成
- テスト結果のSlack/Discord通知
- 週次でのテストヘルスレポート

## 9. トラブルシューティングガイド

### 9.1 よくある問題と対処法

#### 非同期テストのタイムアウト
```python
# タイムアウトを延長
@pytest.mark.timeout(60)
async def test_long_operation():
    pass
```

#### データベース接続エラー
```python
# テスト用DB URLの確認
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost/test_stockura"
```

#### モックが効かない
```python
# パッチの場所を正確に指定
@patch('app.services.company_sync.JQuantsClient')
def test_with_mock(mock_client):
    pass
```

### 9.2 デバッグ手法

```python
# pytest-pudbの使用
import pudb; pudb.set_trace()

# ログ出力の確認
pytest -s  # stdout/stderrを表示

# 特定のテストのみ実行
pytest tests/test_models.py::test_company_creation -vv
```

## 10. 継続的改善

### 10.1 定期レビュー

- 月次でのカバレッジレビュー
- 四半期でのテスト戦略見直し
- フレーキーテストの改善スプリント

### 10.2 チーム教育

- テスト駆動開発（TDD）の推奨
- ペアプログラミングでのテスト作成
- テストコードレビューの徹底

## 付録A: チェックリスト

### 新機能実装時のテストチェックリスト

- [ ] モデルの単体テスト
- [ ] スキーマのバリデーションテスト
- [ ] サービス層の単体・統合テスト
- [ ] APIエンドポイントのテスト
- [ ] エラーケースのテスト
- [ ] パフォーマンスへの影響評価
- [ ] ドキュメントの更新

### プルリクエスト時のチェックリスト

- [ ] 全テストがパス
- [ ] カバレッジが低下していない
- [ ] 新規コードのカバレッジが80%以上
- [ ] テストが読みやすく保守可能
- [ ] 不要なconsole.logやprint文の削除

## 付録B: 参考リソース

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPIテストガイド](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemyテストパターン](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html)