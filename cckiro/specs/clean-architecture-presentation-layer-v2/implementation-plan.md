# CLI 層の依存性注入改善実装計画

## 概要

presentation 層の CLI コマンドの依存性注入を改善する実装計画です。段階的に実装を進め、各段階で動作確認を行います。

## 実装フェーズ

### Phase 1: CLI 用依存性プロバイダーの作成（30 分）

#### 1.1 `app/presentation/dependencies/cli.py`の作成

**タスク:**
1. 新規ファイルを作成
2. 基本的な依存性注入関数を実装
   - `get_cli_session()`: データベースセッション
   - `get_cli_auth_repository()`: 認証リポジトリ
   - `get_cli_listed_info_repository()`: 上場銘柄情報リポジトリ
   - `get_cli_jquants_client()`: J-Quants クライアント

**成功基準:**
- ファイルが正常に作成される
- インポートエラーが発生しない
- 既存のテストに影響を与えない

### Phase 2: fetch_listed_info_command.py のリファクタリング（1 時間）

#### 2.1 認証処理の分離

**タスク:**
1. `authenticate_jquants()`関数を作成
2. 認証ロジックを関数に移動
3. エラーハンドリングを統一

#### 2.2 依存性注入への移行

**タスク:**
1. インフラストラクチャ層への直接インポートを削除
2. CLI 用依存性プロバイダーをインポート
3. 依存性注入を使用するようにメイン処理を変更

#### 2.3 テストと動作確認

**タスク:**
1. 単体テストの実行
2. CLI コマンドの手動実行テスト
3. エラーケースの確認

**成功基準:**
- インフラストラクチャ層への直接的な依存がない
- CLI コマンドが正常に動作する
- エラーハンドリングが適切に機能する

### Phase 3: migration_command.py のリファクタリング（45 分）

#### 3.1 MigrationService インターフェースの実装

**タスク:**
1. `app/presentation/dependencies/migration.py`を作成
2. `MigrationService`プロトコルを定義
3. `get_migration_service()`関数を実装

#### 3.2 migration_command.py の更新

**タスク:**
1. インフラストラクチャ層への直接インポートを削除
2. MigrationService を使用するように変更
3. 各コマンドの実装を更新

#### 3.3 インフラストラクチャ層の対応

**タスク:**
1. `MigrationServiceImpl`クラスを作成（必要に応じて）
2. 既存のマイグレーション関数をラップ

**成功基準:**
- マイグレーションコマンドが正常に動作する
- 依存性が適切に注入される

### Phase 4: 最終確認とドキュメント更新（30 分）

#### 4.1 全体テストの実行

**タスク:**
1. 全てのテストスイートを実行
2. カバレッジの確認
3. 統合テストの実行

#### 4.2 動作確認

**タスク:**
1. `fetch_listed_info`コマンドの実行
2. データベースマイグレーションコマンドの実行
3. エラーケースの確認

#### 4.3 ドキュメントの更新

**タスク:**
1. README.md の更新（必要に応じて）
2. コミットメッセージの準備

## 実装の詳細手順

### Step 1: CLI 依存性プロバイダーの作成

```bash
# ファイルを作成
touch app/presentation/dependencies/cli.py
```

実装内容は設計書に従う。

### Step 2: fetch_listed_info_command.py の更新

1. バックアップの作成（Git 管理されているので不要だが念のため確認）
2. 段階的な変更
   - まず認証処理を分離
   - 次に依存性注入に移行
3. 各段階でテスト実行

### Step 3: migration_command.py の更新

1. MigrationService の設計
2. 最小限の変更で実装
3. 動作確認

### Step 4: テスト実行

```bash
# 単体テストの実行
pytest tests/unit/presentation/

# 統合テストの実行
pytest tests/integration/

# CLI コマンドの動作確認
python -m app.presentation.cli.commands.fetch_listed_info --help
python scripts/db_migrate.py --help
```

## リスク管理

### 想定されるリスクと対策

1. **依存性の循環参照**
   - 監視: インポート時のエラー
   - 対策: 遅延インポートの使用

2. **テストの失敗**
   - 監視: 各フェーズでのテスト実行
   - 対策: 段階的な実装とロールバック

3. **CLI コマンドの動作不良**
   - 監視: 手動での動作確認
   - 対策: デバッグログの追加

## チェックリスト

- [ ] Phase 1: CLI 依存性プロバイダーの作成
  - [ ] cli.py ファイルの作成
  - [ ] 基本的な依存性注入関数の実装
  - [ ] インポートエラーがないことの確認

- [ ] Phase 2: fetch_listed_info_command.py のリファクタリング
  - [ ] 認証処理の分離
  - [ ] 依存性注入への移行
  - [ ] テストの成功
  - [ ] CLI コマンドの動作確認

- [ ] Phase 3: migration_command.py のリファクタリング
  - [ ] MigrationService の実装
  - [ ] コマンドの更新
  - [ ] マイグレーションの動作確認

- [ ] Phase 4: 最終確認
  - [ ] 全テストの成功
  - [ ] 手動での動作確認
  - [ ] ドキュメントの更新

## 完了基準

1. すべての CLI コマンドがインフラストラクチャ層に直接依存していない
2. 依存性注入が統一的に実装されている
3. すべてのテストが成功している
4. CLI コマンドが正常に動作する
5. コードレビューの準備が完了している