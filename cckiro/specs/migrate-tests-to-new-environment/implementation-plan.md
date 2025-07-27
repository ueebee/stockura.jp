# 既存テストの新テスト環境への移行 実装計画書

## 1. 実装概要

設計書に基づき、 4 つのフェーズで段階的に既存テストを新環境に移行する。各フェーズでの具体的な実装手順とタスクを定義する。

## 2. 実装スケジュール

### 全体タイムライン
- **Phase 1**: 1 日（既存テストの動作確認）
- **Phase 2**: 2 日（共通フィクスチャへの置き換え）
- **Phase 3**: 2 日（Factory 活用への移行）
- **Phase 4**: 1 日（リファクタリング）
- **合計**: 約 6 日

## 3. Phase 1: 既存テストの動作確認（1 日）

### 3.1 実装タスク
1. **テスト実行環境の確認**
   ```bash
   # 全テストの実行
   pytest tests/
   
   # カバレッジ付き実行
   pytest --cov=app tests/
   ```

2. **実行時間のベースライン測定**
   ```bash
   # 実行時間の測定
   pytest --durations=10 tests/
   ```

3. **問題点の洗い出し**
   - [ ] 失敗するテストの特定
   - [ ] 環境依存の問題の特定
   - [ ] 実行時間が長いテストの特定

### 3.2 成果物
- テスト実行レポート（現状）
- 問題点リスト
- 実行時間ベースライン

## 4. Phase 2: 共通フィクスチャへの置き換え（2 日）

### 4.1 Day 1: 共通フィクスチャの作成

#### タスク 1: utils ディレクトリの作成
```bash
mkdir -p tests/utils
touch tests/utils/__init__.py
touch tests/utils/mocks.py
touch tests/utils/assertions.py
```

#### タスク 2: 共通モックの実装（tests/utils/mocks.py）
```python
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, Dict, Any

def create_mock_response(
    status: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    text: str = ""
) -> MagicMock:
    """HTTP レスポンスのモックを生成"""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.text = text
    mock_response.json = AsyncMock(return_value=json_data or {})
    return mock_response

def create_mock_redis_client():
    """Redis クライアントのモックを生成"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    return mock
```

#### タスク 3: カスタムアサーションの実装（tests/utils/assertions.py）
```python
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    ValidationError,
    DataNotFoundError
)

def assert_authentication_error(exc_info, expected_message: str):
    """認証エラーのアサーション"""
    assert isinstance(exc_info.value, AuthenticationError)
    assert expected_message in str(exc_info.value)

def assert_validation_error(exc_info, expected_message: str):
    """バリデーションエラーのアサーション"""
    assert isinstance(exc_info.value, ValidationError)
    assert expected_message in str(exc_info.value)

def assert_data_not_found_error(exc_info, expected_message: str):
    """データ未検出エラーのアサーション"""
    assert isinstance(exc_info.value, DataNotFoundError)
    assert expected_message in str(exc_info.value)
```

#### タスク 4: 共通フィクスチャの追加（fixtures/clients.py）
```python
# 既存のフィクスチャに追加
@pytest.fixture
def mock_aiohttp_session():
    """aiohttp Session のモック"""
    with patch("aiohttp.ClientSession") as mock:
        yield mock

@pytest.fixture
def mock_redis_client():
    """Redis クライアントのモック"""
    from tests.utils.mocks import create_mock_redis_client
    return create_mock_redis_client()
```

### 4.2 Day 2: 既存テストの移行

#### 移行対象ファイルと順序
1. **test_auth_repository.py**
   - モックレスポンス生成を共通化
   - aiohttp セッションモックの使用

2. **test_base_client.py**
   - HTTP クライアントモックの共通化

3. **test_redis_auth_repository.py**
   - Redis モックフィクスチャの使用

4. **test_auth_use_case.py, test_stock_use_case.py**
   - エラーアサーションの共通化

