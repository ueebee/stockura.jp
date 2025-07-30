# Docker テスト環境ガイド

このガイドでは、 Docker 環境でのテスト実行方法について説明します。

## テスト環境の概要

テスト環境は独立したコンテナで実行され、開発環境に影響を与えません。

### テスト環境の特徴

- 独立したデータベース（テスト用）
- 自動的なクリーンアップ
- CI/CD 対応
- カバレッジレポート生成

## テストの実行

### 基本的なテスト実行

```bash
# すべてのテストを実行
make test

# または
./scripts/docker/run-tests.sh
```

### 特定のテストを実行

```bash
# 特定のファイルのテストを実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_auth.py

# 特定のテスト関数を実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_auth.py::test_login

# マーカーを使用してテストを実行
docker-compose -f docker-compose.test.yml run --rm test pytest -m "not slow"
```

### テストオプション

```bash
# 詳細な出力
docker-compose -f docker-compose.test.yml run --rm test pytest -v

# 失敗したテストで停止
docker-compose -f docker-compose.test.yml run --rm test pytest -x

# 最後に失敗したテストを再実行
docker-compose -f docker-compose.test.yml run --rm test pytest --lf

# カバレッジレポートを生成
docker-compose -f docker-compose.test.yml run --rm test pytest --cov=app --cov-report=html
```

## 統合テスト

### Celery タスクのテスト

```bash
# Celery タスクのテストを実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/integration/test_celery_tasks.py
```

### API エンドポイントのテスト

```bash
# API テストを実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/integration/test_api_endpoints.py
```

## テストデータの管理

### フィクスチャーの使用

```python
# tests/conftest.py でフィクスチャーを定義
import pytest
from app.infrastructure.database.connection import get_async_session_context

@pytest.fixture
async def db_session():
    async with get_async_session_context() as session:
        yield session
        await session.rollback()
```

### テストデータベースの初期化

```bash
# テストデータベースのマイグレーション
docker-compose -f docker-compose.test.yml run --rm test alembic upgrade head

# テストデータのシード
docker-compose -f docker-compose.test.yml run --rm test python scripts/seed_test_data.py
```

## デバッグ

### テストコンテナでのデバッグ

```bash
# インタラクティブモードでテストコンテナを起動
docker-compose -f docker-compose.test.yml run --rm test bash

# Python デバッガーを使用
docker-compose -f docker-compose.test.yml run --rm test pytest -s --pdb
```

### ログの確認

```bash
# テスト実行中のログを確認
docker-compose -f docker-compose.test.yml logs -f

# 特定のサービスのログを確認
docker-compose -f docker-compose.test.yml logs -f test-postgres
```

## CI/CD 統合

### GitHub Actions での実行

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run tests
      run: |
        cp .env.example .env
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit
        
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## パフォーマンステスト

### 負荷テストの実行

```bash
# Locust を使用した負荷テスト
docker-compose -f docker-compose.test.yml run --rm test locust -f tests/performance/locustfile.py
```

### プロファイリング

```bash
# プロファイリング付きでテストを実行
docker-compose -f docker-compose.test.yml run --rm test pytest --profile
```

## トラブルシューティング

### テストが失敗する場合

1. **データベース接続エラー**
   ```bash
   # テストデータベースの状態を確認
   docker-compose -f docker-compose.test.yml ps
   ```

2. **依存関係の問題**
   ```bash
   # イメージを再ビルド
   docker-compose -f docker-compose.test.yml build --no-cache
   ```

3. **テストの分離問題**
   ```bash
   # テストを個別に実行して問題を特定
   docker-compose -f docker-compose.test.yml run --rm test pytest tests/unit/ -v
   ```

### クリーンアップ

```bash
# テスト環境を完全にクリーンアップ
docker-compose -f docker-compose.test.yml down -v

# 未使用のテストイメージを削除
docker image prune -f
```

## ベストプラクティス

1. **テストの分離**: 各テストは独立して実行できるようにする
2. **フィクスチャーの活用**: 共通のセットアップはフィクスチャーに抽出
3. **非同期テストの適切な処理**: `pytest-asyncio` を使用
4. **モックの活用**: 外部 API はモックを使用
5. **並列実行**: `pytest-xdist` で高速化

## テストカバレッジ

### カバレッジレポートの生成

```bash
# HTML レポートを生成
make test-coverage

# カバレッジを確認
open htmlcov/index.html
```

### カバレッジ目標

- 全体: 80% 以上
- コアロジック: 90% 以上
- API エンドポイント: 95% 以上