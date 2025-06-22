# データソース実装計画

## 概要
データソースは、外部API（J-Quants、Yahoo Finance等）への接続情報と認証情報を管理するモデルです。認証情報は暗号化して保存し、必要に応じて復号化して使用します。

## 実装状況

### ✅ 完了済み
1. **暗号化サービス** - 認証情報の安全な保存の基盤
   - `app/services/encryption.py` - 実装済み
   - AES-256-GCM暗号化方式を使用
   - 初期化ベクトル（IV）の自動生成
   - 認証タグによる完全性検証

2. **データソースモデル** - データベーススキーマの定義
   - `app/models/data_source.py` - 実装済み
   - 暗号化された認証情報の保存機能
   - 認証情報の暗号化/復号化メソッド

3. **マイグレーション** - データベーステーブルの作成
   - Alembic設定完了
   - `data_sources` テーブルのマイグレーションファイル生成
   - データベースにテーブル作成完了

4. **依存関係の更新**
   - `pydantic-settings` 追加
   - `pydantic` 2.x系にアップデート
   - `fastapi` と `uvicorn` を互換性のあるバージョンに更新

5. **Pydanticスキーマ** - APIリクエスト/レスポンスの定義
   - `app/schemas/data_source.py` - 実装済み
   - `DataSourceBase`, `DataSourceCreate`, `DataSourceUpdate`
   - `DataSourceResponse`, `TokenResponse`, `DataSourceListResponse`

6. **データソースサービス** - ビジネスロジックの統合
   - `app/services/data_source_service.py` - 実装済み
   - CRUD操作（作成、取得、一覧、更新、削除）
   - トークン取得機能（リフレッシュトークン、IDトークン）

7. **APIエンドポイント** - RESTful APIの提供
   - `app/api/v1/endpoints/data_sources.py` - 実装済み
   - 非同期エンドポイント
   - ページネーション対応
   - トークン取得エンドポイント

### 🔄 進行中
なし

### ⏳ 未実装
1. **認証ストラテジー** (`app/services/auth/`)
   - `BaseAuthStrategy`: 抽象基底クラス
   - `StrategyRegistry`: ストラテジーの登録・取得
   - `JQuantsStrategy`: J-Quants API用
   - `YFinanceStrategy`: Yahoo Finance用

2. **ルーターの登録** - APIエンドポイントの統合
   - メインアプリケーションへのルーター登録

3. **テスト** - 各機能のテスト実装
   - 単体テスト
   - 統合テスト
   - E2Eテスト

## 実装する機能

### 1. データソースモデル (app/models/data_source.py)

#### 基本フィールド
- `id`: 主キー
- `name`: データソース名（必須）
- `description`: 説明
- `provider_type`: プロバイダータイプ（必須、例: "jquants", "yfinance"）
- `is_enabled`: 有効/無効フラグ（デフォルト: True）
- `base_url`: APIのベースURL（必須）
- `api_version`: APIバージョン
- `rate_limit_per_minute`: 分間レート制限（デフォルト: 60）
- `rate_limit_per_hour`: 時間レート制限（デフォルト: 3600）
- `rate_limit_per_day`: 日間レート制限（デフォルト: 86400）
- `encrypted_credentials`: 暗号化された認証情報（バイナリ）
- `created_at`: 作成日時
- `updated_at`: 更新日時

#### 仮想フィールド（Pydanticスキーマ用）
- `credentials`: 認証情報（辞書形式）
- `credentials_json`: 認証情報（JSON文字列）

### 2. 暗号化サービス (app/services/encryption.py)

#### 機能
- 認証情報の暗号化/復号化
- AES-256-GCM暗号化方式を使用
- 初期化ベクトル（IV）の自動生成
- 認証タグによる完全性検証

#### メソッド
- `encrypt(data: str) -> bytes`: データを暗号化
- `decrypt(encrypted_data: bytes) -> str`: データを復号化

### 3. 認証ストラテジー (app/services/auth/)

#### 基本構造
- `BaseAuthStrategy`: 抽象基底クラス
- `StrategyRegistry`: ストラテジーの登録・取得
- 各プロバイダー固有のストラテジー

#### 実装するストラテジー
- `JQuantsStrategy`: J-Quants API用
- `YFinanceStrategy`: Yahoo Finance用

#### 各ストラテジーのメソッド
- `get_refresh_token(credentials: dict) -> dict`: リフレッシュトークン取得
- `get_id_token(refresh_token: str) -> dict`: IDトークン取得

### 4. データソースサービス (app/services/data_source_service.py)

#### 機能
- データソースのCRUD操作
- 認証情報の暗号化/復号化処理
- トークン取得の統合インターフェース