## 5. Phase 3: Factory 活用への移行（2 日）

### 5.1 Day 1: ファクトリーの拡張

#### タスク 1: StockListFactory の実装
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
    
    @classmethod
    def create_with_stocks(cls, stock_count: int = 3, **kwargs):
        """指定数の株式を含む StockList を生成"""
        stocks = [StockFactory.create() for _ in range(stock_count)]
        return cls.create(stocks=stocks, **kwargs)
```

#### タスク 2: 認証関連ファクトリーの拡張
```python
# fixtures/factories/auth.py に追加
class JQuantsCredentialsFactory(BaseFactory):
    """JQuantsCredentials のファクトリー"""
    class Meta:
        model = JQuantsCredentials
    
    email = factory.Faker('email')
    password = factory.Faker('password')
    refresh_token = factory.SubFactory(RefreshTokenFactory)
    id_token = factory.SubFactory(IdTokenFactory)
```

### 5.2 Day 2: テストの移行

#### 移行対象と変更内容
1. **test_stock_use_case.py**
   - sample_stock フィクスチャを削除
   - StockFactory.create() を使用
   - StockListFactory の活用

2. **test_stock.py, test_stock_v2.py**
   - 2 つのファイルを統合
   - パラメータ化テストの実装

3. **test_auth_repository.py**
   - 認証情報ファクトリーの活用
   - モックデータ生成の簡略化

## 6. Phase 4: リファクタリング（1 日）

### 6.1 実装タスク

#### タスク 1: 重複コードの削除
- 共通パターンの特定
- ヘルパー関数への抽出
- 不要なフィクスチャの削除

#### タスク 2: テストの統合
- test_stock.py と test_stock_v2.py の統合
- 類似テストのパラメータ化

#### タスク 3: ドキュメントの追加
- 各フィクスチャへの docstring 追加
- 複雑なモックの使用例追加
- README.md の更新

### 6.2 最適化
```python
# pyproject.toml に追加
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
asyncio_mode = "auto"
markers = [
    "unit: 単体テスト",
    "integration: 統合テスト",
    "slow: 実行時間の長いテスト",
]

# テストの並列実行
addopts = "-n auto"
```

## 7. 実装時の注意事項

### 7.1 Git 管理
- 各フェーズごとにコミット
- わかりやすいコミットメッセージ
- テスト失敗時は即座に修正

### 7.2 テスト実行
- 各変更後に該当テストを実行
- 全体テストは各フェーズ完了時に実行
- カバレッジの確認

### 7.3 コードレビュー
- 各フェーズ完了後にセルフレビュー
- 重要な変更は個別にレビュー

## 8. リスク管理

### 8.1 想定されるリスク
1. **既存テストの破壊**
   - 対策: 段階的な移行、各ステップでの動作確認

2. **実行時間の増加**
   - 対策: 並列実行の活用、不要な setup/teardown の削除

3. **互換性の問題**
   - 対策: 既存のテストロジックは変更しない

### 8.2 ロールバック計画
- 各フェーズ前に git でタグ付け
- 問題発生時は前のタグに戻す

## 9. 完了基準

### 9.1 各フェーズの完了基準
- **Phase 1**: 全テストの実行結果とベースラインの記録
- **Phase 2**: 共通フィクスチャの作成と一部テストでの動作確認
- **Phase 3**: ファクトリーを使用したテストの動作確認
- **Phase 4**: 全テストの成功とカバレッジの維持

### 9.2 全体の完了基準
- [ ] 全てのテストが成功
- [ ] カバレッジが現状以上
- [ ] 実行時間が 20% 以上短縮
- [ ] コード行数が 30% 以上削減
- [ ] ドキュメントの更新完了

## 10. 次のステップ

実装完了後：
1. パフォーマンステストの追加
2. E2E テストの拡充
3. CI/CD パイプラインの最適化
4. テストベストプラクティスのドキュメント化