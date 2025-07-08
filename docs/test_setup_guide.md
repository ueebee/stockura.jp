# テスト環境セットアップガイド

## 概要

Stockura.jpプロジェクトのテスト環境を構築するためのガイドです。本プロジェクトではDocker環境でのテスト実行を推奨しています。

## 前提条件

- Docker及びDocker Composeがインストールされていること
- プロジェクトのルートディレクトリで作業していること

## クイックスタート

### 1. 環境変数ファイルの準備

```bash
# テスト用環境変数ファイルをコピー
cp .env.test.example .env.test
```

### 2. Docker環境でテスト実行（推奨）

```bash
# テストイメージをビルド
make test-docker-build

# 全てのテストを実行
make test-docker

# 詳細な出力でテストを実行
make test-docker-verbose

# カバレッジ付きでテストを実行
make test-docker-coverage
```

## 詳細な使用方法

### Docker環境でのテスト（推奨）

Docker環境を使用することで、本番環境に近い状態でテストを実行できます。

```bash
# テスト環境のセットアップと実行
make test-docker          # 全テストを実行
make test-docker-verbose  # 詳細出力付きで実行
make test-docker-coverage # カバレッジレポート付きで実行

# テスト環境の管理
make test-up              # テスト用DB・Redisを起動
make test-down            # テスト環境を停止
make test-clean           # テスト環境を完全にクリーンアップ
```

### ローカル環境でのテスト

ローカル環境でテストを実行する場合は、事前にテスト用のデータベースとRedisを起動する必要があります。

```bash
# 1. テスト環境を起動
make test-up

# 2. テストを実行
make test                 # 全テストを実行
make test-unit           # 単体テストのみ
make test-integration    # 統合テストのみ
make test-e2e           # E2Eテストのみ

# 3. テスト環境を停止
make test-down
```

### テストデータベースの管理

```bash
# テスト用データベースを再作成
make setup-test-db

# テスト環境を完全にリセット
make test-clean
make test-docker-build
```

## 特定のテストの実行

### Docker環境での実行

```bash
# 特定のテストファイルを実行
docker compose -f docker-compose.test.yml run --rm test pytest tests/unit/models/test_company.py -v

# 特定のテストクラスを実行
docker compose -f docker-compose.test.yml run --rm test pytest tests/unit/models/test_company.py::TestCompanyModel -v

# 特定のテストメソッドを実行
docker compose -f docker-compose.test.yml run --rm test pytest tests/unit/models/test_company.py::TestCompanyModel::test_create_company_with_required_fields -v
```

### ローカル環境での実行

```bash
# 特定のテストファイルを実行
make test-file FILE=tests/unit/models/test_company.py

# デバッグモードで実行
make test-debug

# 失敗したテストのみ再実行
make test-failed

# 高速テスト（slowマーカーを除外）
make test-fast

# 並列実行
make test-parallel
```

## デバッグオプション

### Docker環境でのデバッグ

```bash
# インタラクティブモードでコンテナに入る
docker compose -f docker-compose.test.yml run --rm test bash

# コンテナ内でデバッグ実行
pytest -s -vv --tb=long  # 標準出力を表示、詳細なトレースバック
pytest -x               # 最初のエラーで停止
pytest --pdb           # エラー時にデバッガを起動
```

### ローカル環境でのデバッグ

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

### Docker環境でのカバレッジ

```bash
# カバレッジ付きでテスト実行
make test-docker-coverage

# カバレッジレポートをホストにコピー
docker compose -f docker-compose.test.yml run --rm test sh -c "pytest --cov=app --cov-report=html && tar -czf coverage.tar.gz htmlcov"
docker compose -f docker-compose.test.yml run --rm test cat coverage.tar.gz > coverage.tar.gz
tar -xzf coverage.tar.gz
open htmlcov/index.html  # macOS
```

### ローカル環境でのカバレッジ

```bash
# カバレッジ付きでテスト実行
make coverage

# HTMLレポートを開く（macOS）
open htmlcov/index.html
```

## トラブルシューティング

### データベース接続エラー

#### Docker環境の場合
```bash
# テストコンテナの状態を確認
docker compose -f docker-compose.test.yml ps

# テストデータベースが存在するか確認
docker compose -f docker-compose.test.yml exec db-test psql -U postgres -l | grep stockura_test

# テスト環境を再起動
make test-clean
make test-docker-build
make test-docker
```

#### ローカル環境の場合
```bash
# テスト用DBが起動しているか確認
docker ps | grep db-test

# ポートが正しいか確認（5433番ポート）
nc -zv localhost 5433

# テスト環境を起動
make test-up
```

### モジュールインポートエラー

#### Docker環境の場合
```bash
# イメージを再ビルド
make test-docker-build

# requirements-test.txtが正しくコピーされているか確認
docker compose -f docker-compose.test.yml run --rm test ls -la requirements*.txt
```

#### ローカル環境の場合
```bash
# 仮想環境が有効化されているか確認
which python

# 必要なパッケージをインストール
pip install -r requirements.txt -r requirements-test.txt
```

### 非同期テストのエラー

1. pytest-asyncioがインストールされているか確認
2. テストメソッドに`@pytest.mark.asyncio`デコレータが付いているか確認
3. conftest.pyで非同期フィクスチャが正しく設定されているか確認

### ポートの競合

本番環境と同時に起動する場合、ポートが競合することがあります：

```bash
# 使用中のポートを確認
lsof -i :5433  # PostgreSQL
lsof -i :6380  # Redis

# 本番環境を一時停止
docker compose down

# テスト環境を起動
make test-up
```

## 継続的インテグレーション（CI）

GitHub ActionsやGitLab CIでテストを実行する場合は、docker-compose.test.ymlを使用：

```yaml
# .github/workflows/test.yml の例
- name: Build test environment
  run: docker compose -f docker-compose.test.yml build

- name: Run tests
  run: docker compose -f docker-compose.test.yml run --rm test pytest --cov=app --cov-report=xml

- name: Cleanup
  run: docker compose -f docker-compose.test.yml down -v
```

## ベストプラクティス

1. **常にDocker環境でテストを実行する**
   - 環境の一貫性が保たれる
   - 本番環境に近い状態でテスト可能

2. **テスト前に環境をクリーンアップ**
   ```bash
   make test-clean
   make test-docker-build
   ```

3. **定期的にカバレッジを確認**
   ```bash
   make test-docker-coverage
   ```

4. **失敗したテストは即座に修正**
   - `make test-failed`で失敗したテストのみ再実行

5. **並列実行で時間短縮**
   - ローカル環境では`make test-parallel`を活用