# Alembic マイグレーションガイド

## 概要

Stockura プロジェクトではデータベースマイグレーションに Alembic を使用しています。
このガイドでは、 Alembic を使用したマイグレーションの基本的な操作方法を説明します。

## 前提条件

- Python 3.11 以上
- PostgreSQL
- 必要な依存関係がインストールされていること（`pip install -r requirements.txt`）

## 基本的な使用方法

### CLI コマンド

マイグレーション操作は`scripts/db_migrate.py`スクリプトを通じて実行します。

```bash
# ヘルプの表示
python scripts/db_migrate.py --help

# サブコマンドのヘルプ
python scripts/db_migrate.py upgrade --help
```

### よく使うコマンド

#### 1. 現在の状態確認

```bash
# 現在のリビジョンを確認
python scripts/db_migrate.py current

# マイグレーション履歴を表示
python scripts/db_migrate.py history

# 未適用のマイグレーションがあるか確認
python scripts/db_migrate.py check
```

#### 2. マイグレーションの実行

```bash
# 最新のマイグレーションまで適用
python scripts/db_migrate.py upgrade

# 特定のリビジョンまで適用
python scripts/db_migrate.py upgrade --revision abc123

# 1 つ前のリビジョンにロールバック
python scripts/db_migrate.py downgrade

# 特定のリビジョンまでロールバック
python scripts/db_migrate.py downgrade --revision abc123
```

#### 3. 新しいマイグレーションの作成

```bash
# モデルの変更を自動検出してマイグレーションを生成
python scripts/db_migrate.py revision -m "Add new column to stocks table"

# 手動でマイグレーションを作成（自動検出なし）
python scripts/db_migrate.py revision -m "Custom migration" --no-autogenerate
```

### Alembic の標準コマンド

CLI コマンドの代わりに、 Alembic の標準コマンドも使用できます：

```bash
# 現在の状態確認
alembic current

# マイグレーション履歴
alembic history

# アップグレード
alembic upgrade head

# ダウングレード
alembic downgrade -1

# 新しいマイグレーション作成
alembic revision --autogenerate -m "Description"
```

## 開発フロー

### 1. モデルの変更

SQLAlchemy モデル（`app/infrastructure/database/models/`）を変更します。

```python
# 例: 新しいカラムを追加
class StockModel(Base):
    __tablename__ = "stocks"
    
    # 既存のカラム
    ticker_symbol = Column(String(10), nullable=False)
    
    # 新しいカラムを追加
    exchange = Column(String(50), nullable=True)  # 新規追加
```

### 2. マイグレーションの生成

```bash
python scripts/db_migrate.py revision -m "Add exchange column to stocks"
```

### 3. マイグレーションファイルの確認

生成されたファイル（`alembic/versions/xxx_add_exchange_column_to_stocks.py`）を確認し、
必要に応じて修正します。

### 4. マイグレーションの実行

```bash
python scripts/db_migrate.py upgrade
```

### 5. 動作確認

```bash
python scripts/db_migrate.py current
```

## トラブルシューティング

### 1. マイグレーションが失敗した場合

```bash
# ロールバック
python scripts/db_migrate.py downgrade

# 問題を修正してから再実行
python scripts/db_migrate.py upgrade
```

### 2. データベースをリセットしたい場合

**注意**: この操作はすべてのデータを削除します！

```bash
python scripts/db_migrate.py reset
```

### 3. 初期化が必要な場合

新しい環境でデータベースを初期化する場合：

```bash
python scripts/db_migrate.py init
```

## ベストプラクティス

1. **マイグレーションファイルは編集しない**
   - 一度コミットされたマイグレーションファイルは編集しない
   - 修正が必要な場合は新しいマイグレーションを作成する

2. **マイグレーション前にバックアップ**
   - 本番環境では必ずバックアップを取る
   - 開発環境でも重要なデータがある場合はバックアップを推奨

3. **マイグレーションの確認**
   - 自動生成されたマイグレーションは必ず確認する
   - 不要な変更が含まれていないかチェック

4. **小さな単位でマイグレーション**
   - 1 つのマイグレーションで多くの変更を行わない
   - 関連する変更をグループ化する

## 非同期対応について

このプロジェクトの Alembic は非同期 SQLAlchemy に対応しています。
`alembic/env.py`で非同期エンジンを使用するようカスタマイズされています。

## 設定ファイル

- `alembic.ini` - Alembic の基本設定
- `alembic/env.py` - 環境設定（非同期対応）
- `app/infrastructure/database/migration.py` - ヘルパー関数

## 関連ドキュメント

- [Alembic 公式ドキュメント](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 公式ドキュメント](https://www.sqlalchemy.org/)