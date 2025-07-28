# Alembic マイグレーションシステム実装計画

## 実装タスクリスト

### フェーズ 1: 環境準備（15 分）
1. **依存関係の追加**
   - [ ] requirements.txt に alembic を追加
   - [ ] requirements-dev.txt に必要なツールを追加（もしあれば）
   - [ ] pip install -r requirements.txt で依存関係をインストール

### フェーズ 2: Alembic 初期化（30 分）
2. **Alembic 基本設定**
   - [ ] `alembic init alembic` で Alembic を初期化
   - [ ] 生成された alembic.ini を編集
   - [ ] alembic/env.py を非同期対応に改修
   - [ ] alembic/script.py.mako をプロジェクト標準に合わせて調整

### フェーズ 3: 既存システムとの統合（45 分）
3. **データベース接続設定**
   - [ ] env.py で app.core.config から DB 設定を読み込むよう実装
   - [ ] 非同期エンジンサポートの実装
   - [ ] Base メタデータの認識設定

4. **ヘルパー関数の実装**
   - [ ] app/infrastructure/database/migration.py を作成
   - [ ] 非同期マイグレーション実行関数を実装
   - [ ] CLI コマンド用のラッパー関数を実装

### フェーズ 4: 初期マイグレーション作成（30 分）
5. **既存テーブルの移行**
   - [ ] 既存のモデル（ListedInfoModel 等）を確認
   - [ ] `alembic revision --autogenerate -m "Initial migration"` で初期マイグレーション生成
   - [ ] 生成されたマイグレーションファイルの確認・修正
   - [ ] テスト環境でマイグレーション実行テスト

### フェーズ 5: CLI コマンド実装（20 分）
6. **CLI インターフェース**
   - [ ] app/presentation/cli/commands/migration_command.py を作成
   - [ ] migrate コマンドの実装
   - [ ] コマンドのテスト

### フェーズ 6: クリーンアップと文書化（20 分）
7. **既存ファイルの整理**
   - [ ] sql/migrations/ ディレクトリを削除またはアーカイブ
   - [ ] 使用方法のドキュメント作成
   - [ ] CLAUDE.md に Alembic 関連の情報を追加

### フェーズ 7: テストと検証（30 分）
8. **動作確認**
   - [ ] 開発環境でのマイグレーション実行
   - [ ] ロールバックテスト
   - [ ] 新規マイグレーション作成テスト
   - [ ] GitHub Actions でのテスト（もし必要なら）

## 実装詳細

### 1. requirements.txt への追加
```txt
alembic==1.13.1
```

### 2. alembic.ini の設定例
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
# sqlalchemy.url は env.py で動的に設定

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 120

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name) s] %(message) s
datefmt = %H:%M:%S
```

### 3. env.py の実装概要
```python
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# プロジェクトルートを Python パスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.infrastructure.database.connection import Base

# すべてのモデルをインポート（重要！）
from app.infrastructure.database.models import *

config = context.config
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """オフラインモードでのマイグレーション実行"""
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """非同期モードでのマイグレーション実行"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """オンラインモードでのマイグレーション実行"""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 4. migration.py の実装概要
```python
import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

def get_alembic_config() -> Config:
    """Alembic 設定を取得"""
    root_path = Path(__file__).resolve().parent.parent.parent.parent
    alembic_ini_path = root_path / "alembic.ini"
    return Config(str(alembic_ini_path))

async def upgrade_database(revision: str = "head") -> None:
    """データベースをアップグレード"""
    def run_upgrade():
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, revision)
    
    await asyncio.get_event_loop().run_in_executor(None, run_upgrade)

async def downgrade_database(revision: str = "-1") -> None:
    """データベースをダウングレード"""
    def run_downgrade():
        alembic_cfg = get_alembic_config()
        command.downgrade(alembic_cfg, revision)
    
    await asyncio.get_event_loop().run_in_executor(None, run_downgrade)

async def create_revision(message: str, autogenerate: bool = True) -> None:
    """新しいリビジョンを作成"""
    def run_revision():
        alembic_cfg = get_alembic_config()
        command.revision(alembic_cfg, message=message, autogenerate=autogenerate)
    
    await asyncio.get_event_loop().run_in_executor(None, run_revision)

def get_current_revision() -> str:
    """現在のリビジョンを取得"""
    alembic_cfg = get_alembic_config()
    # 実装は Alembic の API に依存
    return ""

def show_history() -> None:
    """マイグレーション履歴を表示"""
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg)
```

## 実行順序と依存関係

1. **必須**: フェーズ 1-3 は順番に実行
2. **並行可能**: フェーズ 4 とフェーズ 5 は並行して作業可能
3. **最終段階**: フェーズ 6-7 は他のすべてが完了後に実行

## リスクと対処法

### リスク 1: 既存データの損失
- **対処**: 開発環境のみで実行、本番環境は対象外

### リスク 2: 非同期実装の複雑性
- **対処**: 十分なテストと既存の非同期パターンに従う

### リスク 3: モデル認識の失敗
- **対処**: env.py で明示的にすべてのモデルをインポート

## 成功基準

1. `alembic upgrade head` が正常に実行できる
2. `alembic downgrade -1` でロールバックできる
3. モデル変更時に `alembic revision --autogenerate` で差分検出できる
4. テスト環境での動作確認が完了している
5. ドキュメントが更新されている