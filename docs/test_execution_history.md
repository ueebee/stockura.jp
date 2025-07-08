# テスト実行履歴

## 概要
このドキュメントは、テスト修正作業中の各実行結果を記録したものです。

## 実行履歴

### 1回目: 初回実行
```
make test-docker
```
- **結果**: 192 errors
- **主な問題**: 
  - Dockerコマンドが見つからない（`FileNotFoundError: [Errno 2] No such file or directory: 'docker'`）
  - すべてのテストでエラー発生

### 2回目: Dockerエラー修正後
- **修正内容**: conftest.pyのDocker環境チェックを修正
- **結果**: 192 errors
- **主な問題**:
  - pg_trgm拡張機能が存在しない（`operator class "gin_trgm_ops" does not exist`）

### 3回目: pg_trgm追加後
- **修正内容**: docker-compose.test.ymlにinit.sqlを追加
- **結果**: 192 errors
- **主な問題**:
  - インデックスの重複（`relation "ix_daily_quotes_code" already exists`）

### 4回目: インデックス修正後
- **修正内容**: DailyQuoteモデルから重複インデックスを削除
- **結果**: 95 failed, 97 passed
- **改善**: 初めてテストがパスし始めた
- **主な問題**:
  - 非同期テストのイベントループエラー（`RuntimeError: There is no current event loop`）
  - モックの設定問題（`AttributeError: 'coroutine' object has no attribute 'all'`）

### 5回目: event_loopフィクスチャ修正後
- **修正内容**: event_loopフィクスチャのスコープをsessionからfunctionに変更
- **結果**: 67 failed, 125 passed
- **改善**: 非同期テストのエラーが大幅に減少
- **主な問題**:
  - トランザクションエラー（`Can't operate on closed transaction`）

### 6回目: async_sessionフィクスチャ修正後
- **修正内容**: async_sessionフィクスチャのトランザクション管理を修正
- **結果**: 52 failed, 140 passed
- **改善**: トランザクションエラーが解消

### 7回目: モック設定とDecimalエラー修正後
- **修正内容**: 
  - AsyncMockの返り値設定を修正
  - InvalidOperationのインポート追加
- **結果**: 50 failed, 142 passed

### 8回目: 最終実行
- **修正内容**: 
  - モックのexecuteメソッドの返り値を適切に設定
  - decimal.InvalidOperationの例外処理を修正
- **結果**: 47 failed, 145 passed
- **成功率**: 約75.5%

## エラーパターンの変遷

1. **初期段階（192 errors）**
   - 環境設定の問題が主

2. **中期段階（95 failed）**
   - 環境問題は解決
   - テストコード自体の問題が顕在化

3. **現在（47 failed）**
   - 基本的な問題は解決
   - 個別のビジネスロジックやAPIの問題が残る

## 残存エラーの分類

1. **APIバリデーション（約15件）**
   - 400 Bad Request
   - リクエストボディの形式問題

2. **サーバーエラー（約10件）**
   - 500 Internal Server Error
   - データベース関連

3. **非同期処理（約10件）**
   - Task pending エラー
   - 非同期の待機問題

4. **その他（約12件）**
   - モックの設定ミス
   - 個別のテストロジック問題