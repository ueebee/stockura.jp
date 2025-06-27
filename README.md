# Stockura.jp - 上場銘柄一覧管理システム

## 概要

J-Quants APIを使用して日本の上場銘柄情報を取得・管理するWebアプリケーションです。効率的な検索、フィルタリング、リアルタイム同期機能を提供します。

## 主要機能

### ✅ 実装済み機能

#### データベース基盤
- **企業情報管理**: 上場企業の基本情報・分類情報の保存
- **マスターデータ管理**: 市場区分、17業種・33業種分類の管理
- **高速検索**: GINインデックスによる企業名部分一致検索
- **データ整合性**: 外部キー制約による参照整合性保証

#### 認証・トークン管理
- **J-Quants認証**: リフレッシュトークン・IDトークンの自動管理
- **暗号化**: 認証情報の安全な保存・復号化
- **自動更新**: トークンの期限切れ前自動リフレッシュ

### 🔄 開発中機能

#### API機能
- **企業情報API**: 一覧取得、検索、詳細表示
- **マスターデータAPI**: 市場・業種情報の提供
- **同期管理API**: J-Quants APIとの同期制御

#### バックグラウンド処理
- **定期同期**: 営業時間後の自動データ更新
- **差分更新**: 効率的な増分データ取得
- **エラー処理**: 障害時の自動復旧・アラート

## 技術スタック

### バックエンド
- **Python 3.12**: プログラミング言語
- **FastAPI**: 高性能WebフレームワーK
- **SQLAlchemy**: 非同期ORM
- **Alembic**: データベースマイグレーション
- **Celery**: 非同期タスク処理
- **Pydantic**: データ検証・シリアライゼーション

### データベース・キャッシュ
- **PostgreSQL 17**: メインデータベース
- **Redis 7.2**: キャッシュ・メッセージブローカー
- **pg_trgm**: 全文検索・部分一致検索拡張

### インフラ・ツール
- **Docker Compose**: 開発環境
- **Flower**: Celery監視
- **Prometheus**: メトリクス収集（予定）
- **Grafana**: 監視ダッシュボード（予定）

## データ設計

### データベーススキーマ

#### 企業情報 (companies)
```sql
- code: 銘柄コード (例: "7203")
- company_name: 企業名 (例: "トヨタ自動車株式会社")  
- company_name_english: 企業名英語 (例: "Toyota Motor Corporation")
- market_code: 市場区分 (例: "0111" = プライム)
- sector17_code: 17業種コード (例: "6" = 自動車・輸送機)
- sector33_code: 33業種コード (例: "3700" = 輸送用機器)
- reference_date: 情報基準日
- is_active: アクティブフラグ
```

#### マスターデータ
- **market_masters**: 市場区分 (プライム、スタンダード、グロース等)
- **sector17_masters**: 17業種分類 (食品、エネルギー、建設等)
- **sector33_masters**: 33業種分類 (詳細業種分類)

### 検索最適化
- **GINインデックス**: 企業名の高速部分一致検索
- **複合インデックス**: 市場×業種、アクティブ×分類の効率的検索
- **外部キー制約**: データ整合性保証

## セットアップ

### 前提条件
- Docker Desktop
- Git

### 開発環境構築

1. **リポジトリクローン**
```bash
git clone [repository-url]
cd stockura.jp
```

2. **環境変数設定**
```bash
cp .env.example .env
# .env ファイルを編集してJ-Quants認証情報を設定
```

3. **Docker環境起動**
```bash
docker compose up -d
```

4. **データベースマイグレーション**
```bash
docker compose exec web alembic upgrade head
```

5. **アプリケーション確認**
- API: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs
- Flower (Celery監視): http://localhost:5555

### 環境変数設定

