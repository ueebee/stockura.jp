# テストカバレッジ向上 設計書

## 1. 設計概要
本設計書は、現在 41.60% のテストカバレッジを 80% 以上に向上させるための技術設計を定義します。
要件定義書に基づき、優先度の高いモジュールから段階的にテストを追加していきます。

## 2. アーキテクチャ設計

### 2.1 テスト構造
```
tests/
├── unit/                      # 単体テスト
│   ├── application/
│   │   ├── use_cases/        # ユースケーステスト（Phase 1 で拡充）
│   │   └── dtos/             # DTO テスト（Phase 2 で新規作成）
│   ├── domain/
│   │   ├── services/         # ドメインサービステスト（Phase 2 で新規作成）
│   │   └── value_objects/    # VO テスト（Phase 3 で新規作成）
│   └── infrastructure/
│       └── jquants/          # JQuants リポジトリテスト（Phase 1 で拡充）
├── integration/              # 統合テスト
│   └── repositories/         # リポジトリ統合テスト（Phase 2 で作成）
└── e2e/                      # E2E テスト（Phase 3 で作成）
```

### 2.2 テストユーティリティ設計
```python
tests/
├── conftest.py              # 共通フィクスチャ
├── factories/               # テストデータファクトリ
│   ├── stock_factory.py     # Stock 関連のファクトリ（拡充）
│   └── price_factory.py     # 価格データファクトリ（新規）
└── mocks/                   # モッククラス
    ├── jquants_mock.py      # JQuants API モック（新規）
    └── yfinance_mock.py     # YFinance API モック（新規）
```

## 3. Phase 1 詳細設計

### 3.1 analyze_stock.py のテスト設計
```python
# tests/unit/application/use_cases/test_analyze_stock.py

class TestAnalyzeStockUseCase:
    # 正常系テスト
    - test_analyze_with_valid_stock_code
    - test_analyze_with_custom_period
    - test_generate_buy_recommendation
    - test_generate_sell_recommendation
    - test_generate_hold_recommendation
    
    # 異常系テスト
    - test_analyze_with_invalid_stock_code
    - test_analyze_with_no_price_data
    - test_analyze_with_partial_data
    - test_analyze_with_api_error
    
    # エッジケース
    - test_analyze_with_extreme_volatility
    - test_analyze_with_zero_volume
```

### 3.2 fetch_stock_price.py のテスト設計
```python
# tests/unit/application/use_cases/test_fetch_stock_price.py

class TestFetchStockPriceUseCase:
    # 正常系テスト
    - test_fetch_latest_price
    - test_fetch_price_for_specific_date
    - test_fetch_price_with_cache_hit
    - test_fetch_price_with_cache_miss
    
    # 異常系テスト
    - test_fetch_price_invalid_stock_code
    - test_fetch_price_future_date
    - test_fetch_price_weekend_date
    - test_fetch_price_api_error
    
    # データソース切り替えテスト
    - test_fetch_from_jquants
    - test_fetch_from_yfinance_fallback
```

### 3.3 JQuants Stock Repository のテスト設計
```python
# tests/unit/infrastructure/jquants/test_stock_repository_impl.py

class TestJQuantsStockRepository:
    # 基本機能テスト
    - test_get_listed_stocks_success
    - test_get_stock_by_code_found
    - test_get_stock_by_code_not_found
    - test_search_stocks_by_name
    
    # キャッシュ機能テスト
    - test_save_stock_list_to_cache
    - test_load_cached_stock_list
    - test_cache_expiration
    
    # エラーハンドリング
    - test_api_rate_limit_error
    - test_network_timeout_error
    - test_invalid_response_format
```

## 4. モック戦略

### 4.1 外部 API モック設計
```python
# tests/mocks/jquants_mock.py
class MockJQuantsClient:
    def __init__(self, scenario="success"):
        self.scenario = scenario
        self.call_count = 0
    
    async def get_listed_info(self, **kwargs):
        self.call_count += 1
        if self.scenario == "success":
            return self._success_response()
        elif self.scenario == "error":
            raise JQuantsAPIError("API Error")
        # ... 他のシナリオ
```

### 4.2 フィクスチャ設計
```python
# tests/conftest.py に追加
@pytest.fixture
def mock_jquants_client(monkeypatch):
    """JQuants クライアントのモック"""
    def _mock_client(scenario="success"):
        client = MockJQuantsClient(scenario)
        monkeypatch.setattr(
            "app.infrastructure.jquants.base_client.JQuantsBaseClient",
            lambda *args, **kwargs: client
        )
        return client
    return _mock_client

@pytest.fixture
def sample_stock_list():
    """テスト用の株式リスト"""
    return StockListFactory.create_with_stocks(count=10)
```

## 5. Phase 2 設計概要

### 5.1 DTO テスト
- StockDTO の変換ロジックテスト
- バリデーションテスト
- シリアライゼーション/デシリアライゼーション

### 5.2 価格計算サービステスト
- 移動平均計算のテスト
- ボラティリティ計算のテスト
- テクニカル指標計算のテスト

### 5.3 外部 API インターフェーステスト
- インターフェースの契約テスト
- レスポンス変換テスト

## 6. CI/CD 統合設計

### 6.1 GitHub Actions ワークフロー
```yaml
# .github/workflows/test-coverage.yml
name: Test Coverage Check

on:
  pull_request:
    branches: [main, develop]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
      - name: Comment PR with coverage
        uses: py-cov-action/python-coverage-comment-action@v3
```

### 6.2 カバレッジレポート設定
- PR ごとのカバレッジ差分表示
- カバレッジ低下時の警告
- バッジの自動更新

## 7. テストデータ管理

### 7.1 ファクトリパターン
```python
# tests/factories/stock_factory.py
class StockFactory(Factory):
    class Meta:
        model = Stock
    
    code = factory.Sequence(lambda n: f"{1000 + n}")
    name = factory.Faker("company", locale="ja_JP")
    market_code = factory.fuzzy.FuzzyChoice(["0101", "0102"])
    
    @factory.post_generation
    def add_price_history(obj, create, extracted, **kwargs):
        if extracted:
            # 価格履歴を追加
            pass
```

### 7.2 テストシナリオデータ
- 正常系データセット
- エッジケースデータセット
- エラーケースデータセット

## 8. パフォーマンス考慮事項

### 8.1 テスト並列実行
- pytest-xdist を使用した並列実行
- テスト間の依存関係を排除
- データベーステストの分離

### 8.2 テスト実行時間の最適化
- 重いテストのマーキング（@pytest.mark.slow）
- CI での段階的実行
- ローカル開発時の高速フィードバック

## 9. 成功指標

### 9.1 定量的指標
- 全体カバレッジ: 80% 以上
- Phase 1 完了時: 55% 以上
- Phase 2 完了時: 70% 以上
- Phase 3 完了時: 80% 以上

### 9.2 定性的指標
- すべてのクリティカルパスがテストされている
- テストが理解しやすく保守しやすい
- 新機能追加時にテストが書きやすい