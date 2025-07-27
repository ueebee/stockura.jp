# テスト環境整備 設計仕様書

## 1. アーキテクチャ概要

### 1.1 全体構成
```
┌─────────────────────────────────────────────────────────┐
│                      テスト実行環境                        │
├─────────────────────────────────────────────────────────┤
│  pytest Framework                                       │
│  ├─ conftest.py (グローバル設定)                         │
│  ├─ fixtures/ (共有フィクスチャ)                         │
│  ├─ utils/ (テストユーティリティ)                        │
│  └─ tests/ (テストケース)                               │
├─────────────────────────────────────────────────────────┤
│  Test Infrastructure                                    │
│  ├─ Test Database (PostgreSQL)                         │
│  ├─ Test Redis                                         │
│  └─ Mock Servers (J-Quants API 等)                      │
└─────────────────────────────────────────────────────────┘
```

### 1.2 レイヤー構成
1. **テストフレームワークレイヤー** - pytest 及び関連プラグイン
2. **フィクスチャレイヤー** - テストデータとモックの管理
3. **ユーティリティレイヤー** - 共通ヘルパー関数
4. **テストケースレイヤー** - 実際のテストコード

## 2. 詳細設計

### 2.1 ディレクトリ構造
```
tests/
├── conftest.py                  # グローバルフィクスチャと pytest 設定
├── fixtures/
│   ├── __init__.py
│   ├── database.py              # DB 接続とトランザクション管理
│   ├── factories/               # FactoryBoy ファクトリー定義
│   │   ├── __init__.py
│   │   ├── auth.py              # 認証関連のファクトリー
│   │   ├── stock.py             # 株式関連のファクトリー
│   │   └── base.py              # ベースファクトリー
│   ├── clients.py               # テストクライアント定義
│   └── mocks.py                 # 外部 API モック定義
├── utils/
│   ├── __init__.py
│   ├── assertions.py            # カスタムアサーション
│   ├── helpers.py               # ヘルパー関数
│   └── test_data.py             # テスト用定数とサンプルデータ
├── settings/
│   ├── __init__.py
│   └── test_config.py           # テスト環境設定
├── unit/                        # 単体テスト
├── integration/                 # 統合テスト
└── e2e/                         # E2E テスト
```

### 2.2 主要コンポーネント設計

#### 2.2.1 conftest.py
```python
# グローバルフィクスチャと pytest 設定
- pytest_configure: pytest 設定のカスタマイズ
- pytest_sessionstart: セッション開始時の初期化
- pytest_sessionfinish: セッション終了時のクリーンアップ
- event_loop: 非同期テスト用のイベントループ
```

#### 2.2.2 database.py
```python
# データベース関連フィクスチャ
- test_db: テスト用データベース接続
- db_session: トランザクション管理された DB セッション
- migrated_db: マイグレーション済みのテスト DB
- clean_db: 各テスト後の DB クリーンアップ
```

#### 2.2.3 factories/
```python
# FactoryBoy を使用したテストデータ生成
- BaseFactory: 共通の設定を持つベースクラス
- UserFactory: ユーザーエンティティの生成
- StockFactory: 株式エンティティの生成
- JQuantsCredentialsFactory: 認証情報の生成
```

#### 2.2.4 clients.py
```python
# テスト用 HTTP クライアント
- test_client: 基本的なテストクライアント
- auth_client: 認証済みテストクライアント
- admin_client: 管理者権限付きクライアント
```

#### 2.2.5 mocks.py
```python
# 外部 API のモック
- mock_jquants_api: J-Quants API のモック
- mock_redis: Redis のモック（必要に応じて）
```

### 2.3 テスト実行フロー

#### 2.3.1 セットアップフロー
1. pytest 起動
2. conftest.py のグローバル設定読み込み
3. テストデータベース作成・マイグレーション
4. Redis テスト環境準備
5. 必要なモックサーバー起動

#### 2.3.2 テスト実行フロー
1. テストケース開始
2. 必要なフィクスチャの注入
3. データベーストランザクション開始
4. テスト実行
5. トランザクションロールバック
6. リソースクリーンアップ

#### 2.3.3 クリーンアップフロー
1. 各テスト後のトランザクションロールバック
2. Redis データクリア
3. 一時ファイル削除
4. セッション終了時のデータベース削除

### 2.4 設定管理

#### 2.4.1 環境変数
```bash
# .env.test
DATABASE_URL=postgresql://test_user:test_pass@localhost/stockura_test
REDIS_URL=redis://localhost:6379/1
JQUANTS_API_BASE_URL=http://localhost:8001
TEST_MODE=true
```

#### 2.4.2 pytest.ini 拡張
```ini
[tool.pytest.ini_options]
# 既存の設定に追加
env_files = [".env.test"]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 2.5 並列実行対応

#### 2.5.1 データベース分離
- 各ワーカープロセスごとに独立した DB スキーマを使用
- スキーマ名: `test_{worker_id}`

#### 2.5.2 Redis 分離
- 各ワーカーごとに異なる DB インデックスを使用
- DB インデックス: `worker_id + 1`

### 2.6 モック戦略

#### 2.6.1 J-Quants API モック
- レスポンスデータを JSON ファイルとして管理
- シナリオベースのモック応答
- エラーケースのシミュレーション

#### 2.6.2 時刻のモック
- freezegun を使用した時刻固定
- タイムゾーン考慮

### 2.7 デバッグサポート

#### 2.7.1 VSCode 設定
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "--no-cov",
        "-v"
    ]
}
```

#### 2.7.2 デバッグ時の設定
- トランザクションロールバックの無効化オプション
- 詳細なログ出力

## 3. 実装の優先順位

### Phase 1 (必須)
1. conftest.py の基本設定
2. データベースフィクスチャ
3. 基本的なテストクライアント
4. FactoryBoy の導入と基本ファクトリー

### Phase 2 (推奨)
1. J-Quants API モック
2. 認証付きクライアント
3. カスタムアサーション
4. 並列実行対応

### Phase 3 (オプション)
1. E2E テスト環境
2. パフォーマンステスト支援
3. テストレポート生成

## 4. 技術選定理由

### 4.1 FactoryBoy
- Django で実績がある
- 柔軟なデータ生成
- リレーションの扱いが簡単

### 4.2 pytest-xdist
- 並列実行による高速化
- ワーカー分離が容易

### 4.3 httpx
- FastAPI との相性が良い
- 非同期対応
- テストクライアントとして推奨

## 5. 移行計画

### 5.1 既存テストへの影響
- 既存テストは段階的に新環境へ移行
- 旧テストも一時的に並行稼働可能

### 5.2 移行手順
1. 新環境の構築
2. サンプルテストでの検証
3. 既存テストの段階的移行
4. 旧環境の廃止