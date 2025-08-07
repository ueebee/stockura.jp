# データ取得機構削除の設計書

## 1. 設計概要

本設計書では、 trades_spec 、 weekly_margin_interest 、 announcement の 3 つのデータ取得機構を安全かつ完全に削除するための設計を記載します。

## 2. アーキテクチャへの影響

### 2.1 クリーンアーキテクチャの各層への影響

現在のシステムはクリーンアーキテクチャに基づいて構築されており、削除は以下の層に影響します：

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (削除対象: API エンドポイント)         │
├─────────────────────────────────────────────────────────┤
│  Application Layer (削除対象: UseCase, DTO)              │
├─────────────────────────────────────────────────────────┤
│  Domain Layer (削除対象: Entity, Repository Interface)   │
├─────────────────────────────────────────────────────────┤
│  Infrastructure Layer (削除対象: DB Model, Client, Task) │
└─────────────────────────────────────────────────────────┘
```

### 2.2 削除による依存関係の解消

削除により、以下の依存関係が解消されます：
- J-Quants API への依存（3 つのエンドポイント）
- Celery による定期実行タスク（3 つのタスク）
- PostgreSQL テーブル（3 つのテーブル）

## 3. 削除設計

### 3.1 削除戦略

**段階的削除アプローチ**を採用し、外側の層から内側の層へ向かって削除を実施します：

1. **Phase 1: API エンドポイントの無効化**
   - API ルーターから該当エンドポイントを削除
   - 外部からのアクセスを遮断

2. **Phase 2: バックグラウンドタスクの停止**
   - Celery タスクの削除
   - タスク設定の削除

3. **Phase 3: ビジネスロジックの削除**
   - UseCase 、 DTO の削除
   - 外部 API クライアントの削除

4. **Phase 4: ドメイン層の削除**
   - Entity 、 Repository Interface の削除

5. **Phase 5: インフラストラクチャ層の削除**
   - Database Model 、 Repository 実装の削除

6. **Phase 6: データベーススキーマの削除**
   - マイグレーションによるテーブル削除

### 3.2 削除対象ファイル一覧

#### 3.2.1 trades_spec 関連（9 ファイル）
```
app/presentation/api/v1/endpoints/trades_spec.py
app/infrastructure/celery/tasks/trades_spec_task_asyncpg.py
app/application/use_cases/fetch_trades_spec.py
app/application/dtos/trades_spec_dto.py
app/infrastructure/jquants/trades_spec_client.py
app/infrastructure/repositories/database/trades_spec_repository_impl.py
app/domain/entities/trades_spec.py
app/domain/repositories/trades_spec_repository.py
app/infrastructure/database/models/trades_spec.py
```

#### 3.2.2 weekly_margin_interest 関連（9 ファイル）
```
app/presentation/api/v1/endpoints/weekly_margin_interest.py
app/infrastructure/celery/tasks/weekly_margin_interest_task_asyncpg.py
app/application/use_cases/fetch_weekly_margin_interest.py
app/application/dtos/weekly_margin_interest_dto.py
app/infrastructure/jquants/weekly_margin_interest_client.py
app/infrastructure/repositories/database/weekly_margin_interest_repository_impl.py
app/domain/entities/weekly_margin_interest.py
app/domain/repositories/weekly_margin_interest_repository.py
app/infrastructure/database/models/weekly_margin_interest.py
```

#### 3.2.3 announcement 関連（10 ファイル）
```
app/presentation/api/v1/endpoints/announcement.py
app/infrastructure/celery/tasks/announcement_task_asyncpg.py
app/application/use_cases/fetch_announcement.py
app/application/dtos/announcement_dto.py
app/application/interfaces/external/announcement_client.py
app/infrastructure/jquants/announcement_client.py
app/infrastructure/repositories/database/announcement_repository_impl.py
app/domain/entities/announcement.py
app/domain/repositories/announcement_repository.py
app/infrastructure/database/models/announcement.py
```

#### 3.2.4 スクリプトファイル（6 ファイル）
```
scripts/test_trades_spec.py
scripts/test_trades_spec_direct.py
scripts/test_celery_trades_spec_debug.py
scripts/debug_trades_spec_api.py
scripts/test_weekly_margin_interest.py
scripts/test_announcement.py
```

### 3.3 修正対象ファイル一覧

#### 3.3.1 インポート削除が必要なファイル
```
app/presentation/api/v1/__init__.py
app/infrastructure/celery/tasks/__init__.py
app/infrastructure/celery/config.py
app/infrastructure/jquants/client_factory.py
app/infrastructure/database/models/__init__.py
app/domain/repositories/__init__.py
app/domain/entities/__init__.py
app/application/dtos/__init__.py
```

### 3.4 データベースマイグレーション設計

#### 3.4.1 削除対象テーブル
- `trades_spec`
- `weekly_margin_interests`
- `announcements`

#### 3.4.2 マイグレーションファイル名
```
remove_trades_spec_weekly_margin_interest_announcement_tables.py
```

#### 3.4.3 マイグレーション内容
```python
"""Remove trades_spec, weekly_margin_interest, and announcement tables

Revision ID: [自動生成]
Revises: dba980847750
Create Date: [自動生成]

"""
from alembic import op

