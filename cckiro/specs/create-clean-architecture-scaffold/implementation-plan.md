# 実装計画書：クリーンアーキテクチャベースのアプリケーション雛形

## 1. 実装フェーズ概要

### フェーズ分割と優先順位
1. **Phase 1: 基盤構築** - プロジェクト構造と共通設定
2. **Phase 2: ドメイン層** - エンティティと値オブジェクト
3. **Phase 3: アプリケーション層** - インターフェースとユースケース
4. **Phase 4: インフラストラクチャ層** - データベースと外部 API 連携
5. **Phase 5: プレゼンテーション層** - FastAPI 実装
6. **Phase 6: テストとドキュメント** - テストコードとドキュメント整備

## 2. Phase 1: 基盤構築（推定時間: 2 時間）

### 2.1 ディレクトリ構造の作成
```bash
# 全体のディレクトリ構造を作成
mkdir -p app/{domain,application,infrastructure,presentation,core}
mkdir -p app/domain/{entities,value_objects,exceptions,services}
mkdir -p app/application/{use_cases,interfaces,dtos}
mkdir -p app/infrastructure/{database,cache,external_api,job_queue}
mkdir -p app/presentation/{api,schemas,middleware}
mkdir -p tests/{unit,integration}
mkdir -p scripts
mkdir -p docker
```

### 2.2 必要なファイルの作成
- [ ] 各ディレクトリに`__init__.py`を作成
- [ ] `requirements.txt`の作成
- [ ] `requirements-dev.txt`の作成
- [ ] `.env.example`の作成
- [ ] `.gitignore`の作成
- [ ] `pyproject.toml`の作成

### 2.3 基本設定の実装
- [ ] `app/core/config.py` - 設定管理クラス
- [ ] `app/core/constants.py` - 定数定義
- [ ] `app/core/logger.py` - ロギング設定

## 3. Phase 2: ドメイン層（推定時間: 3 時間）

### 3.1 エンティティの実装
- [ ] `app/domain/entities/stock.py` - Stock エンティティ
- [ ] `app/domain/entities/price.py` - Price エンティティ

### 3.2 値オブジェクトの実装
- [ ] `app/domain/value_objects/ticker_symbol.py` - ティッカーシンボル
- [ ] `app/domain/value_objects/time_period.py` - 期間

### 3.3 ドメイン例外の実装
- [ ] `app/domain/exceptions/stock_exceptions.py` - ドメイン固有の例外

### 3.4 ドメインサービスの実装
- [ ] `app/domain/services/price_calculator.py` - 価格計算サービス

## 4. Phase 3: アプリケーション層（推定時間: 3 時間）

### 4.1 インターフェースの定義
- [ ] `app/application/interfaces/repositories/stock_repository.py` - リポジトリインターフェース
- [ ] `app/application/interfaces/external/jquants_client.py` - J-Quants クライアントインターフェース
- [ ] `app/application/interfaces/external/yfinance_client.py` - yFinance クライアントインターフェース

### 4.2 DTO の実装
- [ ] `app/application/dtos/stock_dto.py` - 株式データ転送オブジェクト

### 4.3 ユースケースの実装
- [ ] `app/application/use_cases/fetch_stock_price.py` - 株価取得ユースケース
- [ ] `app/application/use_cases/analyze_stock.py` - 株式分析ユースケース

## 5. Phase 4: インフラストラクチャ層（推定時間: 4 時間）

### 5.1 データベース関連
- [ ] `app/infrastructure/database/connection.py` - DB 接続管理
- [ ] `app/infrastructure/database/models/stock_model.py` - SQLAlchemy モデル
- [ ] `app/infrastructure/database/repositories/stock_repository_impl.py` - リポジトリ実装

### 5.2 キャッシュ関連
- [ ] `app/infrastructure/cache/redis_client.py` - Redis クライアント

### 5.3 外部 API 連携
- [ ] `app/infrastructure/external_api/jquants/client.py` - J-Quants クライアント実装
- [ ] `app/infrastructure/external_api/yfinance/client.py` - yFinance クライアント実装

### 5.4 ジョブキュー
- [ ] `app/infrastructure/job_queue/celery_app.py` - Celery アプリケーション設定
- [ ] `app/infrastructure/job_queue/tasks/stock_tasks.py` - 株式関連タスク

## 6. Phase 5: プレゼンテーション層（推定時間: 4 時間）

### 6.1 API エンドポイント
- [ ] `app/presentation/api/v1/router.py` - メインルーター
- [ ] `app/presentation/api/v1/endpoints/stocks.py` - 株式エンドポイント
- [ ] `app/presentation/api/v1/endpoints/health.py` - ヘルスチェック
- [ ] `app/presentation/api/dependencies.py` - 依存性注入設定

### 6.2 スキーマ定義
- [ ] `app/presentation/schemas/stock_schema.py` - 株式スキーマ
- [ ] `app/presentation/schemas/common_schema.py` - 共通スキーマ

### 6.3 ミドルウェア
- [ ] `app/presentation/middleware/error_handler.py` - エラーハンドリング
- [ ] `app/presentation/middleware/logging.py` - ロギングミドルウェア

### 6.4 メインアプリケーション
- [ ] `app/main.py` - FastAPI アプリケーションのエントリーポイント
- [ ] `app/core/container.py` - DI コンテナ設定

## 7. Phase 6: テストとドキュメント（推定時間: 3 時間）

### 7.1 テストコード
- [ ] `tests/conftest.py` - pytest 設定
- [ ] `tests/unit/domain/test_stock_entity.py` - エンティティのテスト
- [ ] `tests/unit/application/test_fetch_stock_price.py` - ユースケースのテスト
- [ ] `tests/integration/api/test_stock_endpoints.py` - API エンドポイントのテスト

### 7.2 ドキュメントとスクリプト
- [ ] `scripts/init_db.py` - データベース初期化スクリプト
- [ ] `docker/Dockerfile` - Docker ファイル
- [ ] `docker/docker-compose.yml` - Docker Compose 設定
- [ ] プロジェクト README の更新

## 8. 実装時の注意事項

### 8.1 コーディング規約
- PEP 8 に準拠
- 型ヒントを必ず使用
- docstring を適切に記述

### 8.2 依存関係の管理
- 各層の依存関係の方向を厳守
- インターフェースを介した疎結合な設計

### 8.3 エラーハンドリング
- 各層で適切な例外を定義・使用
- エラーメッセージは具体的かつユーザーフレンドリーに

### 8.4 テスト
- 各実装と同時にテストコードを作成
- カバレッジ 80% 以上を目標

## 9. 進捗管理

### 9.1 進捗確認ポイント
- 各 Phase の完了時にテストを実行
- コードレビューの実施（セルフレビュー）
- ドキュメントの更新

### 9.2 完了基準
- [ ] 全てのテストがパス
- [ ] lint エラーがない
- [ ] 型チェックがパス
- [ ] アプリケーションが正常に起動
- [ ] サンプル API エンドポイントが動作

## 10. 実装順序の最適化

効率的な実装のため、以下の順序を推奨：
1. コア設定（config, logger）
2. ドメインエンティティ
3. リポジトリインターフェース
4. 簡単なユースケース
5. インメモリリポジトリ実装（テスト用）
6. API エンドポイント（1 つ）
7. 動作確認
8. 残りの実装を並行して進める