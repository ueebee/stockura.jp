# CLI 層の依存性注入改善設計

## 概要

presentation 層の CLI コマンドにおける依存性注入を改善し、インフラストラクチャ層への直接的な依存を排除します。 API 層と同様の依存性注入パターンを採用することで、アーキテクチャの一貫性を保ちます。

## 設計方針

### 1. 依存性注入パターンの統一
- API 層で採用されているパターンを CLI 層にも適用
- `presentation/dependencies`配下に集約された依存性プロバイダーを使用
- インフラストラクチャ層への直接的な依存を完全に排除

### 2. 段階的な改善
- まず`fetch_listed_info_command.py`から改善を開始
- 次に`migration_command.py`を改善
- 各段階でテストを実行し、動作を確認

### 3. インターフェースの活用
- ドメイン層で定義されたインターフェースのみに依存
- 実装の詳細は依存性注入で解決

## 詳細設計

### 1. CLI 用依存性プロバイダーの作成

#### ファイル: `app/presentation/dependencies/cli.py`

```python
"""CLI commands dependency injection providers."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.auth_repository import AuthRepository
from app.domain.repositories.listed_info_repository import ListedInfoRepository
from app.infrastructure.database.connection import get_async_session_context


# Database session provider
async def get_cli_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for CLI commands."""
    async with get_async_session_context() as session:
        yield session


# Repository providers
async def get_cli_auth_repository() -> AuthRepository:
    """Get auth repository for CLI commands."""
    from app.infrastructure.repositories.external.jquants_auth_repository_impl import JQuantsAuthRepository
    return JQuantsAuthRepository()


async def get_cli_listed_info_repository(
    session: AsyncSession
) -> ListedInfoRepository:
    """Get listed info repository for CLI commands."""
    from app.infrastructure.repositories.database.listed_info_repository_impl import ListedInfoRepositoryImpl
    return ListedInfoRepositoryImpl(session)


# Service providers
async def get_cli_jquants_client(credentials):
    """Get J-Quants client for CLI commands."""
    from app.infrastructure.external_services.jquants.base_client import JQuantsBaseClient
    from app.infrastructure.external_services.jquants.listed_info_client import JQuantsListedInfoClient
    
    base_client = JQuantsBaseClient(credentials)
    return JQuantsListedInfoClient(base_client)
```

### 2. fetch_listed_info_command.py のリファクタリング

#### 主な変更点：
1. インフラストラクチャ層への直接インポートを削除
2. 依存性注入を使用してサービスやリポジトリを取得
3. 認証処理を分離し、再利用可能にする

#### 新しい構造：
```python
# インポートの変更
from app.presentation.dependencies.cli import (
    get_cli_session,
    get_cli_auth_repository,
    get_cli_listed_info_repository,
    get_cli_jquants_client,
)

# 認証処理の分離
async def authenticate_jquants(email: str, password: str) -> JQuantsCredentials:
    """J-Quants API の認証を行う"""
    auth_repo = await get_cli_auth_repository()
    # ... 認証処理 ...
    return credentials

# メイン処理
async def _fetch_listed_info_async(...):
    # 認証
    credentials = await authenticate_jquants(jquants_email, jquants_password)
    
    # 依存性の取得
    async for session in get_cli_session():
        repository = await get_cli_listed_info_repository(session)
        jquants_client = await get_cli_jquants_client(credentials)
        
        # ユースケースの実行
        use_case = FetchListedInfoUseCase(
            jquants_client=jquants_client,
            listed_info_repository=repository,
            logger=logger,
        )
        # ... 実行処理 ...
```

### 3. migration_command.py のリファクタリング

#### アプローチ：
- マイグレーション機能は本質的にインフラストラクチャ層の機能
- 最小限の変更で依存性を改善
- マイグレーションサービスのインターフェースを作成

#### ファイル: `app/presentation/dependencies/migration.py`

```python
"""Migration service dependency injection."""
from typing import Protocol


class MigrationService(Protocol):
    """Migration service interface."""
    
    async def upgrade_database(self, revision: str) -> None: ...
    async def downgrade_database(self, revision: str) -> None: ...
    async def create_revision(self, message: str, autogenerate: bool) -> None: ...
    def get_current_revision(self) -> Optional[str]: ...
    def show_history(self) -> None: ...
    async def check_pending_migrations(self) -> bool: ...
    async def init_database(self) -> None: ...
    async def reset_database(self) -> None: ...


def get_migration_service() -> MigrationService:
    """Get migration service."""
    from app.infrastructure.database.migration import MigrationServiceImpl
    return MigrationServiceImpl()
```

### 4. 共通処理の整理

#### エラーハンドリング
- CLI コマンド用の共通エラーハンドリング関数を作成
- 一貫したエラーメッセージフォーマット

#### 認証処理
- J-Quants 認証処理を共通化
- 他の CLI コマンドからも再利用可能

## 実装手順

1. **Phase 1: 依存性プロバイダーの作成**
   - `app/presentation/dependencies/cli.py`を作成
   - 基本的な依存性注入関数を実装

2. **Phase 2: fetch_listed_info_command のリファクタリング**
   - インフラストラクチャ層への直接インポートを削除
   - 依存性注入を使用するように変更
   - テストを実行して動作確認

3. **Phase 3: migration_command のリファクタリング**
   - MigrationService インターフェースの実装
   - 依存性注入を使用するように変更
   - テストを実行して動作確認

4. **Phase 4: 最終確認**
   - 全体のテストを実行
   - CLI コマンドの動作確認
   - ドキュメントの更新

## テスト戦略

1. **単体テスト**
   - 依存性プロバイダーのテスト
   - モックを使用した CLI コマンドのテスト

2. **統合テスト**
   - 実際のデータベースを使用したテスト
   - CLI コマンドの実行テスト

3. **動作確認**
   - 各 CLI コマンドを手動で実行
   - エラーハンドリングの確認

## リスクと対策

1. **リスク: 既存の動作への影響**
   - 対策: 段階的な実装と各段階でのテスト実行

2. **リスク: 依存性の循環参照**
   - 対策: 明確な層の分離と依存関係の管理

3. **リスク: パフォーマンスへの影響**
   - 対策: 必要最小限の変更に留める