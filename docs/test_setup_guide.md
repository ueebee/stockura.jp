# テスト環境セットアップガイド

## 概要

Stockura.jpプロジェクトのテスト環境を構築するためのガイドです。

## 前提条件

- Docker環境が起動していること
- PostgreSQLコンテナが稼働していること
- Pythonの仮想環境が有効化されていること

## テストデータベースのセットアップ

### 1. テスト用データベースの作成

```bash
# Dockerコンテナ内でテスト用データベースを作成
docker exec stockurajp-db-1 psql -U postgres -c "CREATE DATABASE stockura_test;"
```

### 2. 環境変数の設定

テスト実行時は以下の環境変数を設定してください：

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/stockura_test"
```

## テストの実行

### 全テストの実行

```bash
# カバレッジなしで実行（高速）
./venv/bin/pytest

# カバレッジありで実行
./venv/bin/pytest --cov=app --cov-report=html
```

### 特定のテストファイルの実行

```bash
# Companyモデルのテストのみ実行
./venv/bin/pytest tests/unit/models/test_company.py -v
```

### 特定のテストケースの実行

```bash
# 特定のテストメソッドのみ実行
./venv/bin/pytest tests/unit/models/test_company.py::TestCompanyModel::test_create_company_with_required_fields -v
```

## デバッグオプション

```bash
# 標準出力を表示
./venv/bin/pytest -s

# 詳細なトレースバック
./venv/bin/pytest --tb=long

# 最初のエラーで停止
./venv/bin/pytest -x

# 失敗したテストのみ再実行
./venv/bin/pytest --lf
```

## カバレッジレポート

テスト実行後、`htmlcov/index.html`をブラウザで開くことで、詳細なカバレッジレポートを確認できます。

```bash
# HTMLレポートを生成して開く（macOS）
./venv/bin/pytest --cov=app --cov-report=html && open htmlcov/index.html
```

## トラブルシューティング

### データベース接続エラー

1. Dockerコンテナが起動しているか確認：
   ```bash
   docker ps | grep postgres
   ```

2. テストデータベースが存在するか確認：
   ```bash
   docker exec stockurajp-db-1 psql -U postgres -l | grep stockura_test
   ```

### モジュールインポートエラー

1. 仮想環境が有効化されているか確認
2. 必要なパッケージがインストールされているか確認：
   ```bash
   ./venv/bin/pip install -r requirements-test.txt
   ```

### 非同期テストのエラー

1. pytest-asyncioがインストールされているか確認
2. テストメソッドに`@pytest.mark.asyncio`デコレータが付いているか確認

## 継続的インテグレーション（CI）

GitHub ActionsやGitLab CIでテストを実行する場合は、以下の設定を使用してください：

```yaml
# .github/workflows/test.yml の例
- name: Run tests
  env:
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/stockura_test
  run: |
    pytest --cov=app --cov-report=xml
```