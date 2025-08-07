# データ取得機構削除の実装計画書

## 1. 実装概要

設計書に基づき、 trades_spec 、 weekly_margin_interest 、 announcement の 3 つのデータ取得機構を段階的に削除します。外側の層から内側の層へ向かって削除を実施し、各ステップで動作確認を行います。

## 2. 実装フェーズと作業項目

### Phase 1: API エンドポイントの無効化

#### 1.1 API ルーターの更新
**ファイル**: `app/presentation/api/v1/__init__.py`
- [ ] trades_spec 関連のインポートを削除
- [ ] weekly_margin_interest 関連のインポートを削除  
- [ ] announcement 関連のインポートを削除
- [ ] 各ルーターの登録を削除（3 箇所）

#### 1.2 動作確認
- [ ] アプリケーションが起動することを確認
- [ ] 削除したエンドポイントにアクセスして 404 が返ることを確認

### Phase 2: バックグラウンドタスクの停止

#### 2.1 Celery タスクの削除
**削除ファイル**:
- [ ] `app/infrastructure/celery/tasks/trades_spec_task_asyncpg.py`
- [ ] `app/infrastructure/celery/tasks/weekly_margin_interest_task_asyncpg.py`
- [ ] `app/infrastructure/celery/tasks/announcement_task_asyncpg.py`

#### 2.2 Celery 設定の更新
**ファイル**: `app/infrastructure/celery/tasks/__init__.py`
- [ ] announcement_task_asyncpg のインポートを削除
- [ ] trades_spec_task_asyncpg のインポートを削除
- [ ] weekly_margin_interest_task_asyncpg のインポートを削除（存在する場合）

**ファイル**: `app/infrastructure/celery/config.py`
- [ ] fetch_trades_spec_task_asyncpg のルーティング設定を削除

#### 2.3 動作確認
- [ ] Celery ワーカーが起動することを確認
- [ ] エラーログが出力されていないことを確認

### Phase 3: ビジネスロジックの削除

#### 3.1 API エンドポイントファイルの削除
**削除ファイル**:
- [ ] `app/presentation/api/v1/endpoints/trades_spec.py`
- [ ] `app/presentation/api/v1/endpoints/weekly_margin_interest.py`
- [ ] `app/presentation/api/v1/endpoints/announcement.py`

#### 3.2 UseCase の削除
**削除ファイル**:
- [ ] `app/application/use_cases/fetch_trades_spec.py`
- [ ] `app/application/use_cases/fetch_weekly_margin_interest.py`
- [ ] `app/application/use_cases/fetch_announcement.py`

#### 3.3 DTO の削除とインポート更新
**削除ファイル**:
- [ ] `app/application/dtos/trades_spec_dto.py`
- [ ] `app/application/dtos/weekly_margin_interest_dto.py`
- [ ] `app/application/dtos/announcement_dto.py`

**ファイル**: `app/application/dtos/__init__.py`
- [ ] 関連するインポートを削除（3 箇所）

#### 3.4 外部インターフェースの削除
**削除ファイル**:
- [ ] `app/application/interfaces/external/announcement_client.py`

#### 3.5 J-Quants クライアントの削除
**削除ファイル**:
- [ ] `app/infrastructure/jquants/trades_spec_client.py`
- [ ] `app/infrastructure/jquants/weekly_margin_interest_client.py`
- [ ] `app/infrastructure/jquants/announcement_client.py`

**ファイル**: `app/infrastructure/jquants/client_factory.py`
- [ ] 関連するインポートを削除（3 箇所）
- [ ] create_trades_spec_client() メソッドを削除
- [ ] create_weekly_margin_interest_client() メソッドを削除
- [ ] create_announcement_client() メソッドを削除

### Phase 4: ドメイン層の削除

#### 4.1 Entity の削除とインポート更新
**削除ファイル**:
- [ ] `app/domain/entities/trades_spec.py`
- [ ] `app/domain/entities/weekly_margin_interest.py`
- [ ] `app/domain/entities/announcement.py`

**ファイル**: `app/domain/entities/__init__.py`
- [ ] 関連するインポートを削除（3 箇所）

