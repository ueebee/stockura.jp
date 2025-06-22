# 開発ガイド

## 開発環境のセットアップ

### 必要なツール
- Python 3.11以上
- Redis
- PostgreSQL（開発環境ではSQLiteも可）

### 環境構築手順

1. リポジトリのクローン
```bash
git clone [repository-url]
cd stockura
```

2. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # Linuxの場合
# または
.\venv\Scripts\activate  # Windowsの場合
```

3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

4. 環境変数の設定
`.env`ファイルを作成し、必要な環境変数を設定します：
```env
DATABASE_URL=postgresql://user:password@localhost:5432/stockura
REDIS_URL=redis://localhost:6379/0
API_KEY_JQUANTS=your_api_key
```

## 開発フロー

### 1. 機能開発

1. 新しい機能の開発は、必ず新しいブランチで開始します：
```bash
git checkout -b feature/your-feature-name
```

2. 開発中は定期的にコミットを行います：
```bash
git add .
git commit -m "feat: 機能の説明"
```

3. プルリクエストを作成する前に、以下の確認を行います：
   - コードがPEP 8に準拠しているか
   - 型ヒントが適切に設定されているか
   - テストが追加されているか
   - ドキュメントが更新されているか

### 2. テスト

1. ユニットテストの実行：
```bash
pytest
```

2. カバレッジレポートの生成：
```bash
pytest --cov=app tests/
```

### 3. コードレビュー

1. プルリクエストの作成
2. レビュアーのアサイン
3. レビューコメントへの対応
4. 承認後のマージ

## コーディング規約

### Pythonコード

1. **インポート順序**
```python
# 標準ライブラリ
import os
import sys

# サードパーティライブラリ
import fastapi
import sqlalchemy

# ローカルモジュール
from app.core import config
from app.services import stock_data
```

2. **型ヒントの使用**
```python
from typing import List, Optional

def get_stock_data(symbol: str, period: str = "1d") -> List[dict]:
    ...
```

3. **ドキュメント文字列**
```python
def fetch_stock_price(symbol: str) -> float:
    """指定された銘柄の現在の株価を取得します。

    Args:
        symbol (str): 証券コード

    Returns:
        float: 現在の株価

    Raises:
        StockDataError: データ取得に失敗した場合
    """
    ...
```

### HTMLテンプレート

1. **コンポーネントの命名規則**
- ファイル名: `snake_case.html`
- コンポーネントID: `kebab-case`

2. **テンプレートの構造**
```html
<!-- 再利用可能なコンポーネント -->
<div id="stock-price-card" class="card">
    <div class="card-header">
        <h3>{{ stock.symbol }}</h3>
    </div>
    <div class="card-body">
        <!-- コンテンツ -->
    </div>
</div>
```

## デプロイメント

### 開発環境

1. ローカルでの実行：
```bash
uvicorn app.main:app --reload
```

2. Celeryワーカーの起動：
```bash
celery -A app.tasks worker --loglevel=info
```

### 本番環境

1. 環境変数の設定
2. データベースのマイグレーション
3. アプリケーションの起動
4. モニタリングの設定

## トラブルシューティング

### よくある問題と解決方法

1. **データベース接続エラー**
   - 接続文字列の確認
   - データベースの起動確認

2. **Redis接続エラー**
   - Redisサーバーの起動確認
   - 接続設定の確認

3. **APIレート制限エラー**
   - レート制限の設定確認
   - リトライロジックの確認

## 参考リンク

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Hotwire公式ドキュメント](https://hotwired.dev/)
- [Celery公式ドキュメント](https://docs.celeryq.dev/)
- [SQLAlchemy公式ドキュメント](https://www.sqlalchemy.org/) 