#### メソッド
- `create_data_source(data: dict) -> DataSource`: データソース作成
- `update_data_source(id: int, data: dict) -> DataSource`: データソース更新
- `get_data_source(id: int) -> DataSource`: データソース取得
- `list_data_sources() -> List[DataSource]`: データソース一覧取得
- `delete_data_source(id: int) -> bool`: データソース削除
- `get_refresh_token(data_source_id: int) -> dict`: リフレッシュトークン取得
- `get_id_token(data_source_id: int, refresh_token: str) -> dict`: IDトークン取得

### 5. APIエンドポイント (app/api/v1/endpoints/data_sources.py)

#### エンドポイント
- `POST /api/v1/data-sources`: データソース作成
- `GET /api/v1/data-sources`: データソース一覧取得
- `GET /api/v1/data-sources/{id}`: データソース詳細取得
- `PUT /api/v1/data-sources/{id}`: データソース更新
- `DELETE /api/v1/data-sources/{id}`: データソース削除
- `POST /api/v1/data-sources/{id}/refresh-token`: リフレッシュトークン取得
- `POST /api/v1/data-sources/{id}/id-token`: IDトークン取得

### 6. Pydanticスキーマ (app/schemas/data_source.py)

#### スキーマ
- `DataSourceBase`: 基本フィールド
- `DataSourceCreate`: 作成用スキーマ
- `DataSourceUpdate`: 更新用スキーマ
- `DataSourceResponse`: レスポンス用スキーマ
- `TokenResponse`: トークン取得レスポンス

## 実装順序

1. **暗号化サービス** - 認証情報の安全な保存の基盤 ✅
2. **データソースモデル** - データベーススキーマの定義 ✅
3. **Pydanticスキーマ** - APIリクエスト/レスポンスの定義 ✅
4. **データソースサービス** - ビジネスロジックの統合 ✅
5. **認証ストラテジー** - 各プロバイダー固有の認証ロジック ⏳
6. **APIエンドポイント** - RESTful APIの提供 ✅

## セキュリティ考慮事項

- 認証情報は必ず暗号化して保存
- 環境変数で暗号化キーを管理
- レート制限の実装
- アクセスログの記録
- エラーハンドリングの適切な実装

## テスト計画

- 暗号化/復号化の単体テスト
- 各認証ストラテジーの単体テスト
- データソースサービスの統合テスト
- APIエンドポイントのE2Eテスト
- セキュリティテスト（認証情報の漏洩防止）

## 手動テスト手順

### 前提条件
- Docker Composeサービスが起動していること
- データベースマイグレーションが完了していること

### 1. 環境確認
```bash
# Docker Composeサービスの状態確認
docker compose ps

# 期待される出力例:
# NAME                 IMAGE                  COMMAND                   SERVICE   CREATED         STATUS         PORTS
# stockurajp-db-1      postgres:17-bookworm   "docker-entrypoint.s…"   db        22 hours ago    Up 22 hours    0.0.0.0:5432->5432/tcp
# stockurajp-redis-1   redis:7.2-bookworm     "docker-entrypoint.s…"   redis     22 hours ago    Up 22 hours    0.0.0.0:6379->6379/tcp
# stockurajp-web-1     stockurajp-web         "uvicorn app.main:ap…"   web       5 minutes ago   Up 5 minutes   0.0.0.0:8000->8000/tcp
```

### 2. アプリケーション起動確認
```bash
# ルートエンドポイントの確認
curl -X GET "http://localhost:8000/" -H "accept: application/json"

# 期待される出力:
# {"message": "Welcome to Stockura API"}
```

### 3. データソースAPIエンドポイントのテスト

#### 3.1 データソース一覧取得
```bash
# 空のデータソース一覧を取得
curl -X GET "http://localhost:8000/api/v1/data-sources/" -H "accept: application/json"

# 期待される出力:
# {"data_sources":[],"total":0,"page":1,"per_page":100}
```

#### 3.2 データソース作成
```bash
# J-Quantsデータソースを作成
curl -X POST "http://localhost:8000/api/v1/data-sources/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "J-Quants API",
    "description": "J-Quants API for Japanese stock data",
    "provider_type": "jquants",
    "is_enabled": true,
    "base_url": "https://api.jquants.com",
    "api_version": "v1",
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 3600,
    "rate_limit_per_day": 86400,
    "credentials": {
      "client_id": "test_client_id",
      "client_secret": "test_client_secret"
    }
  }'

# 期待される出力例:
# {
#   "id": 1,
#   "name": "J-Quants API",
#   "description": "J-Quants API for Japanese stock data",
#   "provider_type": "jquants",
#   "is_enabled": true,
#   "base_url": "https://api.jquants.com",
#   "api_version": "v1",
#   "rate_limit_per_minute": 60,
#   "rate_limit_per_hour": 3600,
#   "rate_limit_per_day": 86400,
#   "created_at": "2024-01-01T00:00:00",
#   "updated_at": "2024-01-01T00:00:00"
# }
```

