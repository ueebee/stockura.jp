# Alembic マイグレーションシステム導入要件

## 概要
現在の SQL ファイルベースのマイグレーションシステムを Alembic に置き換え、より体系的なデータベースマイグレーション管理を実現する。

## 要件

### 1. 基本要件
- Alembic を DB マイグレーションツールとして導入する
- 非同期対応（async/await）を維持する
- 既存の SQLAlchemy モデル定義（Base）と整合性を保つ
- 開発環境のため、過去のマイグレーション履歴は全て置き換える

### 2. 機能要件

#### 2.1 Alembic 設定
- `alembic.ini`設定ファイルの作成
- 非同期エンジン対応の設定
- PostgreSQL 対応の設定
- 環境変数からデータベース接続情報を取得

#### 2.2 マイグレーション管理
- `alembic/`ディレクトリ構造の作成
- 自動マイグレーション生成機能（autogenerate）の有効化
- 既存のテーブル定義を初期マイグレーションとして作成
- ロールバック機能の実装

#### 2.3 既存システムとの統合
- 既存の`app/infrastructure/database/connection.py`との連携
- 既存の SQLAlchemy モデル（ListedInfoModel, StockModel）の認識
- アプリケーション起動時の自動マイグレーション実行オプション

### 3. 対象テーブル
現在確認されているテーブル：
- `listed_info`: J-Quants 上場企業情報テーブル
  - 複合主キー: (date, code)
  - インデックス: code, date
- その他のテーブル（StockModel など）も含む

### 4. 置き換え対象
以下の SQL マイグレーションファイルを置き換える：
- `sql/migrations/001_create_listed_info_table.sql`
- `sql/migrations/001_rollback_listed_info_table.sql`
- `sql/migrations/002_alter_listed_info_code_length.sql`
- `sql/migrations/003_alter_listed_info_code_length_10.sql`

### 5. 開発者向け機能
- マイグレーション履歴の確認コマンド
- 現在のスキーマ状態の確認コマンド
- マイグレーションの生成・適用・ロールバックコマンド
- テスト環境でのマイグレーション実行方法

### 6. 制約事項
- 本番環境への移行は考慮しない（開発環境専用）
- 既存データの移行は不要（開発中のため）
- Python 3.11 以上を前提とする
- FastAPI アプリケーションとの統合を考慮する

### 7. 成果物
- Alembic 設定ファイル一式
- 初期マイグレーションスクリプト
- 使用方法のドキュメント
- CLI コマンドのサンプル