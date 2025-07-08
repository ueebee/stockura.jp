# GitHub設定ファイル

このディレクトリにはGitHub固有の設定ファイルが含まれています。

## workflows/

GitHub Actionsのワークフロー定義を配置します。

### test.yml.example
- 自動テスト実行のサンプル設定
- CI/CDを導入する際は`.example`を削除して使用
- PostgreSQLとRedisのサービスコンテナを含む

## 使い方

1. GitHub Actionsを有効化する場合:
   ```bash
   mv workflows/test.yml.example workflows/test.yml
   ```

2. 必要に応じて設定を調整:
   - Pythonバージョン
   - テスト実行コマンド
   - カバレッジレポートの設定

## 参考リンク
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [GitHub Actions for Python](https://docs.github.com/actions/automating-builds-and-tests/building-and-testing-python)