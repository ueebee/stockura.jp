# 認証機能の動作確認手順

このドキュメントでは、 Stockura アプリケーションの認証機能を手動で確認する手順を説明します。

## 前提条件

1. **アプリケーションの起動**
   ```bash
   # プロジェクトルートで実行
   uvicorn app.main:app --reload --port 8000
   ```

2. **Redis の起動**
   ```bash
   # Redis がローカルで動作していることを確認
   redis-cli ping
   # PONG が返ってくれば OK
   ```

3. **J-Quants アカウント**
   - J-Quants の有効なアカウント（メールアドレスとパスワード）が必要です
   - アカウントは[J-Quants 公式サイト](https://application.jpx-jquants.com/) で作成できます

## API エンドポイント

認証関連の API エンドポイントは以下の通りです：

- `POST /api/v1/auth/login` - ログイン
- `POST /api/v1/auth/refresh` - トークンの更新
- `GET /api/v1/auth/status/{email}` - 認証状態の確認
- `POST /api/v1/auth/logout` - ログアウト

## 動作確認手順

### 1. ログイン機能の確認

```bash
# J-Quants アカウントでログイン
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

**成功時のレスポンス例：**
```json
{
  "email": "your-email@example.com",
  "has_valid_token": true,
  "message": "ログインに成功しました"
}
```

**失敗時のレスポンス例：**
```json
{
  "detail": "Invalid email or password"
}
```

### 2. 認証状態の確認

```bash
# 認証状態を確認
curl -X GET "http://localhost:8000/api/v1/auth/status/your-email@example.com"
```

**レスポンス例：**
```json
{
  "email": "your-email@example.com",
  "authenticated": true,
  "has_valid_token": true,
  "needs_refresh": false
}
```

### 3. トークンの更新

ID トークンの有効期限が近づいている場合、リフレッシュトークンを使用して新しい ID トークンを取得します。

```bash
# トークンを更新
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com"
  }'
```

**成功時のレスポンス例：**
```json
{
  "email": "your-email@example.com",
  "has_valid_token": true,
  "message": "トークンの更新に成功しました"
}
```

### 4. ログアウト

```bash
# ログアウト（認証情報を Redis から削除）
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com"
  }'
```

**レスポンス例：**
```json
{
  "email": "your-email@example.com",
  "message": "ログアウトしました"
}
```

## 認証フローの詳細

1. **ログイン時の処理**
   - J-Quants API に対してメールアドレスとパスワードで認証
   - リフレッシュトークンと ID トークンを取得
   - 認証情報を Redis に保存（有効期限付き）

2. **トークンの管理**
   - ID トークンの有効期限は 24 時間
   - リフレッシュトークンの有効期限は 7 日間
   - ID トークンの有効期限が 1 時間を切ると`needs_refresh`が true になる

3. **Redis での認証情報管理**
   - キー形式: 
     - 認証情報メタデータ: `jquants:credentials:{email}`
     - リフレッシュトークン: `jquants:refresh_token:{email}`
     - ID トークン: `jquants:id_token:{email}`
   - TTL: 7 日間（リフレッシュトークンの有効期限に合わせて設定）

## トラブルシューティング

### 1. Redis に接続できない場合

```bash
# Redis の状態を確認
redis-cli ping

# Redis が起動していない場合は起動
# macOS
brew services start redis

# Linux
sudo systemctl start redis
```

### 2. 認証情報の確認

```bash
# Redis に保存されている認証情報を確認
redis-cli
> KEYS jquants:*
> GET jquants:credentials:your-email@example.com
> GET jquants:refresh_token:your-email@example.com
> GET jquants:id_token:your-email@example.com
```

### 3. ログの確認

アプリケーションログで認証処理の詳細を確認できます。
デバッグモードで起動している場合、より詳細なログが出力されます。

## 開発時の注意事項

1. **環境変数の設定**
   - `.env`ファイルに必要な環境変数を設定してください
   - 特に`REDIS_URL`が正しく設定されていることを確認

2. **CORS 設定**
   - フロントエンドから呼び出す場合は、`CORS_ORIGINS`に適切なオリジンを設定

3. **セキュリティ**
   - 本番環境では必ず HTTPS を使用してください
   - パスワードは平文で送信されるため、通信の暗号化が必須です

## Swagger UI での確認

ブラウザで以下の URL にアクセスすることで、 Swagger UI から認証 API を試すことができます：

```
http://localhost:8000/docs
```

Swagger UI では、各エンドポイントの詳細な仕様とリクエスト/レスポンスの例を確認できます。