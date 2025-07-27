# ファイル構造と各ファイルの詳細な役割

## Domain Layer（ドメイン層）

### Entities（エンティティ）

#### `app/domain/entities/auth.py`
J-Quants API 認証に関するエンティティとバリューオブジェクトを定義。

- **RefreshToken**: リフレッシュトークンのバリューオブジェクト
  - 値の妥当性検証（空でないこと）
  - 不変性の保証（@dataclass(frozen=True)）

- **IdToken**: ID トークンのバリューオブジェクト
  - トークン値と有効期限を保持
  - 期限切れチェック機能（is_expired）
  - まもなく期限切れになるかのチェック（is_expiring_soon）

- **JQuantsCredentials**: 認証情報のエンティティ
  - メールアドレス、パスワード、各種トークンを管理
  - トークンの有効性チェック（has_valid_id_token）
  - トークン更新の必要性判定（needs_refresh）
  - トークン情報の更新メソッド

#### `app/domain/entities/stock.py`
株式銘柄に関するエンティティとバリューオブジェクトを定義。

- **MarketCode**: 市場区分コードの Enum
  - プライム、スタンダード、グロースなど全市場区分を定義
  - 旧市場区分（東証 1 部、マザーズなど）も含む

- **SectorCode17/SectorCode33**: 業種コードの Enum
  - 17 業種分類と 33 業種分類をそれぞれ定義
  - 日本の証券コード協議会の業種分類に準拠

- **StockCode**: 銘柄コードのバリューオブジェクト
  - 4 桁数字の検証
  - 不変性の保証

- **Stock**: 銘柄情報のエンティティ
  - 銘柄の基本情報（コード、会社名、業種、市場区分など）を保持
  - 辞書からエンティティへの変換機能（from_dict）
  - 市場区分の判定メソッド（is_prime_market 等）

- **StockList**: 銘柄リストのバリューオブジェクト
  - 複数の銘柄をまとめて管理
  - 銘柄コードによる検索（get_by_code）
  - 市場区分・業種によるフィルタリング
  - 会社名による検索（日本語・英語対応）

### Repositories（リポジトリインターフェース）

#### `app/domain/repositories/auth_repository.py`
認証データアクセスの抽象インターフェース。

- **get_refresh_token**: メールアドレスとパスワードからリフレッシュトークンを取得
- **get_id_token**: リフレッシュトークンから ID トークンを取得
- **save_credentials**: 認証情報の永続化
- **load_credentials**: 保存された認証情報の読み込み

#### `app/domain/repositories/stock_repository.py`
銘柄情報データアクセスの抽象インターフェース。

- **get_listed_stocks**: 上場銘柄一覧の取得
- **get_stock_by_code**: 銘柄コードによる個別銘柄の取得
- **search_stocks**: キーワード・条件による銘柄検索
- **save_stock_list**: 銘柄一覧のキャッシュ保存
- **load_cached_stock_list**: キャッシュされた銘柄一覧の読み込み

### Exceptions（例外）

#### `app/domain/exceptions/jquants_exceptions.py`
J-Quants API 関連の例外定義。

- **JQuantsException**: 基底例外クラス
- **AuthenticationError**: 認証失敗時の例外
- **TokenRefreshError**: トークン更新失敗時の例外
- **NetworkError**: ネットワーク通信エラー
- **RateLimitError**: レート制限エラー
- **DataNotFoundError**: データが見つからない場合の例外
- **ValidationError**: バリデーションエラー
- **StorageError**: ストレージ操作エラー

## Application Layer（アプリケーション層）

### Use Cases（ユースケース）

#### `app/application/use_cases/auth_use_case.py`
認証に関するビジネスロジックを実装。

- **authenticate**: 新規認証またはキャッシュからの認証情報取得
  - 既存の有効なトークンがある場合は再利用
  - ない場合は新規にトークンを取得
  - 認証情報の永続化

- **refresh_token**: ID トークンの更新
  - リフレッシュトークンを使用して ID トークンを再取得
  - 失敗時は再認証にフォールバック

- **ensure_valid_token**: 有効なトークンの確保
  - 期限切れまたは期限切れ間近の場合は自動更新

- **get_valid_credentials**: 保存済み認証情報の取得
  - 有効な認証情報のみを返す

#### `app/application/use_cases/stock_use_case.py`
銘柄情報に関するビジネスロジックを実装。

- **get_all_stocks**: 全銘柄一覧の取得
  - キャッシュ優先の取得戦略
  - キャッシュがない場合は API から取得して保存