#### 4.2 Repository Interface の削除とインポート更新
**削除ファイル**:
- [ ] `app/domain/repositories/trades_spec_repository.py`
- [ ] `app/domain/repositories/weekly_margin_interest_repository.py`
- [ ] `app/domain/repositories/announcement_repository.py`

**ファイル**: `app/domain/repositories/__init__.py`
- [ ] 関連するインポートを削除（3 箇所）

### Phase 5: インフラストラクチャ層の削除

#### 5.1 Repository 実装の削除
**削除ファイル**:
- [ ] `app/infrastructure/repositories/database/trades_spec_repository_impl.py`
- [ ] `app/infrastructure/repositories/database/weekly_margin_interest_repository_impl.py`
- [ ] `app/infrastructure/repositories/database/announcement_repository_impl.py`

#### 5.2 Database Model の削除とインポート更新
**削除ファイル**:
- [ ] `app/infrastructure/database/models/trades_spec.py`
- [ ] `app/infrastructure/database/models/weekly_margin_interest.py`
- [ ] `app/infrastructure/database/models/announcement.py`

**ファイル**: `app/infrastructure/database/models/__init__.py`
- [ ] 関連するインポートを削除（3 箇所）

### Phase 6: スクリプトファイルの削除

**削除ファイル**:
- [ ] `scripts/test_trades_spec.py`
- [ ] `scripts/test_trades_spec_direct.py`
- [ ] `scripts/test_celery_trades_spec_debug.py`
- [ ] `scripts/debug_trades_spec_api.py`
- [ ] `scripts/test_weekly_margin_interest.py`
- [ ] `scripts/test_announcement.py`

### Phase 7: データベーススキーマの削除

#### 7.1 マイグレーションファイルの作成
- [ ] Alembic でマイグレーションファイルを生成
- [ ] upgrade メソッドでテーブル削除を実装
- [ ] downgrade メソッドでテーブル再作成を実装（既存のマイグレーションから）

#### 7.2 マイグレーションの実行
- [ ] マイグレーションを実行してテーブルを削除

### Phase 8: 最終確認とクリーンアップ

#### 8.1 全体動作確認
- [ ] アプリケーションの起動確認
- [ ] 既存 API の動作確認（/api/v1/schedules 、/api/v1/auth）
- [ ] Celery ワーカーの起動確認
- [ ] データベース接続確認

#### 8.2 コードレビュー
- [ ] 不要なインポートが残っていないか確認
- [ ] デッドコードが残っていないか確認
- [ ] エラーログが出力されていないか確認

## 3. 実装時の注意事項

### 3.1 削除順序の厳守
- 必ず外側の層から内側の層へ向かって削除する
- 各フェーズ完了後に動作確認を実施する

### 3.2 Git 操作
- 各フェーズ完了時にコミットを作成
- コミットメッセージは明確に記載

### 3.3 エラー対応
- インポートエラーが発生した場合は、依存関係を再確認
- 削除漏れがないか確認

## 4. 想定作業時間

| フェーズ | 作業内容 | 想定時間 |
|---------|---------|----------|
| Phase 1 | API エンドポイントの無効化 | 10 分 |
| Phase 2 | バックグラウンドタスクの停止 | 15 分 |
| Phase 3 | ビジネスロジックの削除 | 30 分 |
| Phase 4 | ドメイン層の削除 | 15 分 |
| Phase 5 | インフラストラクチャ層の削除 | 15 分 |
| Phase 6 | スクリプトファイルの削除 | 5 分 |
| Phase 7 | データベーススキーマの削除 | 20 分 |
| Phase 8 | 最終確認とクリーンアップ | 10 分 |
| **合計** | | **約 2 時間** |

## 5. ロールバック手順

問題が発生した場合：
1. `git reset --hard` でコードをロールバック
2. `alembic downgrade -1` でデータベースをロールバック
3. エラーログを確認して原因を特定
4. 必要に応じて段階的に再実施

## 6. 完了条件

- [ ] 全 34 ファイルが削除されている
- [ ] 全 8 ファイルのインポートが更新されている
- [ ] 3 つのテーブルがデータベースから削除されている
- [ ] アプリケーションが正常に動作している
- [ ] エラーログが出力されていない
- [ ] テストが正常に実行できる（既存のテスト）