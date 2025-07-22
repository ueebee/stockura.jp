# Stockura ユーティリティスクリプト

このディレクトリには、開発とテストを支援するためのユーティリティスクリプトが含まれています。

## スクリプト一覧

### regression_test.py

リファクタリング後の動作確認を行うためのリグレッションテストツールです。手動テストと自動ブラウザテストの両方をサポートしています。

**使用方法:**
```bash
# 手動テストモード（デフォルト）
python bin/regression_test.py

# 自動ブラウザテストモード
python bin/regression_test.py --auto

# 確認プロンプトをスキップ
python bin/regression_test.py --auto --no-confirm
```

**機能:**
- データベースのクリーンな初期化
- 手動テスト手順の提供
- 自動ブラウザテスト（Playwright使用）
- テスト結果レポートの生成
- スクリーンショットの保存
- テスト実行時刻の自動計算（JST）

**必要な依存関係（自動テストモード）:**
```bash
pip install playwright
playwright install chromium
```

**注意:** このスクリプトはデータベースを完全にリセットします。開発環境でのみ使用してください。

詳細は [リグレッションテストガイド](../docs/regression_test_guide.md) を参照してください。