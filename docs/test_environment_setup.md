# テスト環境セットアップ補足

## 環境変数の設定

テストを実行する前に、テスト用の環境変数ファイルを作成する必要があります：

```bash
# .env.test.example を .env.test にコピー
cp .env.test.example .env.test

# 必要に応じて .env.test を編集
# ※ 実際のAPIキーやパスワードは使用しないでください
```

## Docker環境でのテスト実行

### 1. テスト環境の起動

```bash
# テストコンテナをビルド
docker compose -f docker-compose.test.yml build

# 全てのテストを実行
docker compose -f docker-compose.test.yml run --rm test

# 特定のテストファイルを実行
docker compose -f docker-compose.test.yml run --rm test pytest tests/unit/models/test_company.py -v

# カバレッジレポート付きで実行
docker compose -f docker-compose.test.yml run --rm test pytest --cov=app --cov-report=html
```

### 2. インタラクティブモードでのデバッグ

```bash
# テストコンテナに入る
docker compose -f docker-compose.test.yml run --rm test bash

# コンテナ内でテストを実行
pytest -v
pytest -s  # print文の出力を表示
pytest --pdb  # デバッガを使用
```

### 3. テスト環境のクリーンアップ

```bash
# コンテナとボリュームを削除
docker compose -f docker-compose.test.yml down -v
```

## セキュリティに関する注意事項

1. **.env.test には本番環境の認証情報を含めないでください**
2. **テスト用のAPIキーやパスワードは、実際のサービスで使用できないダミー値を使用してください**
3. **.env.test は Git にコミットしないでください（.gitignore に含まれています）**
4. **CI/CD環境では、環境変数として機密情報を管理してください**

## トラブルシューティング

### データベース接続エラー

```bash
# テスト用データベースが存在するか確認
docker compose -f docker-compose.test.yml exec db-test psql -U postgres -c "\l"

# テスト用データベースを再作成
docker compose -f docker-compose.test.yml exec db-test psql -U postgres -c "DROP DATABASE IF EXISTS stockura_test;"
docker compose -f docker-compose.test.yml exec db-test psql -U postgres -c "CREATE DATABASE stockura_test;"
```

### 依存関係の競合

requirements.txt と requirements-test.txt でバージョンが競合する場合：

1. requirements-test.txt から競合するパッケージを削除
2. requirements.txt のバージョンを使用

### ポートの競合

本番環境と同時に起動する場合、ポートが競合することがあります。
docker-compose.test.yml では以下のポートを使用しています：

- PostgreSQL: 5433 (本番は 5432)
- Redis: 6380 (本番は 6379)