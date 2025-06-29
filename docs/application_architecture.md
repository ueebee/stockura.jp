# Stockura.jp アプリケーションアーキテクチャ

## 概要

Stockura.jpは、J-Quants APIを使用した日本の上場銘柄管理システムです。FastAPI + PostgreSQL + Redisを基盤とした非同期Webアプリケーションとして設計されています。

## 全体アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   クライアント    │ -> │   FastAPI        │ -> │  PostgreSQL     │
│   (Web/API)     │    │   (Stockura)     │    │  (データベース)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          
                              ▼                          
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Celery         │ -> │    Redis        │
                       │   (バックグラウンド) │    │ (ブローカー/キャッシュ)│
                       └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   J-Quants API   │
                       │   (外部データ源)   │
                       └──────────────────┘
```

## ディレクトリ構造と責務

### プロジェクトルート構造

```
stockura.jp/
├── app/                     # メインアプリケーション
├── alembic/                 # データベースマイグレーション
├── tests/                   # テストコード
├── docs/                    # ドキュメント
├── docker/                  # Docker設定
├── logs/                    # ログファイル
├── requirements.txt         # Python依存関係
├── docker-compose.yml       # 開発環境設定
└── README.md
```

### app/ ディレクトリ詳細

```
app/
├── api/                     # APIレイヤー
│   ├── routes/              # 共通ルート設定
│   └── v1/                  # APIバージョン1
│       └── endpoints/       # エンドポイント実装
├── core/                    # コア機能・設定
├── db/                      # データベース関連
├── models/                  # データモデル (SQLAlchemy)
├── schemas/                 # データスキーマ (Pydantic)
├── services/                # ビジネスロジック
├── tasks/                   # 非同期タスク (Celery)
├── templates/               # HTMLテンプレート
├── config.py                # アプリケーション設定
└── main.py                  # アプリケーションエントリーポイント
```

## 各レイヤーの責務

### 1. APIレイヤー (`app/api/`)

**責務**: HTTPリクエストの受信、バリデーション、レスポンスの返却

#### 構成
- **`routes/`**: 共通のルート設定とミドルウェア
- **`v1/endpoints/`**: バージョン1のAPIエンドポイント実装

#### 現在のエンドポイント
- **`companies.py`**: 企業情報関連API
  - 企業一覧取得、検索、詳細表示
  - マスターデータ（市場・業種）提供
  - 同期管理・履歴確認
- **`daily_quotes.py`**: 日次株価関連API
  - 株価データ取得、期間指定検索
- **`data_sources.py`**: データソース管理API
  - 認証情報管理、接続テスト

#### 実装パターン
```python
@router.get("/companies", response_model=CompanyList)
async def get_companies(
    db: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=1000)
):
    # バリデーション → サービス呼び出し → レスポンス
```

### 2. モデルレイヤー (`app/models/`)

**責務**: データベーススキーマの定義、データ構造の管理

#### 主要モデル
- **`company.py`**: 企業・マスターデータモデル
  - `Company`: 上場企業基本情報
  - `Sector17Master/Sector33Master`: 業種分類マスター
  - `MarketMaster`: 市場区分マスター
  - `CompanySyncHistory`: 同期履歴管理
  
- **`data_source.py`**: データソース管理
  - J-Quants、Yahoo Finance等の外部API管理
  
- **`daily_quote.py`**: 株価データ
  - 日次株価、出来高データ

- **`stock.py`**: 汎用株式データ

#### 設計特徴
- SQLAlchemy 2.0 + Async対応
- GINインデックスによる高速検索
- 外部キー制約による整合性保証
- タイムスタンプ自動管理

```python
class Company(Base):
    __tablename__ = "companies"
    
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # ... GINインデックス、複合インデックス設定
```

### 3. スキーマレイヤー (`app/schemas/`)

**責務**: APIリクエスト/レスポンスの型定義、バリデーション

#### 構成パターン
各モデルに対応したPydanticスキーマ:
- **Base**: 基本フィールド定義
- **Create**: 作成時のリクエストスキーマ
- **Update**: 更新時のリクエストスキーマ  
- **Response**: レスポンススキーマ（IDやタイムスタンプ含む）
- **List**: ページネーション対応リストレスポンス

#### 例: `company.py`
```python
class CompanyBase(BaseModel):
    code: str = Field(..., description="銘柄コード")
    company_name: str = Field(..., description="会社名")

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True
```

### 4. サービスレイヤー (`app/services/`)

**責務**: ビジネスロジックの実装、外部API連携、データ処理

#### 主要サービス

##### データ同期サービス
- **`company_sync_service.py`**: 企業データ同期
  - J-Quants APIからの企業情報取得
  - 差分更新、フル同期の実行
  - 同期履歴の管理

- **`daily_quotes_sync_service.py`**: 株価データ同期
  - 日次株価データの取得・更新
  - 期間指定同期、バッチ処理

##### 外部API連携
- **`jquants_client.py`**: J-Quants API クライアント
  - 認証トークン管理
  - API呼び出し、レート制限対応
  - エラーハンドリング、リトライ処理

- **`data_source_service.py`**: データソース管理
  - 複数データソースの統合管理
  - 認証情報の暗号化保存

##### 認証・セキュリティ
- **`auth/`**: 認証戦略パターン
  - `base.py`: 認証戦略基底クラス
  - `strategies/jquants_strategy.py`: J-Quants認証実装
  - `strategies/yfinance_strategy.py`: Yahoo Finance認証実装

- **`encryption.py`**: 暗号化サービス
  - 認証情報の安全な保存・復号化

- **`token_manager.py`**: トークン管理
  - アクセストークンの自動更新
  - 期限切れトークンのクリーンアップ

#### サービス層設計パターン
```python
class CompanySyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def sync_companies(self, data_source_id: int) -> Dict[str, Any]:
        # 1. データソース取得
        # 2. 外部API呼び出し
        # 3. データベース更新
        # 4. 同期履歴記録
