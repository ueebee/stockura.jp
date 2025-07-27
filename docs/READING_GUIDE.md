# コード読解ガイド

このドキュメントは、 Stockura プロジェクトのコードを効率的に理解するための読み進め方を説明します。

## 推奨される読み進め順序

### 1. ドキュメントから始める（概要把握）
最初にプロジェクトの全体像を理解するため、以下のドキュメントを読むことをお勧めします：

- **`docs/ARCHITECTURE.md`** - システム全体のアーキテクチャ設計
- **`docs/CLEAN_ARCHITECTURE_DIAGRAM.md`** - クリーンアーキテクチャの図解と説明
- **`docs/FILE_STRUCTURE.md`** - ディレクトリ構造とファイルの役割

### 2. エントリーポイント（起動の流れ）
アプリケーションがどのように起動するかを理解します：

- **`app/main.py`** - FastAPI アプリケーションの起点
- **`app/core/config.py`** - 環境変数と設定管理

### 3. ドメイン層（ビジネスロジックの中核）
ビジネスルールとエンティティを理解します：

- **`app/domain/entities/auth.py`** - 認証関連のエンティティ（JQuantsCredentials 等）
- **`app/domain/entities/stock.py`** - 株価データのエンティティ（Stock, DailyQuote 等）
- **`app/domain/repositories/`** - リポジトリインターフェース（抽象化）
- **`app/domain/exceptions/`** - カスタム例外クラス

### 4. アプリケーション層（ユースケース）
ビジネスロジックの実装を理解します：

- **`app/application/use_cases/auth_use_case.py`** - 認証フローの実装
- **`app/application/use_cases/stock_use_case.py`** - 株価データ取得の実装

### 5. プレゼンテーション層（API）
外部との接点を理解します：

- **`app/presentation/api/v1/endpoints/auth.py`** - 認証 API エンドポイント
- **`app/presentation/api/v1/__init__.py`** - API ルーターの設定

### 6. インフラストラクチャ層（外部連携）
外部サービスとの連携実装を理解します：

- **`app/infrastructure/jquants/base_client.py`** - J-Quants API クライアントの基底クラス
- **`app/infrastructure/jquants/auth_repository_impl.py`** - J-Quants 認証の実装
- **`app/infrastructure/redis/auth_repository_impl.py`** - Redis 認証キャッシュの実装
- **`app/infrastructure/redis/redis_client.py`** - Redis 接続管理

### 7. テストコード（動作理解）
実際の使用例とテストケースから動作を理解します：

- **`tests/unit/`** - 各コンポーネントの単体テスト
  - `domain/entities/` - エンティティのテスト
  - `application/use_cases/` - ユースケースのテスト
  - `infrastructure/` - 外部連携のテスト
- **`tests/integration/`** - API エンドポイントの統合テスト

## 読解のポイント

### クリーンアーキテクチャの層構造
1. **依存性の方向**: 外側から内側への一方向のみ
   - Presentation → Application → Domain
   - Infrastructure → Domain

2. **各層の責務**:
   - **Domain**: ビジネスルールとエンティティ
   - **Application**: ユースケース（ビジネスロジックの実行）
   - **Infrastructure**: 外部サービスとの連携
   - **Presentation**: ユーザーインターフェース（API）

### 非同期処理
- すべての処理は`async/await`を使用した非同期処理
- `aiohttp`と`aioredis`を使用した非同期 I/O

### 認証フロー
1. J-Quants のメールアドレス/パスワードでログイン
2. リフレッシュトークン（7 日間有効）を取得
3. ID トークン（24 時間有効）を取得
4. Redis に認証情報をキャッシュ

### エラーハンドリング
- カスタム例外クラスによる明確なエラー分類
- HTTP ステータスコードへの適切なマッピング

## 次のステップ

コードを読み終えたら：
1. `docs/auth-verification.md`を参照して認証機能を実際に動かしてみる
2. 新しい機能を追加する場合は、既存のパターンに従う
3. テストを書いて動作を確認する