#### 3.3 データソース詳細取得
```bash
# 作成したデータソースの詳細を取得
curl -X GET "http://localhost:8000/api/v1/data-sources/1" -H "accept: application/json"

# 期待される出力: 作成時のデータと同じ内容
```

#### 3.4 データソース更新
```bash
# データソースの説明を更新
curl -X PUT "http://localhost:8000/api/v1/data-sources/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description for J-Quants API"
  }'

# 期待される出力: 更新されたデータ
```

#### 3.5 データソース一覧取得（更新後）
```bash
# 更新後のデータソース一覧を取得
curl -X GET "http://localhost:8000/api/v1/data-sources/" -H "accept: application/json"

# 期待される出力:
# {
#   "data_sources": [
#     {
#       "id": 1,
#       "name": "J-Quants API",
#       "description": "Updated description for J-Quants API",
#       ...
#     }
#   ],
#   "total": 1,
#   "page": 1,
#   "per_page": 100
# }
```

#### 3.6 データソース削除
```bash
# データソースを削除
curl -X DELETE "http://localhost:8000/api/v1/data-sources/1" -H "accept: application/json"

# 期待される出力:
# {"message": "Data source deleted successfully"}
```

#### 3.7 削除後の確認
```bash
# 削除後のデータソース一覧を取得
curl -X GET "http://localhost:8000/api/v1/data-sources/" -H "accept: application/json"

# 期待される出力:
# {"data_sources":[],"total":0,"page":1,"per_page":100}
```

### 4. エラーハンドリングのテスト

#### 4.1 存在しないデータソースの取得
```bash
# 存在しないIDでデータソースを取得
curl -X GET "http://localhost:8000/api/v1/data-sources/999" -H "accept: application/json"

# 期待される出力:
# {"detail": "Data source not found"}
```

#### 4.2 無効なデータでの作成
```bash
# 必須フィールドが不足したデータで作成
curl -X POST "http://localhost:8000/api/v1/data-sources/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Data Source"
  }'

# 期待される出力: バリデーションエラー
```

### 5. ページネーションのテスト
```bash
# 複数のデータソースを作成後、ページネーションパラメータを指定
curl -X GET "http://localhost:8000/api/v1/data-sources/?skip=0&limit=5" -H "accept: application/json"

# 期待される出力: 指定したページネーション設定でのレスポンス
```

### 6. フィルタリングのテスト
```bash
# 有効なデータソースのみを取得
curl -X GET "http://localhost:8000/api/v1/data-sources/?is_enabled=true" -H "accept: application/json"

# 期待される出力: is_enabled=trueのデータソースのみ
```

### 7. ログ確認
```bash
# アプリケーションログの確認
docker compose logs web --tail=50

# エラーが発生した場合の詳細確認
docker compose logs web --tail=100 | grep ERROR
```

### 8. データベース確認
```bash
# データベースに直接接続してデータを確認
docker compose exec db psql -U postgres -d stockura -c "SELECT * FROM data_sources;"
```

## 次のステップ

### 優先度1: 基本機能の完成
1. **ルーターの登録** - APIエンドポイントの統合
   - `app/main.py` にデータソースルーターを登録
   - メインアプリケーションでの動作確認

2. **認証ストラテジーの基本実装**
   - `BaseAuthStrategy`: 抽象基底クラス
   - `StrategyRegistry`: ストラテジーの登録・取得
   - モックストラテジー: テスト用のダミー実装

### 優先度2: プロバイダー固有の実装
3. **J-Quants認証ストラテジー**
   - `JQuantsStrategy`: J-Quants API用の認証ロジック
   - リフレッシュトークン取得
   - IDトークン取得

4. **Yahoo Finance認証ストラテジー**
   - `YFinanceStrategy`: Yahoo Finance用の認証ロジック
   - API認証の実装

### 優先度3: 品質向上
5. **テスト実装**
   - 単体テスト: 各サービスのテスト
   - 統合テスト: APIエンドポイントのテスト
   - E2Eテスト: 完全なワークフローのテスト

6. **エラーハンドリングの強化**
   - 適切なエラーレスポンス
   - ログ出力の改善
   - バリデーションの強化

### 優先度4: 運用準備
7. **ドキュメント整備**
   - API仕様書の作成
   - 運用マニュアルの作成

8. **セキュリティ強化**
   - レート制限の実装
   - アクセス制御の追加
   - 監査ログの実装
