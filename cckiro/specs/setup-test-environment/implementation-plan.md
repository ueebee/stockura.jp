# テスト環境整備 実装計画書

## 1. 実装概要
設計書に基づいて、段階的にテスト環境を構築していきます。 Phase 1 を優先的に実装し、動作確認後に Phase 2 、 Phase 3 へ進みます。

## 2. 実装フェーズ

### Phase 1: 基礎環境構築（必須）

#### 1.1 依存パッケージの追加
```bash
poetry add --group dev factory-boy pytest-env pytest-xdist httpx freezegun
```

実装ファイル:
- `pyproject.toml` - 依存関係の更新

#### 1.2 テスト環境設定ファイルの作成
実装ファイル:
- `.env.test` - テスト環境用の環境変数
- `tests/settings/__init__.py`
- `tests/settings/test_config.py` - テスト設定の集約

#### 1.3 グローバルフィクスチャの実装
実装ファイル:
- `tests/conftest.py` - pytest 設定とグローバルフィクスチャ

実装内容:
- pytest 設定のカスタマイズ
- イベントループフィクスチャ
- ログ設定
- テストマーカーの定義

#### 1.4 データベースフィクスチャの実装
実装ファイル:
- `tests/fixtures/__init__.py`
- `tests/fixtures/database.py` - DB 関連フィクスチャ

実装内容:
- テストデータベース接続
- トランザクション管理
- マイグレーション実行
- クリーンアップ処理

#### 1.5 基本テストクライアントの実装
実装ファイル:
- `tests/fixtures/clients.py` - HTTP テストクライアント

実装内容:
- FastAPI テストクライアントのラップ
- 基本的なリクエストヘルパー

#### 1.6 ベースファクトリーの実装
実装ファイル:
- `tests/fixtures/factories/__init__.py`
- `tests/fixtures/factories/base.py` - FactoryBoy ベース設定
- `tests/fixtures/factories/auth.py` - 認証関連ファクトリー
- `tests/fixtures/factories/stock.py` - 株式関連ファクトリー

実装内容:
- SQLAlchemy セッション統合
- 基本的なエンティティファクトリー

### Phase 2: 高度な機能追加（推奨）

#### 2.1 J-Quants API モックの実装
実装ファイル:
- `tests/fixtures/mocks.py` - モック定義
- `tests/fixtures/mock_responses/` - モックレスポンスデータ

実装内容:
- J-Quants API エンドポイントのモック
- レスポンスデータの管理
- エラーシナリオのサポート

#### 2.2 認証付きクライアントの実装
実装ファイル:
- `tests/fixtures/clients.py` への追加

実装内容:
- JWT トークン生成
- 認証ヘッダー自動付与
- ロールベースのクライアント

#### 2.3 カスタムアサーションの実装
実装ファイル:
- `tests/utils/__init__.py`
- `tests/utils/assertions.py`

実装内容:
- API レスポンス検証
- データベース状態検証
- エラーメッセージ検証

#### 2.4 並列実行対応
実装ファイル:
- `tests/conftest.py` への追加
- `tests/fixtures/database.py` への追加

実装内容:
- ワーカー ID ベースの DB/Redis 分離
- リソース競合の回避

### Phase 3: 拡張機能（オプション）

#### 3.1 E2E テスト環境
実装ファイル:
- `tests/e2e/conftest.py`
- `tests/e2e/fixtures/`

#### 3.2 パフォーマンステスト
実装ファイル:
- `tests/performance/`
- `tests/utils/performance.py`

#### 3.3 テストレポート
実装ファイル:
- `tests/utils/reporter.py`

## 3. 実装手順詳細

### Step 1: 依存関係のインストール
```bash
# 開発依存関係の追加
poetry add --group dev factory-boy==3.3.0
poetry add --group dev pytest-env==1.1.1  
poetry add --group dev pytest-xdist==3.5.0
poetry add --group dev httpx==0.25.2
poetry add --group dev freezegun==1.2.2
```

### Step 2: ディレクトリ構造の作成
```bash
# ディレクトリ作成
mkdir -p tests/fixtures/factories
mkdir -p tests/fixtures/mock_responses
mkdir -p tests/utils
mkdir -p tests/settings
```

### Step 3: 環境設定ファイルの作成
1. `.env.test` を作成
2. `tests/settings/test_config.py` を実装

### Step 4: conftest.py の実装
1. pytest 設定
2. グローバルフィクスチャ
3. プラグイン設定

### Step 5: データベースフィクスチャの実装
1. 接続管理
2. トランザクション管理
3. クリーンアップ

### Step 6: ファクトリーの実装
1. ベースファクトリー
2. エンティティファクトリー

### Step 7: テストクライアントの実装
1. 基本クライアント
2. ヘルパーメソッド

### Step 8: 動作確認
1. サンプルテストの作成
2. 各フィクスチャの動作確認
3. 既存テストの移行確認

## 4. 実装時の注意事項

### 4.1 既存テストとの互換性
- 既存のテストが壊れないように注意
- 段階的な移行をサポート

### 4.2 環境分離
- 本番環境の設定に影響しない
- テスト用 DB は完全に分離

### 4.3 エラーハンドリング
- セットアップ失敗時の適切なエラーメッセージ
- リソースリークの防止

### 4.4 ドキュメント
- 各フィクスチャの使用方法を文書化
- サンプルコードの提供

## 5. テスト計画

### 5.1 単体テスト
- 各フィクスチャの単体テスト
- ファクトリーの動作確認

### 5.2 統合テスト  
- フィクスチャ間の連携確認
- 実際のテストケースでの動作確認

### 5.3 性能テスト
- セットアップ/クリーンアップ時間
- 並列実行時のパフォーマンス

## 6. 移行計画

### 6.1 移行対象
```
現在のテストファイル:
- tests/unit/infrastructure/jquants/test_base_client.py
- tests/unit/infrastructure/jquants/test_auth_repository.py
- tests/unit/infrastructure/jquants/test_jquants_auth_repository.py
- tests/unit/infrastructure/redis/test_redis_auth_repository.py
- tests/unit/application/use_cases/test_auth_use_case.py
- tests/unit/application/use_cases/test_stock_use_case.py
- tests/unit/domain/entities/test_stock.py
- tests/integration/api/test_auth_endpoints.py
```

### 6.2 移行手順
1. 新環境でのサンプルテスト作成
2. 1 ファイルずつ移行
3. 旧フィクスチャの削除
4. CI/CD 設定の更新

## 7. 成果物

### 7.1 Phase 1 完了時
- 基本的なテスト環境の動作
- データベーステストの実行可能
- ファクトリーによるテストデータ生成

### 7.2 Phase 2 完了時  
- 外部 API モックの利用可能
- 認証付きテストの簡易化
- 並列実行による高速化

### 7.3 Phase 3 完了時
- E2E テストの実行環境
- パフォーマンス計測
- 詳細なテストレポート