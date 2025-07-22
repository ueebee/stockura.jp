# ローカル開発環境セットアップガイド

## 概要
Docker環境で開発を行いながら、エディターの補完機能やリンティングを活用するため、ローカル環境にもパッケージをインストールする手順です。

## 前提条件
- Python 3.11または3.12を推奨（3.13はpsycopg2との互換性問題あり）
- PostgreSQLクライアントライブラリ（libpq）
- Redis（オプション）

## セットアップ手順

### 1. Python環境の準備

```bash
# Python 3.12をインストール（miseを使用している場合）
mise install python@3.12
mise use python@3.12

# または pyenv を使用
pyenv install 3.12.7
pyenv local 3.12.7
```

### 2. 必要なシステムパッケージのインストール（macOS）

```bash
# Homebrew でPostgreSQLクライアントをインストール
brew install postgresql@17
brew install redis  # オプション

# 環境変数を設定（.zshrcや.bashrcに追加推奨）
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/postgresql@17/lib"
export CPPFLAGS="-I/opt/homebrew/opt/postgresql@17/include"
```

### 3. Python仮想環境の作成

```bash
# プロジェクトルートで実行
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 4. パッケージのインストール

#### オプション1: psycopg2-binaryを使用（推奨）
```bash
# requirements.txtを一時的に修正
sed 's/psycopg2==/psycopg2-binary==/' requirements.txt > requirements-local.txt

# インストール
pip install -r requirements-local.txt
```

#### オプション2: システムのpsycopg2を使用
```bash
# macOSでPostgreSQLがインストール済みの場合
pip install psycopg2-binary==2.9.9
pip install -r requirements.txt
```

#### オプション3: エディター用の最小限のパッケージのみインストール
```bash
# requirements-dev.txtを作成
cat > requirements-dev.txt << EOF
# Type checking and linting
mypy==1.8.0
pylint==3.0.3
black==24.1.1
flake8==7.0.0

# Core packages for editor support
fastapi==0.104.1
sqlalchemy==2.0.0
pydantic==2.5.3
celery==5.3.6

# Stubs for type checking
types-redis
types-requests
sqlalchemy-stubs
EOF

pip install -r requirements-dev.txt
```

### 5. VSCode設定（推奨）

`.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.extraPaths": [
        "${workspaceFolder}/app"
    ],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### 6. トラブルシューティング

#### psycopg2のビルドエラー
```bash
# Python 3.13で発生する場合
# 1. Python 3.12に切り替える
mise use python@3.12

# 2. または、プリコンパイル版を使用
pip install --only-binary :all: psycopg2-binary==2.9.9
```

#### asyncpgのビルドエラー
```bash
# Cythonを先にインストール
pip install Cython
pip install asyncpg==0.29.0
```

#### M1/M2 Macでの問題
```bash
# arm64アーキテクチャ用の設定
export ARCHFLAGS="-arch arm64"
pip install -r requirements.txt
```

## 開発ワークフロー

1. **コード編集**: ローカル環境でエディターを使用
2. **実行・テスト**: Docker環境で実行
3. **デバッグ**: 必要に応じてローカルまたはDocker環境を選択

### Docker環境との連携
```bash
# コードの変更はボリュームマウントで自動反映
docker compose up -d

# ログの確認
docker compose logs -f web

# テストの実行
docker compose exec web pytest
```

## 注意事項

- ローカル環境はあくまでエディターサポート用
- 実際の動作確認は必ずDocker環境で行う
- データベース接続等はDocker環境のものを使用
- 環境変数は`.env`ファイルで管理（Dockerと共通）

## 推奨される.gitignore追加項目
```
# Local development
venv/
.venv/
*.pyc
__pycache__/
.mypy_cache/
.pytest_cache/
.coverage
htmlcov/
```