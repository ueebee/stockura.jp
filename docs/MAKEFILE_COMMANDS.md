# Makefile コマンドリファレンス

## 概要

このドキュメントでは、 stockura プロジェクトの Makefile で利用可能なコマンドについて説明します。

## 基本コマンド

### 開発環境

```bash
# ヘルプを表示
make help

# Docker イメージをビルド
make build

# 開発環境を起動
make up

# すべてのコンテナを停止
make down

# コンテナログを表示
make logs
```

### テスト関連

```bash
# Docker 内でテストを実行
make test

# ウォッチモードでテストを実行
make test-watch
```

### データベース

```bash
# データベースマイグレーション（ヘルプを表示）
make migrate

# マイグレーションを実行
make migrate upgrade

# 現在のリビジョンを表示
make migrate current

# マイグレーション履歴を表示
make migrate history

# 新しいマイグレーションを作成
make migrate-create MSG="your migration message"
```

### ユーティリティ

```bash
# app コンテナのシェルを開く
make shell

# PostgreSQL のシェルを開く
make shell-db

# Redis CLI を開く
make redis-cli
```

## スクリプト実行コマンド

### 汎用スクリプト実行

```bash
# 利用可能なスクリプトを表示
make run-script

# 特定のスクリプトを実行
make run-script SCRIPT=script_name.py
```

### テストスクリプト

```bash
# 利用可能なテストスクリプトを表示
make test-scripts

# 特定のテストスクリプトを実行
make test-script test_weekly_margin_interest.py

# すべてのテストスクリプトを実行
make test-scripts-all

# すべてのテストスクリプトを自動モードで実行
make test-scripts-all-auto
```

## スケジュール API テスト

### 新規追加コマンド

```bash
# スケジュール API テスト（インタラクティブモード）
make test-scheduled-api

# スケジュール API テスト（自動モード）
make test-scheduled-api-auto
```

#### test-scheduled-api
- 1 分後に実行されるスケジュールを作成
- 実行前に確認プロンプトが表示される
- 8 月 6 日の listed_info データを取得

#### test-scheduled-api-auto
- `test-scheduled-api` と同じ処理を自動モードで実行
- 確認プロンプトがスキップされる
- CI/CD パイプラインやバッチ処理に適している

### 実行例

```bash
# インタラクティブモード
$ make test-scheduled-api
Testing scheduled listed_info API...
This will create a schedule to run 1 minute from now.

前提条件:
1. FastAPI サーバーが起動していること:
   uvicorn app.main:app --reload
2. Celery ワーカーが起動していること:
   celery -A app.infrastructure.celery.app worker --loglevel=info
3. Celery Beat が起動していること:
   celery -A app.infrastructure.celery.app beat --loglevel=info
4. Redis/PostgreSQL が起動していること
----------------------------------------

上記の前提条件を確認してください。続行するには Enter キーを押してください...
```

```bash
# 自動モード
$ make test-scheduled-api-auto
Testing scheduled listed_info API (auto mode)...
This will create a schedule to run 1 minute from now.

前提条件:
1. FastAPI サーバーが起動していること:
   uvicorn app.main:app --reload
2. Celery ワーカーが起動していること:
   celery -A app.infrastructure.celery.app worker --loglevel=info
3. Celery Beat が起動していること:
   celery -A app.infrastructure.celery.app beat --loglevel=info
4. Redis/PostgreSQL が起動していること
----------------------------------------

自動モードで実行中...
[2024-XX-XX HH:MM:SS] INFO: ================================================================================
[2024-XX-XX HH:MM:SS] INFO: スケジュール作成テスト開始
...
```

## クリーンアップ

```bash
# コンテナとボリュームをクリーンアップ
make clean

# すべてクリーンアップ（イメージも含む）
make clean-all
```

## プロダクション環境

```bash
# プロダクションイメージをビルド
make prod-build

# プロダクション環境を起動
make prod-up

# プロダクション環境を停止
make prod-down

# プロダクションログを表示
make prod-logs
```

## 環境判定

Makefile は実行環境を自動的に判定します：

- Docker コンテナ内: 直接 Python スクリプトを実行
- ホストマシン: docker-compose exec を使用してコンテナ内で実行

これにより、どちらの環境からでも同じコマンドを使用できます。