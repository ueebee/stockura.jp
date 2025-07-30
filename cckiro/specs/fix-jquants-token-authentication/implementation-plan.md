# J-Quants API トークン認証自動化の実装計画

## 実装手順

### Phase 1: 認証済みクライアントファクトリーの実装（優先度：高）

#### 1.1 client_factory.py の作成
**ファイル**: `app/infrastructure/jquants/client_factory.py`（新規）

**作業内容**:
1. `create_authenticated_client()`関数の実装
2. 環境変数からの認証情報取得
3. AuthUseCase を使った認証フロー
4. エラーハンドリング

**推定作業時間**: 30 分

### Phase 2: Celery タスクの修正（優先度：高）

#### 2.1 listed_info_task_asyncpg.py の修正
**ファイル**: `app/infrastructure/celery/tasks/listed_info_task_asyncpg.py`

**変更内容**:
1. `client_factory`のインポート追加
2. クライアント初期化部分を置き換え（2 行）
3. エラーハンドリングの追加

**推定作業時間**: 15 分

### Phase 3: Redis リポジトリの確認と調整（優先度：中）

#### 3.1 Redis 認証リポジトリの動作確認
**ファイル**: `app/infrastructure/redis/auth_repository_impl.py`

**確認内容**:
1. トークンの保存・取得が正しく動作するか
2. TTL 設定が適切か
3. 必要に応じて微調整

**推定作業時間**: 20 分

### Phase 4: テストとドキュメント（優先度：中）

#### 4.1 手動テスト
1. Docker 環境での動作確認
2. 認証フローの確認
3. タスク実行ログの確認

#### 4.2 進捗ドキュメントの作成
**ファイル**: `cckiro/specs/fix-jquants-token-authentication/progress.md`

**推定作業時間**: 30 分

## 実装の詳細

### 1. client_factory.py の実装詳細

```python
"""J-Quants API 認証済みクライアントファクトリー"""
from typing import Tuple

from app.application.use_cases.auth_use_case import AuthUseCase
from app.core.config import get_settings
from app.domain.exceptions.jquants_exceptions import AuthenticationError
from app.infrastructure.jquants.auth_repository_impl import JQuantsAuthRepository
from app.infrastructure.jquants.base_client import JQuantsBaseClient
from app.infrastructure.jquants.listed_info_client import JQuantsListedInfoClient
from app.infrastructure.redis.auth_repository_impl import RedisAuthRepository
from app.infrastructure.redis.redis_client import get_redis_client
from app.core.logger import get_logger

logger = get_logger(__name__)


async def create_authenticated_client() -> Tuple[JQuantsBaseClient, JQuantsListedInfoClient]:
    """
    環境変数から認証情報を取得し、認証済みのクライアントを生成
    
    Returns:
        Tuple[JQuantsBaseClient, JQuantsListedInfoClient]: 認証済みクライアント
        
    Raises:
        AuthenticationError: 認証に失敗した場合
    """
    try:
        # 環境変数から認証情報を取得
        settings = get_settings()
        
        if not settings.jquants_email or not settings.jquants_password:
            raise AuthenticationError(
                "J-Quants 認証情報が設定されていません。"
                "JQUANTS_EMAIL と JQUANTS_PASSWORD を環境変数に設定してください。"
            )
        
        # 認証リポジトリを初期化（Redis が利用可能なら Redis 、そうでなければファイル）
        try:
            redis_client = await get_redis_client()
            auth_repo = RedisAuthRepository(redis_client)
            logger.info("Redis 認証リポジトリを使用します")
        except Exception as e:
            logger.warning(f"Redis 接続エラー: {e}. ファイルベースの認証リポジトリを使用します")
            auth_repo = JQuantsAuthRepository(storage_path=".jquants_auth.json")
        
        # 認証ユースケースを初期化
        auth_use_case = AuthUseCase(auth_repo)
        
        # 認証実行（キャッシュがあれば利用）
        logger.info(f"J-Quants 認証を開始します: {settings.jquants_email}")
        credentials = await auth_use_case.authenticate(
            email=settings.jquants_email,
            password=settings.jquants_password
        )
        
        # トークンの有効性確認と必要に応じて更新
        valid_credentials = await auth_use_case.ensure_valid_token(credentials)
        logger.info("J-Quants 認証が完了しました")
        
        # 認証済みクライアントを生成
        base_client = JQuantsBaseClient(credentials=valid_credentials)
        listed_info_client = JQuantsListedInfoClient(base_client)
        
        return base_client, listed_info_client
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"クライアント初期化エラー: {e}")
        raise AuthenticationError(f"J-Quants クライアントの初期化に失敗しました: {str(e)}")
```

### 2. タスクファイルの修正箇所

```python
# 修正前（126-128 行目）
base_client = JQuantsBaseClient()
jquants_client = JQuantsListedInfoClient(base_client)

# 修正後
from app.infrastructure.jquants.client_factory import create_authenticated_client

# ... 中略 ...

# 認証済みクライアントを取得
base_client, jquants_client = await create_authenticated_client()
```

## リスクと対策

1. **リスク**: Redis 接続エラー
   - **対策**: ファイルベースの認証リポジトリにフォールバック

2. **リスク**: 認証情報の不足
   - **対策**: 明確なエラーメッセージで環境変数の設定を促す

3. **リスク**: トークン更新の失敗
   - **対策**: 自動的に再認証を試みる

## 成功基準の確認方法

1. **タスク実行の成功**
   ```bash
   docker-compose logs celery-worker | grep "Task completed"
   ```

2. **認証ログの確認**
   ```bash
   docker-compose logs celery-worker | grep "J-Quants 認証"
   ```

3. **エラーがないことの確認**
   ```bash
   docker exec stockura-postgres psql -U stockura -d stockura \
     -c "SELECT * FROM task_execution_logs WHERE status = 'failed' ORDER BY started_at DESC LIMIT 5;"
   ```

## 総作業時間見積もり

- Phase 1: 30 分
- Phase 2: 15 分  
- Phase 3: 20 分
- Phase 4: 30 分
- **合計**: 約 1 時間 35 分