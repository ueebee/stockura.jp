# 既存テストの新テスト環境への移行 設計書

## 1. 設計概要

既存のテストを新しいテスト環境に移行するための詳細設計。要件に基づき、段階的な移行を実施する。

## 2. アーキテクチャ設計

### 2.1 テスト構造
```
tests/
├── conftest.py          # グローバルフィクスチャ（既存）
├── fixtures/            # 共有フィクスチャ（既存）
│   ├── database.py      # DB 関連フィクスチャ
│   ├── clients.py       # HTTP クライアントフィクスチャ
│   └── factories/       # ファクトリークラス
│       ├── auth.py      # 認証関連ファクトリー
│       └── stock.py     # 株式関連ファクトリー
├── unit/                # 単体テスト
├── integration/         # 統合テスト
└── utils/              # 共通ユーティリティ（新規追加）
    ├── __init__.py
    ├── mocks.py        # 共通モック定義
    └── assertions.py   # カスタムアサーション
```

### 2.2 依存関係の管理
- 各テストは conftest.py のグローバルフィクスチャを利用
- テストデータ生成は factories/ のファクトリーを使用
- 外部 API のモックは utils/mocks.py に集約

## 3. Phase 1: 既存テストの動作確認

### 3.1 実施内容
- 現在のテストをそのまま新環境で実行
- 依存関係の問題を特定
- 実行時間のベースライン測定

### 3.2 確認項目
```python
# 各テストファイルで以下を確認
- pytest での実行可否
- 必要な環境変数の有無
- 外部依存の特定
```

## 4. Phase 2: 共通フィクスチャへの置き換え

### 4.1 データベースフィクスチャの活用

**現在のパターン（例: test_auth_repository.py）**
```python
@pytest.fixture
def auth_repository():
    return JQuantsAuthRepository()
```

**移行後**
```python
# conftest.py or fixtures/repositories.py に移動
@pytest.fixture
async def auth_repository(db_session):
    """共通の認証リポジトリフィクスチャ"""
    return JQuantsAuthRepository()
```

### 4.2 モッククライアントの統合

**現在のパターン**
```python
# 各テストファイルで個別にモック定義
with patch("aiohttp.ClientSession") as mock_session:
    # モックの設定
```

**移行後**
```python
# fixtures/clients.py に追加
@pytest.fixture
def mock_aiohttp_session():
    """共通の aiohttp Session モック"""
    with patch("aiohttp.ClientSession") as mock:
        yield mock

# utils/mocks.py
def create_mock_response(status=200, json_data=None):
    """モックレスポンスの生成ヘルパー"""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=json_data)
    return mock_response
```

## 5. Phase 3: Factory 活用への移行

### 5.1 テストデータ生成の改善

**現在のパターン（例: test_stock_use_case.py）**
```python
@pytest.fixture
def sample_stock():
    return Stock(
        code=StockCode("7203"),
        company_name="トヨタ自動車",
        # ... 長いハードコード
    )
```

**移行後**
```python
# テスト内で直接ファクトリーを使用
def test_stock_creation(stock_factory):
    stock = stock_factory.create(
        code="7203",
        company_name="トヨタ自動車"
    )
    # デフォルト値は自動設定
```

### 5.2 ファクトリーの拡張

```python
# fixtures/factories/stock.py に追加
class StockListFactory(BaseFactory):
    """StockList エンティティのファクトリー"""
    class Meta:
        model = StockList
    
    stocks = factory.List([
        factory.SubFactory(StockFactory) for _ in range(2)
    ])
    updated_date = factory.Faker('date_object')
```

## 6. Phase 4: リファクタリング

### 6.1 重複コードの削除

**共通パターンの抽出**
```python
# utils/assertions.py
def assert_authentication_error(exc_info, expected_message):
    """認証エラーの共通アサーション"""
    assert isinstance(exc_info.value, AuthenticationError)
    assert expected_message in str(exc_info.value)

def assert_validation_error(exc_info, expected_message):
    """バリデーションエラーの共通アサーション"""
    assert isinstance(exc_info.value, ValidationError)
    assert expected_message in str(exc_info.value)
```

### 6.2 非同期テストの最適化

```python
# conftest.py に追加
@pytest.fixture
def event_loop():
    """非同期テスト用のイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

## 7. 移行マッピング

### 7.1 単体テスト

| 現在のファイル | 主な変更点 |
|-------------|----------|
| test_auth_use_case.py | - モックリポジトリを共通フィクスチャ化<br>- エラーアサーションを共通化 |
| test_stock_use_case.py | - StockFactory の活用<br>- StockListFactory の追加 |
| test_stock.py, test_stock_v2.py | - 統合して一つのファイルに<br>- パラメータ化テストの活用 |
| test_auth_repository.py | - モックレスポンス生成の共通化<br>- 認証情報ファクトリーの活用 |
| test_base_client.py | - HTTP クライアントモックの共通化 |
| test_redis_auth_repository.py | - Redis モックフィクスチャの活用 |

### 7.2 統合テスト

| 現在のファイル | 主な変更点 |
|-------------|----------|
| test_auth_endpoints.py | - auth_client フィクスチャの活用<br>- レスポンス検証の共通化 |

## 8. テスト実行設定

### 8.1 pytest.ini の設定
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
markers = [
    "unit: 単体テスト",
    "integration: 統合テスト",
    "slow: 実行時間の長いテスト",
]
```

### 8.2 カバレッジ設定
```ini
[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "**/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

## 9. 移行時の注意事項

### 9.1 後方互換性
- 既存のテストロジックは変更しない
- テストの意図を保持する
- 段階的に移行し、各段階で動作確認

### 9.2 命名規則
- フィクスチャ名は用途を明確に表す
- モック関数は `mock_` プレフィックスを使用
- ファクトリークラスは `Factory` サフィックスを使用

### 9.3 ドキュメント
- 各フィクスチャに docstring を追加
- 複雑なモックには使用例を記載
- 移行ガイドを作成

## 10. 期待される成果

### 10.1 定量的指標
- テスト実行時間: 20-30% の短縮
- コード行数: 30-40% の削減（重複削除により）
- カバレッジ: 現状維持以上

### 10.2 定性的指標
- 新規テスト作成の容易さ向上
- テストコードの可読性向上
- メンテナンス性の向上