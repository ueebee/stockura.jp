# テスト環境整備 要件仕様書

## 1. 概要
FastAPI アプリケーションのテスト環境を、 Rails のような使いやすく統一的な環境に整備する。

## 2. 目的
- テストの作成・実行を簡単にする
- テストデータの準備・クリーンアップを自動化する
- テストの可読性と保守性を向上させる
- CI/CD 環境でも動作する堅牢なテスト環境を構築する

## 3. 機能要件

### 3.1 テストフィクスチャ管理
- [ ] データベースのテストデータ作成・管理機能
- [ ] FactoryBoy または同等のファクトリーパターン実装
- [ ] テスト前後のデータベースクリーンアップ機能
- [ ] トランザクショナルテストのサポート

### 3.2 共通テストユーティリティ
- [ ] 認証付きテストクライアントの提供
- [ ] モックサーバー（J-Quants API 等）の準備
- [ ] 共通アサーションヘルパーの実装
- [ ] レスポンス検証ユーティリティ

### 3.3 テスト設定管理
- [ ] 環境別設定ファイル（test 環境専用）
- [ ] テストデータベースの自動セットアップ
- [ ] Redis テスト環境の分離
- [ ] 環境変数の管理

### 3.4 テスト実行環境
- [ ] pytest 設定の最適化
- [ ] カバレッジ計測の設定
- [ ] 並列実行のサポート
- [ ] テストグルーピング（unit/integration/e2e）

### 3.5 開発者体験
- [ ] VSCode/PyCharm でのデバッグサポート
- [ ] ウォッチモードでのテスト実行
- [ ] テスト結果の見やすい表示
- [ ] 失敗時の詳細なエラー情報

## 4. 非機能要件

### 4.1 パフォーマンス
- テスト実行時間を最小限に抑える
- データベース操作の最適化
- 不要な外部 API 呼び出しの排除

### 4.2 保守性
- テストコードの重複を最小限に抑える
- 新しいテストケースの追加が容易
- 既存テストへの影響を最小限に

### 4.3 可搬性
- ローカル環境での動作保証
- Docker 環境での動作保証
- CI/CD 環境（GitHub Actions 等）での動作保証

## 5. 技術要件

### 5.1 使用ツール・ライブラリ
- pytest（メインテストフレームワーク）
- pytest-asyncio（非同期テストサポート）
- pytest-cov（カバレッジ計測）
- factory-boy（テストデータ生成）
- pytest-mock（モック機能）
- httpx（API テストクライアント）

### 5.2 ディレクトリ構成
```
tests/
├── conftest.py          # グローバルフィクスチャ
├── fixtures/            # 共有フィクスチャ
│   ├── __init__.py
│   ├── database.py      # DB 関連
│   ├── factories.py     # データファクトリー
│   └── clients.py       # テストクライアント
├── utils/               # テストユーティリティ
│   ├── __init__.py
│   ├── assertions.py    # カスタムアサーション
│   └── helpers.py       # ヘルパー関数
├── unit/                # 単体テスト
├── integration/         # 統合テスト
└── e2e/                 # E2E テスト
```

## 6. 制約事項
- 既存のクリーンアーキテクチャ構造を維持する
- 本番環境のコードに影響を与えない
- Python 3.9 以上をサポート

## 7. 想定される使用例

### 7.1 単体テスト作成例
```python
def test_create_stock(stock_factory, db_session):
    # ファクトリーを使ったテストデータ作成
    stock = stock_factory.create(symbol="7203")
    
    # テスト実行
    result = stock_use_case.create(stock_data)
    
    # アサーション
    assert result.symbol == "7203"
```

### 7.2 API テスト例
```python
async def test_get_stock_price(auth_client, mock_jquants):
    # モックの設定
    mock_jquants.get_stock_price.return_value = {"price": 1000}
    
    # API リクエスト
    response = await auth_client.get("/api/stocks/7203/price")
    
    # レスポンス検証
    assert response.status_code == 200
    assert response.json()["price"] == 1000
```