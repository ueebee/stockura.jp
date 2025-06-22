# プロジェクト構造

## ディレクトリ構成

```
stockura/
├── app/                    # アプリケーションのメインコード
│   ├── __init__.py
│   ├── main.py            # FastAPIアプリケーションのエントリーポイント
│   ├── api/               # API関連のコード
│   │   ├── __init__.py
│   │   ├── routes/        # APIエンドポイント
│   │   │   ├── __init__.py
│   │   │   └── stock.py
│   │   └── dependencies.py # 依存性注入
│   ├── core/              # コア機能
│   │   ├── __init__.py
│   │   ├── config.py      # アプリケーション設定
│   │   └── celery_app.py  # Celery設定
│   ├── models/            # SQLAlchemyモデル
│   │   ├── __init__.py
│   │   └── stock.py
│   ├── schemas/           # Pydanticモデル
│   │   ├── __init__.py
│   │   └── stock.py
│   ├── services/          # ビジネスロジック
│   │   ├── __init__.py
│   │   └── stock_service.py
│   ├── tasks/             # Celeryタスク
│   │   ├── __init__.py
│   │   └── stock_tasks.py
│   └── templates/         # HTMLテンプレート
│       ├── base.html
│       └── home.html
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── conftest.py
│   └── test_tasks.py
├── logs/                  # ログファイル
│   └── celery.log
├── .env                  # 環境変数
├── .gitignore
├── requirements.txt      # 依存パッケージ
├── docker-compose.yml   # Docker設定
└── README.md
```

## 主要ディレクトリの説明

### app/
アプリケーションのメインコードを格納するディレクトリです。

- **main.py**: FastAPIアプリケーションのエントリーポイント
- **api/**: RESTful APIのエンドポイントと関連コード
- **core/**: アプリケーションのコア機能（設定、Celery設定など）
- **models/**: SQLAlchemyモデル定義
- **schemas/**: Pydanticモデル定義（リクエスト/レスポンスの型定義）
- **services/**: ビジネスロジックを実装するサービス層
- **tasks/**: Celeryタスクの実装
- **templates/**: HTMLテンプレート

### tests/
テストコードを格納するディレクトリです。

### logs/
ログファイルを格納するディレクトリです。

## 設計方針

1. **シンプルな構造**
   - 必要最小限のディレクトリ構成
   - 明確な責務分担

2. **非同期処理**
   - Celeryを使用した非同期タスク処理
   - レート制限の管理

3. **型安全性**
   - Pydanticモデルによるリクエスト/レスポンスの型チェック
   - SQLAlchemyモデルによるデータベース操作の型安全性

## 開発ガイドライン

1. **コード規約**
   - PEP 8に準拠
   - 型ヒントを積極的に使用
   - ドキュメント文字列（docstring）の必須化

2. **テスト方針**
   - ユニットテストの必須化
   - テストカバレッジの目標値設定

3. **非同期処理**
   - 重い処理はCeleryタスクとして実装
   - タスクの状態管理とエラーハンドリング

4. **ログ管理**
   - Celeryタスクのログを適切に管理
   - エラー発生時のトレース情報の保持 