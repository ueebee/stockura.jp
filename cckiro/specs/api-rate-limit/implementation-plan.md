# 外部 API レートリミット機能の実装計画

## 実装順序

### 1. 基盤クラスの実装（infrastructure/rate_limiter/）
1. ディレクトリ構造の作成
2. `token_bucket.py` - トークンバケットアルゴリズム実装
3. `rate_limiter.py` - 汎用レートリミッター実装
4. `__init__.py` - パッケージ初期化

### 2. 設定クラスの拡張（infrastructure/config/）
1. `settings.py` に `RateLimitSettings` クラス追加
2. `InfrastructureSettings` に rate_limit フィールド追加
3. 環境変数の初期化処理追加

### 3. 各 API クライアントへの統合
1. `jquants/base_client.py` の修正
   - レートリミッターのインスタンス化
   - `_request_with_retry` メソッドへのデコレーター適用
2. `yfinance/base_client.py` の修正
   - レートリミッターのインスタンス化
   - 主要メソッドへのデコレーター適用

### 4. テストの実装
1. `tests/unit/infrastructure/rate_limiter/` ディレクトリ作成
2. `test_token_bucket.py` - TokenBucket クラスのテスト
3. `test_rate_limiter.py` - RateLimiter クラスのテスト
4. 既存テストの更新
   - `test_jquants_base_client.py` の更新
   - `test_yfinance_base_client.py` の作成/更新

## 各ファイルの実装内容

### 1. token_bucket.py
```python
# 実装項目：
- TokenBucket クラス
- capacity（最大トークン数）の管理
- トークンの補充ロジック（時間経過に基づく）
- acquire() メソッド（待機あり）
- try_acquire() メソッド（待機なし）
- 非同期ロックによる並行性制御
```

### 2. rate_limiter.py
```python
# 実装項目：
- RateLimiter クラス
- TokenBucket のラッパー
- ログ出力機能
- デコレーター関数 with_rate_limit()
```

### 3. settings.py の修正
```python
# 追加項目：
- RateLimitSettings クラス
- 環境変数のマッピング
- デフォルト値の設定
```

### 4. base_client.py の修正（J-Quants/yfinance）
```python
# 修正項目：
- __init__ メソッドでレートリミッター初期化
- リクエストメソッドへのデコレーター適用
- インポート文の追加
```

## テスト計画

### 単体テスト
1. **TokenBucket のテスト**
   - トークン消費のテスト
   - トークン補充のテスト
   - 待機時間の計算テスト
   - 並行アクセスのテスト

2. **RateLimiter のテスト**
   - 基本的な動作確認
   - ログ出力の確認
   - デコレーターの動作確認

### 統合テスト
1. **JQuantsBaseClient のテスト**
   - レート制限が適用されることの確認
   - 既存機能が正常に動作することの確認

2. **YfinanceBaseClient のテスト**
   - レート制限が適用されることの確認
   - 既存機能が正常に動作することの確認

## 実装時の注意点

1. **既存コードへの影響を最小限に**
   - デコレーターパターンを使用
   - 既存のメソッドシグネチャを変更しない
   - エラーハンドリングを変更しない

2. **非同期処理の考慮**
   - asyncio.Lock() を使用した排他制御
   - await を適切に使用
   - デッドロックを避ける

3. **ログ出力**
   - デバッグレベルで詳細情報
   - 警告レベルで待機発生の通知
   - パフォーマンスへの影響を最小限に

4. **テスト容易性**
   - 時間に依存する部分をモック可能に
   - 依存性注入を考慮した設計

## 完了条件

1. すべてのテストがパスする
2. 既存の機能に影響がない
3. ログでレート制限の動作が確認できる
4. 環境変数で設定が変更できる
5. コードレビューで承認を得る

## 実装予定時間

- 基盤クラスの実装: 2 時間
- 設定クラスの拡張: 30 分
- API クライアントへの統合: 1 時間
- テストの実装: 2 時間
- デバッグ・調整: 1 時間

合計: 約 6.5 時間