- **get_stock_by_code**: 個別銘柄の取得
  - 銘柄コードのバリデーション
  - 存在しない場合の適切なエラーハンドリング

- **search_stocks**: 銘柄の検索
  - キーワードによる会社名検索
  - 市場区分・業種によるフィルタリング

- **get_stocks_by_market**: 市場区分別の銘柄取得
- **get_stocks_by_sector_17/33**: 業種別の銘柄取得
- **refresh_stock_cache**: キャッシュの強制更新

## Infrastructure Layer（インフラストラクチャ層）

### JQuants API 実装

#### `app/infrastructure/jquants/base_client.py`
J-Quants API 通信の基底クライアント。

- **HTTP クライアント機能**:
  - 非同期通信（aiohttp 使用）
  - 自動リトライ機能（最大 3 回）
  - Gzip 圧縮レスポンスの処理
  - 認証ヘッダーの自動付与

- **エラーハンドリング**:
  - レート制限エラーの検出と処理
  - ネットワークエラーの適切な変換
  - JSON パースエラーの処理

- **ページネーション対応**:
  - get_paginated メソッドで全ページ取得
  - pagination_key を使用した連続取得

#### `app/infrastructure/jquants/auth_repository_impl.py`
認証リポジトリの具体的な実装。

- **J-Quants API 認証フロー**:
  - `/token/auth_user`: リフレッシュトークン取得
  - `/token/auth_refresh`: ID トークン取得

- **認証情報の永続化**:
  - メモリキャッシュとファイルストレージの 2 層構造
  - JSON ファイルへの保存（オプション）
  - トークンの有効期限情報も保存

#### `app/infrastructure/jquants/stock_repository_impl.py`
銘柄情報リポジトリの具体的な実装。

- **API 通信**:
  - `/listed/info`エンドポイントからの銘柄情報取得
  - ページネーション対応で全銘柄取得
  - 認証トークンの自動更新

- **キャッシュ機能**:
  - ローカルファイルシステムへのキャッシュ
  - JSON 形式での銘柄一覧保存
  - 更新日付の管理

- **検索・フィルタリング**:
  - メモリ上での高速検索
  - 複数条件での絞り込み

## Tests（テスト）

### Unit Tests

#### `tests/unit/domain/entities/test_stock.py`
Stock エンティティの単体テスト。

- **StockCode のテスト**:
  - 正常な銘柄コードの検証
  - 空文字、不正な長さ、数字以外の検証

- **Stock エンティティのテスト**:
  - 正常なインスタンス生成
  - 必須フィールドの検証
  - 辞書からの変換機能
  - 無効なコードの処理

- **StockList のテスト**:
  - リスト操作の検証
  - 検索・フィルタリング機能
  - 日本語・英語での会社名検索

#### `tests/unit/application/use_cases/test_auth_use_case.py`
認証ユースケースの単体テスト。

- **認証フローのテスト**:
  - 新規認証
  - キャッシュからの認証情報取得
  - 認証失敗時の処理

- **トークン更新のテスト**:
  - 正常なリフレッシュ
  - リフレッシュトークンがない場合の再認証
  - 期限切れトークンの処理

- **モックを使用した依存性の分離**:
  - リポジトリ層のモック化
  - 非同期処理のテスト

## 設定ファイル

### `requirements.txt`
プロジェクトの依存パッケージを定義。

- **Web フレームワーク**: FastAPI, uvicorn
- **データベース**: SQLAlchemy, asyncpg, alembic
- **キャッシュ**: redis, hiredis
- **タスクキュー**: Celery, flower
- **外部 API**: httpx, yfinance, aiohttp
- **開発ツール**: black, isort, flake8, mypy
- **テスト**: pytest, pytest-asyncio, pytest-cov

## 今後実装が必要なファイル

### Presentation Layer
- `app/main.py`: FastAPI アプリケーションのエントリーポイント
- `app/presentation/api/v1/endpoints/auth.py`: 認証エンドポイント
- `app/presentation/api/v1/endpoints/stocks.py`: 銘柄情報エンドポイント
- `app/presentation/schemas/`: リクエスト/レスポンススキーマ
- `app/presentation/middleware/`: エラーハンドラー、認証ミドルウェア

### Infrastructure Layer
- `app/infrastructure/database/`: データベース接続とモデル
- `app/infrastructure/cache/`: Redis キャッシュ実装
- `app/infrastructure/job_queue/`: Celery タスク定義

### Configuration
- `app/core/config.py`: アプリケーション設定
- `.env.example`: 環境変数のサンプル
- `app/core/dependencies.py`: 依存性注入の設定