```env
# データベース
DATABASE_URL=postgresql://postgres:postgres@db:5432/stockura

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# 暗号化設定
ENCRYPTION_KEY=your-super-secure-encryption-key-here-change-in-production
ENCRYPTION_SALT=your-super-secure-salt-here-change-in-production
ENCRYPTION_ITERATIONS=100000
ENCRYPTION_KEY_LENGTH=32
ENCRYPTION_ALGORITHM=SHA256

# J-Quants認証情報 (.envに設定)
JQUANTS_MAIL_ADDRESS=your-email@example.com
JQUANTS_PASSWORD=your-password
```

## API仕様

### 認証
```http
# APIキー認証（予定）
X-API-Key: your-api-key
```

### エンドポイント（予定実装）

#### 企業情報
```http
# 企業一覧取得
GET /api/v1/companies?market_code=0111&sector17_code=6&limit=100

# 特定企業取得  
GET /api/v1/companies/7203

# 企業検索
GET /api/v1/companies/search?q=トヨタ&limit=50
```

#### マスターデータ
```http
# 市場一覧
GET /api/v1/companies/markets

# 業種一覧
GET /api/v1/companies/sectors?type=17
```

#### データ同期
```http
# 同期実行
POST /api/v1/companies/sync
Content-Type: application/json
{
    "date": "2025-06-26",
    "force_update": false
}

# 同期状態確認
GET /api/v1/companies/sync/status
```

## 開発・運用

### データベース操作

```bash
# マイグレーション作成
docker compose exec web alembic revision --autogenerate -m "description"

# マイグレーション適用
docker compose exec web alembic upgrade head

# マイグレーション履歴
docker compose exec web alembic history

# データベース接続
docker compose exec db psql -U postgres -d stockura
```

### テスト実行

```bash
# 単体テスト
docker compose exec web pytest tests/unit/

# 統合テスト  
docker compose exec web pytest tests/integration/

# 全テスト
docker compose exec web pytest
```

### ログ確認

```bash
# アプリケーションログ
docker compose logs web

# ワーカーログ
docker compose logs worker

# データベースログ
docker compose logs db
```

## プロジェクト構造

```
stockura.jp/
├── app/                          # アプリケーション
│   ├── api/                      # API エンドポイント
│   │   └── v1/
│   │       └── endpoints/
│   ├── models/                   # データモデル
│   │   ├── company.py           # 企業関連モデル
│   │   └── data_source.py       # データソースモデル
│   ├── services/                # ビジネスロジック
│   │   ├── token_manager.py     # トークン管理
│   │   └── data_source.py       # データソース管理
│   ├── db/                      # データベース設定
│   └── core/                    # コア機能
├── alembic/                     # データベースマイグレーション
│   └── versions/
├── tests/                       # テストコード
│   ├── unit/
│   └── integration/
├── docs/                        # ドキュメント
│   ├── database_schema_design.md
│   ├── migration_history.md
│   ├── technical_architecture.md
│   └── listed_companies_implementation_design.md
├── docker/                      # Docker設定
│   └── postgres/
│       └── init.sql
├── docker-compose.yml           # Docker Compose設定
└── README.md
```

## ドキュメント

### 設計ドキュメント
- [📊 データベーススキーマ設計](./docs/database_schema_design.md)
- [🏗️ 技術アーキテクチャ](./docs/technical_architecture.md)
- [📈 実装進捗・設計](./docs/listed_companies_implementation_design.md)
- [📝 マイグレーション履歴](./docs/migration_history.md)

### 運用ドキュメント
- [🔧 手動テスト結果](./docs/manual_testing_results.md)

## 貢献

### 開発フロー
1. イシューの作成・確認
2. フィーチャーブランチの作成
3. 実装・テスト
4. プルリクエスト作成
5. コードレビュー・マージ

### コーディング規約
- **Python**: PEP 8準拠
- **コミットメッセージ**: Conventional Commits
- **ドキュメント**: Markdown形式

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## お問い合わせ

プロジェクトに関する質問や提案は、GitHubのIssueまでお願いします。

---

**Stockura.jp** - Efficient Japanese Listed Company Management System