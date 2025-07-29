# Stockura - 株価データ分析プラットフォーム

## 概要
Stockura は、 J-Quants と yFinance から取得した株価データを統合的に管理・分析するためのプラットフォームです。日本株式市場のデータを中心に、グローバルな市場データも含めた包括的な分析環境を提供します。

## 主な機能
- **データ収集**: J-Quants API および yFinance からの自動データ取得
- **データ統合**: 異なるソースからのデータを一元管理
- **分析ツール**: 各種テクニカル指標の計算と可視化
- **API 提供**: FastAPI による RESTful API の提供
- **データストレージ**: PostgreSQL と Redis を使用した効率的なデータ管理

## 技術スタック
- **バックエンド**: Python, FastAPI
- **データベース**: PostgreSQL (時系列データ), Redis (キャッシュ)
- **JobQueue**: Celery(Beat)
- **アーキテクチャ**: クリーンアーキテクチャ
- **データソース**:
  - J-Quants API (日本株データ)
  - yFinance (日本株データ,グローバル市場データ)

## プロジェクト構造
```
stockura/
├── app/                    # アプリケーションコード
│   ├── api/               # API エンドポイント
│   ├── core/              # コア設定・共通処理
│   ├── domain/            # ドメインモデル
│   ├── infrastructure/    # 外部サービス連携
│   ├── services/          # ビジネスロジック
│   └── repositories/      # データアクセス層
├── tests/                 # テストコード
├── scripts/               # ユーティリティスクリプト
└── docs/                  # ドキュメント

```

## セットアップ

### 前提条件
- Docker および Docker Compose がインストールされていること
- Git がインストールされていること
- ローカル開発の場合は Python 3.11+ がインストールされていること

### Docker 環境でのセットアップ（推奨）

1. リポジトリのクローン
```bash
git clone https://github.com/ueebee/stockura.git
cd stockura
```

2. 環境変数の設定
```bash
cp .env.docker .env
# .env ファイルを編集して必要な設定（J-Quants API キーなど）を追加
```

3. Docker 環境の起動
```bash
# 開発環境の起動
make up

# または直接スクリプトを実行
./scripts/docker/start-dev.sh
```

4. データベースのマイグレーション（初回のみ）
```bash
make migrate
```

### ローカル開発環境でのセットアップ

1. Python 仮想環境の作成
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 依存関係のインストール
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. 環境変数の設定
```bash
cp .env.example .env
# .env ファイルを編集
```

4. PostgreSQL と Redis の起動（Docker を使用）
```bash
docker-compose up -d postgres redis
```

5. データベースマイグレーション
```bash
python scripts/db_migrate.py
```

6. アプリケーションの起動
```bash
uvicorn app.main:app --reload
```

## 使用方法

### 開発環境

#### サービスの起動・停止
```bash
# 開発環境の起動
make up

# ログの確認
make logs

# サービスの停止
make down
```

#### テストの実行
```bash
# Docker でテストを実行
make test

# ローカルでテストを実行
pytest
```

#### データベース操作
```bash
# マイグレーションの実行
make migrate

# PostgreSQL に接続
make shell-db

# Redis に接続
make redis-cli
```

### API アクセス

- **API ドキュメント**: http://localhost:8000/docs
- **Flower (Celery 監視)**: http://localhost:5555

### 本番環境

```bash
# 本番環境用のイメージビルド
make prod-build

# 本番環境の起動
make prod-up

# 本番環境のログ確認
make prod-logs
```

### よく使うコマンド

| コマンド | 説明 |
|---------|------|
| `make help` | 利用可能なコマンド一覧を表示 |
| `make build` | Docker イメージをビルド |
| `make shell` | アプリケーションコンテナのシェルに接続 |
| `make clean` | コンテナとボリュームをクリーンアップ |

## ライセンス
（今後追加予定）
