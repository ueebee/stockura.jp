# J-Quants API トークン認証自動化の設計

## 概要

既存の認証機能を活用し、 Celery タスク実行時に自動的に J-Quants API の認証を行う仕組みを実装します。

## 設計方針

### 1. 最小限の変更で実現

既存のコンポーネントを最大限活用：
- `JQuantsAuthRepository`：トークン取得・更新
- `AuthUseCase`：認証フロー管理
- `get_settings()`：環境変数の取得

### 2. 認証済みクライアントの自動生成

タスク実行時に認証済みの API クライアントを自動生成する関数を追加。

## アーキテクチャ

```
┌─────────────────┐
│ Celery Task     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ create_authenticated_   │ ← 新規追加
│ client()                │
└────────┬────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────────┐
│Settings │ │AuthUseCase   │
│(.env)   │ │              │
└─────────┘ └──────┬───────┘
                   │
                   ▼
         ┌─────────────────┐
         │AuthRepository   │
         │(Redis/File)     │
         └─────────────────┘
```

## 詳細設計

### 1. 認証済みクライアント生成ファクトリー

**ファイル**: `app/infrastructure/jquants/client_factory.py`（新規）

```python
async def create_authenticated_client() -> Tuple[JQuantsBaseClient, JQuantsListedInfoClient]:
    """
    環境変数から認証情報を取得し、認証済みのクライアントを生成
    
    Returns:
        Tuple[JQuantsBaseClient, JQuantsListedInfoClient]: 認証済みクライアント
    """
    # 1. 環境変数から認証情報を取得
    settings = get_settings()
    
    # 2. 認証リポジトリとユースケースを初期化
    auth_repo = RedisAuthRepository() or JQuantsAuthRepository()
    auth_use_case = AuthUseCase(auth_repo)
    
    # 3. 認証実行（キャッシュがあれば利用）
    credentials = await auth_use_case.authenticate(
        email=settings.jquants_email,
        password=settings.jquants_password
    )
    
    # 4. トークンの有効性確認と必要に応じて更新
    valid_credentials = await auth_use_case.ensure_valid_token(credentials)
    
    # 5. 認証済みクライアントを生成
    base_client = JQuantsBaseClient(credentials=valid_credentials)
    listed_info_client = JQuantsListedInfoClient(base_client)
    
    return base_client, listed_info_client
```

### 2. Celery タスクの修正

**ファイル**: `app/infrastructure/celery/tasks/listed_info_task_asyncpg.py`

変更箇所：
```python
# Before:
base_client = JQuantsBaseClient()
jquants_client = JQuantsListedInfoClient(base_client)

# After:
from app.infrastructure.jquants.client_factory import create_authenticated_client
base_client, jquants_client = await create_authenticated_client()
```

### 3. Redis 認証リポジトリの活用

**ファイル**: `app/infrastructure/redis/auth_repository_impl.py`（既存）

- トークンを Redis にキャッシュ
- TTL: 23 時間（トークン有効期限 24 時間より少し短く）
- キー形式: `jquants:auth:{email}`

### 4. エラーハンドリングの強化

```python
try:
    base_client, jquants_client = await create_authenticated_client()
except AuthenticationError as e:
    logger.error(f"J-Quants 認証エラー: {e}")
    raise
except Exception as e:
    logger.error(f"クライアント初期化エラー: {e}")
    raise
```

## 実装の流れ

1. **初回実行時**
   - .env から認証情報を読み込み
   - J-Quants API で refresh_token を取得
   - refresh_token を使って id_token を取得
   - Redis にトークンを保存（TTL: 23 時間）

2. **2 回目以降の実行時**
   - Redis からトークンを取得
   - トークンの有効性を確認
   - 有効ならそのまま使用
   - 無効なら自動的に再認証

3. **エラー時**
   - トークンエラーの場合は自動再認証
   - ネットワークエラーの場合はリトライ

## テスト戦略

1. **単体テスト**
   - `create_authenticated_client`関数のテスト
   - モックを使った各種エラーケースのテスト

2. **統合テスト**
   - Docker 環境での実際の認証フロー確認
   - トークン期限切れ時の自動更新確認

3. **手動テスト**
   - Celery タスクの実行確認
   - task_execution_logs でエラーがないことを確認

## 利点

1. **既存コードへの影響が最小限**
   - タスクファイルの変更は 2 行のみ
   - 既存の認証機能を再利用

2. **他のタスクでも利用可能**
   - `create_authenticated_client`関数を呼ぶだけ

3. **パフォーマンス向上**
   - Redis キャッシュによる高速化
   - 不要な認証リクエストを削減

## セキュリティ考慮事項

1. パスワードは環境変数でのみ管理
2. トークンは Redis に暗号化して保存（オプション）
3. ログにはトークンを出力しない