def upgrade():
    # テーブル削除（依存関係を考慮した順序）
    op.drop_table('trades_spec')
    op.drop_table('weekly_margin_interests')
    op.drop_table('announcements')

def downgrade():
    # テーブル再作成のロジック（既存のマイグレーションから復元）
    pass
```

## 4. エラーハンドリング設計

### 4.1 削除時の考慮事項

1. **Celery ワーカーの停止確認**
   - 削除前にワーカーを停止し、実行中のタスクがないことを確認

2. **データベーストランザクション**
   - マイグレーション実行時は自動的にトランザクション管理される

3. **ロールバック戦略**
   - Git によるコードのロールバック
   - Alembic によるデータベースのダウングレード

## 5. テスト戦略

### 5.1 削除後の確認テスト

1. **アプリケーション起動テスト**
   ```bash
   python app/main.py
   ```

2. **既存 API エンドポイントの動作確認**
   - `/api/v1/schedules`
   - `/api/v1/auth`

3. **Celery ワーカーの起動確認**
   ```bash
   celery -A app.infrastructure.celery.app worker --loglevel=info
   ```

4. **マイグレーション実行確認**
   ```bash
   python scripts/db_migrate.py
   ```

### 5.2 削除完了の確認項目

- [ ] 削除対象の 34 ファイルがすべて削除されている
- [ ] 修正対象の 8 ファイルからインポートが削除されている
- [ ] データベースから 3 つのテーブルが削除されている
- [ ] アプリケーションが正常に起動する
- [ ] 既存の API が正常に動作する
- [ ] Celery ワーカーが正常に起動する

## 6. セキュリティ考慮事項

1. **API キーの削除**
   - 削除する機能で使用していた API キーの無効化（J-Quants 側での対応）

2. **データの完全削除**
   - データベーステーブルの削除によりデータも完全に削除される

## 7. 運用への影響

1. **監視設定の更新**
   - 削除したエンドポイントの監視設定を削除

2. **ドキュメントの更新**
   - API 仕様書から該当エンドポイントを削除
   - README から該当機能の説明を削除

## 8. リスクと対策

### 8.1 リスク
1. **依存関係の見落とし**
   - 他の機能が削除対象機能に依存している可能性

2. **実行中のタスク**
   - Celery タスクが実行中の場合のエラー

### 8.2 対策
1. **段階的削除**
   - 外側から内側へ向かって削除することで依存関係エラーを防止

2. **事前確認**
   - Celery ワーカーの停止とタスク完了の確認

## 9. 削除後のアーキテクチャ

削除後は、以下の機能のみが残ります：
- 上場銘柄情報取得機能（listed_info）
- 認証機能（auth）
- スケジュール管理機能（schedule）

これにより、システムはよりシンプルで保守しやすい構成となります。