```

### 5. タスクレイヤー (`app/tasks/`)

**責務**: 非同期・定期実行タスクの定義

#### 構成
- **`company_tasks.py`**: 企業データ同期タスク
  - 定期的な企業情報更新
  - バッチ処理の実行

- **`stock_tasks.py`**: 株価データ同期タスク
  - 日次株価データの自動取得
  - 市場時間外の一括処理

- **`sample_tasks.py`**: テスト・サンプルタスク

#### Celeryタスク実装例
```python
@celery_app.task(bind=True)
def sync_company_data(self, data_source_id: int, sync_type: str = "incremental"):
    # 非同期処理をCeleryタスクとして実行
    return asyncio.run(_async_sync_company_data(data_source_id, sync_type))
```

### 6. コアレイヤー (`app/core/`)

**責務**: アプリケーション全体の基盤機能

#### 構成
- **`config.py`**: 設定管理
  - 環境変数の管理
  - データベース、Redis、API設定

- **`celery_app.py`**: Celery設定
  - 非同期タスクキューの設定
  - ワーカー設定、ブローカー設定

### 7. データベースレイヤー (`app/db/`)

**責務**: データベース接続、セッション管理

#### 構成
- **`session.py`**: データベースセッション管理
  - 同期・非同期セッション作成
  - 接続プール設定
  - ヘルスチェック機能

- **`base_class.py`**: モデル基底クラス
- **`base.py`**: SQLAlchemy設定
- **`models/`**: 旧式モデル（移行予定）

#### セッション管理パターン
```python
async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## データフロー

### 1. 同期処理フロー
```
J-Quants API -> JQuantsClient -> CompanySyncService -> Database
                                      ↓
                                 SyncHistory記録
```

### 2. API処理フロー  
```
Client Request -> FastAPI Router -> Service Layer -> Database
                      ↓                    ↓
                 Schema Validation    Business Logic
                      ↓                    ↓
                 Response Schema     Data Transformation
```

### 3. 非同期タスクフロー
```
Scheduler -> Celery -> Task -> Service -> Database
                ↓              ↓
            Redis Queue    Background Process
```

## 設定管理

### 環境変数 (`.env`)
```bash
# データベース
DATABASE_URL=postgresql://postgres:postgres@db:5432/stockura

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# J-Quants認証
JQUANTS_MAIL_ADDRESS=your-email@example.com
JQUANTS_PASSWORD=your-password

# 暗号化
ENCRYPTION_KEY=your-encryption-key
ENCRYPTION_SALT=your-salt
```

### 設定クラス (`app/core/config.py`)
Pydantic BaseSettingsを使用した型安全な設定管理

## セキュリティ考慮事項

### 1. 認証情報の保護
- **暗号化**: 外部API認証情報の暗号化保存
- **環境変数**: 秘匿情報の環境変数管理
- **トークン管理**: アクセストークンの自動ローテーション

### 2. データベースセキュリティ
- **SQLインジェクション対策**: SQLAlchemy ORM使用
- **接続プール**: 適切な接続数制限
- **トランザクション管理**: ACID特性の保証

### 3. API セキュリティ
- **入力バリデーション**: Pydanticによる厳密な型チェック
- **レート制限**: 外部API呼び出しの制限
- **エラーハンドリング**: 情報漏洩防止

## 監視・ログ

### ログ戦略
- **構造化ログ**: JSON形式での出力
- **レベル分け**: INFO、WARNING、ERROR の適切な使い分け
- **トレーサビリティ**: リクエストIDによる追跡

### 監視ポイント  
- **API レスポンス時間**
- **データベース接続数**
- **Celeryタスクキュー状況**
- **外部API呼び出し成功率**

---
