# Alembic マイグレーションシステム設計書

## 1. 概要
本設計書では、既存の SQL ファイルベースのマイグレーションシステムを Alembic に置き換えるための詳細設計を記述する。

## 2. アーキテクチャ設計

### 2.1 ディレクトリ構造
```
stockura/
├── alembic/
│   ├── versions/        # マイグレーションファイル格納
│   ├── env.py          # Alembic 環境設定（非同期対応）
│   ├── script.py.mako  # マイグレーションテンプレート
│   └── README
├── alembic.ini         # Alembic 設定ファイル
└── app/
    └── infrastructure/
        └── database/
            ├── migration.py  # Alembic ヘルパー関数
            └── models/      # 既存の SQLAlchemy モデル
```

### 2.2 非同期対応設計
Alembic は標準では同期処理のみサポートしているため、非同期対応のカスタマイズが必要：

1. **env.py のカスタマイズ**
   - asyncio を使用した非同期実行環境の構築
   - 既存の `get_engine()` との連携
   - run_migrations_online() の非同期化

2. **マイグレーション実行方法**
   - コマンドライン: `alembic upgrade head`
   - プログラム内: `app.infrastructure.database.migration` のヘルパー関数

### 2.3 設定管理

#### alembic.ini
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname  # env.py で上書き

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 120

[loggers]
[handlers]
[formatters]
```

#### env.py での設定
- `app.core.config.settings` から DATABASE_URL を取得
- 非同期エンジンの設定を利用
- autogenerate のためのメタデータ設定

## 3. 既存システムとの統合

### 3.1 モデル認識
```python
# env.py での実装
from app.infrastructure.database.connection import Base
from app.infrastructure.database.models import *  # 全モデルをインポート

target_metadata = Base.metadata
```

### 3.2 初期マイグレーション
既存のテーブル定義を初期マイグレーションとして作成：

1. 既存の DB スキーマをダンプ（開発環境）
2. Alembic で初期マイグレーションを生成
3. 既存の SQL マイグレーションとの整合性確認

### 3.3 アプリケーション統合
```python
# app/infrastructure/database/migration.py
import asyncio
from alembic import command
from alembic.config import Config

async def run_migrations():
    """非同期でマイグレーションを実行"""
    def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()
    
    async with engine.begin() as conn:
        await conn.run_sync(do_run_migrations)

async def create_migration(message: str):
    """新しいマイグレーションを作成"""
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, autogenerate=True, message=message)
```

## 4. マイグレーション戦略

### 4.1 初期セットアップ手順
1. Alembic を初期化（`alembic init`）
2. env.py を非同期対応に改修
3. 既存のテーブルを認識させる
4. 初期マイグレーションを生成

### 4.2 既存 SQL マイグレーションの置き換え
- 001_create_listed_info_table.sql → 初期マイグレーション
- 002/003_alter_listed_info_code_length.sql → 初期マイグレーションに統合

### 4.3 開発フロー
1. モデル変更
2. `alembic revision --autogenerate -m "message"`
3. 生成されたマイグレーションファイルの確認・修正
4. `alembic upgrade head`

## 5. コマンドラインインターフェース

### 5.1 基本コマンド
```bash
# マイグレーション状態確認
alembic current

# マイグレーション履歴
alembic history

# マイグレーション適用
alembic upgrade head

# ロールバック
alembic downgrade -1

# 新規マイグレーション作成
alembic revision --autogenerate -m "Add new column"
```

### 5.2 カスタム CLI コマンド
```python
# app/presentation/cli/commands/migration_command.py
import click
from app.infrastructure.database.migration import run_migrations

@click.command()
@click.option('--rollback', is_flag=True, help='Rollback last migration')
async def migrate(rollback):
    """データベースマイグレーションを実行"""
    if rollback:
        await rollback_migration()
    else:
        await run_migrations()
```

## 6. エラーハンドリング

### 6.1 マイグレーション失敗時
- トランザクション内で実行されるため自動ロールバック
- エラーログの記録
- 失敗したマイグレーションの特定

### 6.2 競合解決
- 複数の開発者が同時にマイグレーションを作成した場合
- バージョン番号の調整
- マージ時の対応手順

## 7. テスト戦略

### 7.1 マイグレーションテスト
```python
# tests/integration/test_migrations.py
async def test_migration_up_and_down():
    """マイグレーションの適用とロールバックのテスト"""
    # テスト用 DB でマイグレーション実行
    # スキーマの検証
    # ロールバックの検証
```

### 7.2 CI/CD 統合
- GitHub Actions でのマイグレーションチェック
- スキーマの差分検出
- 自動テストでのマイグレーション実行

## 8. セキュリティ考慮事項
- alembic.ini にデータベース接続情報を直接記載しない
- 環境変数からの読み込み
- マイグレーションファイルのレビュープロセス

## 9. 今後の拡張性
- マルチテナント対応
- ゼロダウンタイムマイグレーション
- データマイグレーションのサポート