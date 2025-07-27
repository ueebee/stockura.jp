# セキュリティ監査結果

実施日: 2025-07-27

## エグゼクティブサマリー

Stockura プロジェクトのセキュリティ監査を実施した結果、いくつかの重大な脆弱性を発見しました。特に認証情報の管理とアクセス制御に改善が必要です。

**セキュリティスコア**: 40/100 (要改善)  
**OWASP Top 10 準拠度**: 40%

## 🔴 重大なセキュリティ脆弱性 (Critical)

### 1. ハードコードされたシークレット
**OWASP A07: Identification and Authentication Failures**

#### 該当箇所
- ファイル: `app/core/config.py:91-92`
- 問題のコード:
  ```python
  secret_key: str = Field(
      default="your-secret-key-here-change-in-production",
  ```

#### リスク評価
- **CVSS スコア**: 9.8 (Critical)
- **影響**: JWT 署名の偽造が可能となり、認証システム全体が危険に晒される
- **攻撃難易度**: 低（ソースコードにアクセスできれば即座に悪用可能）

#### 修正方法
```python
# 環境変数から必須項目として読み込む
secret_key: str = Field(
    ...,  # 必須項目として定義
    description="Secret key for JWT signing - must be set in production"
)
```

### 2. テスト用認証情報の露出

#### 該当箇所
- ファイル: `.test_credentials.json`
- 内容:
  ```json
  {
    "email": "test@example.com",
    "password": "testpassword",
    "refresh_token": "test_refresh_token"
  }
  ```

#### リスク評価
- **CVSS スコア**: 8.5 (High)
- **影響**: 本番環境に誤ってデプロイされると認証情報が露出
- **攻撃難易度**: 低

#### 修正方法
1. `.gitignore`に追加
2. 環境変数またはシークレット管理システムを使用
3. テスト環境でもダミーデータを使用

## 🟠 高リスクの脆弱性 (High)

### 3. 過度に寛容な CORS 設定
**OWASP A05: Security Misconfiguration**

#### 該当箇所
- ファイル: `app/main.py:31`
- 問題のコード:
  ```python
  allow_origins=["*"],
  ```

#### リスク評価
- **CVSS スコア**: 7.5 (High)
- **影響**: すべてのオリジンからのリクエストを許可し、 CSRF 攻撃が可能
- **攻撃難易度**: 中

#### 修正方法
```python
# 設定ファイルから許可するオリジンを読み込む
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["https://example.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 4. パスワードの平文保存

#### 該当箇所
- ファイル: `app/infrastructure/jquants/auth_repository_impl.py:107`
- 問題のコード:
  ```python
  credentials_data = {
      "email": credentials.email,
      "password": credentials.password,  # 平文保存
  }
  ```

#### リスク評価
- **CVSS スコア**: 7.5 (High)
- **影響**: ファイルシステムへの不正アクセスで認証情報が漏洩
- **攻撃難易度**: 中

#### 修正方法
```python
# パスワードは保存せず、トークンのみを管理
credentials_data = {
    "email": credentials.email,
    "refresh_token": refresh_token,
    # パスワードは保存しない
}
```

## 🟡 中リスクの脆弱性 (Medium)

### 5. JWT 検証ミドルウェアの未実装

#### 問題
- API エンドポイントの認証保護が不完全
- トークンの有効性検証が各エンドポイントで個別実装

#### 修正方法
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.secret_key, 
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# 使用例
@router.get("/protected")
async def protected_route(current_user=Depends(verify_jwt_token)):
    return {"user": current_user}
```

### 6. レート制限の未実装
**OWASP A04: Insecure Design**

#### 問題
- 設定は存在するが実装されていない
- ブルートフォース攻撃や DoS 攻撃に脆弱

#### 修正方法
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    # ログイン処理
```

## 🟢 低リスクの観察事項 (Low)

### 7. エラーメッセージの情報漏洩

#### 問題
- スタックトレースや詳細なエラー情報が本番環境で表示される可能性

#### 修正方法
```python
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    if settings.debug:
        # 開発環境では詳細情報を返す
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    else:
        # 本番環境では一般的なメッセージのみ
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
```

### 8. セキュリティイベントのロギング不足

#### 問題
- 認証失敗、アクセス拒否等の重要なイベントが記録されていない

#### 修正方法
```python
# セキュリティイベントのロギング
async def log_security_event(
    event_type: str,
    user_id: Optional[str],
    ip_address: str,
    details: dict
):
    logger.warning(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        details=details,
        timestamp=datetime.utcnow()
    )
```

## 推奨されるセキュリティ対策

### 即時対応（24 時間以内）

1. **シークレットキーの環境変数化**
   ```bash
   export JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **CORS 設定の制限**
   ```python
   cors_origins: list[str] = Field(
       default=["http://localhost:3000"],
       description="Allowed CORS origins"
   )
   ```

3. **テスト認証情報ファイルの削除**
   ```bash
   echo ".test_credentials.json" >> .gitignore
   rm .test_credentials.json
   ```

### 短期対応（1 週間以内）

1. **認証ミドルウェアの実装**
2. **レート制限の導入**
3. **セキュリティヘッダーの追加**
   ```python
   from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
   from secure import SecureHeaders
   
   secure_headers = SecureHeaders()
   
   @app.middleware("http")
   async def set_secure_headers(request, call_next):
       response = await call_next(request)
       secure_headers.framework.fastapi(response)
       return response
   ```

### 中長期対応（1 ヶ月以内）

1. **Zero Trust アーキテクチャの採用**
   - すべてのリクエストを検証
   - 最小権限の原則の徹底
   - ネットワークセグメンテーション

2. **セキュリティテストの自動化**
   ```yaml
   # .github/workflows/security.yml
   - name: Run security scan
     run: |
       pip install safety bandit
       safety check
       bandit -r app/
   ```

3. **監査ログとモニタリング**
   - Sentry の設定強化
   - セキュリティイベントの追跡
   - 異常検知の実装

## セキュリティチェックリスト

### 認証・認可
- [ ] JWT 署名キーの環境変数化
- [ ] パスワードの暗号化保存
- [ ] セッション管理の実装
- [ ] 多要素認証の検討

### アクセス制御
- [ ] CORS 設定の制限
- [ ] レート制限の実装
- [ ] API キーの管理
- [ ] 権限ベースのアクセス制御

### データ保護
- [ ] 機密データの暗号化
- [ ] SQL インジェクション対策
- [ ] XSS 対策
- [ ] CSRF 対策

### 監視・ログ
- [ ] セキュリティイベントログ
- [ ] 異常検知システム
- [ ] インシデント対応計画
- [ ] 定期的な脆弱性スキャン

## 結論

現在のセキュリティ状態は改善が必要です。特に認証情報の管理とアクセス制御に関する脆弱性は早急に対処すべきです。提案された修正を段階的に実装することで、セキュリティポスチャーを大幅に改善できます。

次回の監査は、これらの修正実装後 1 ヶ月以内に実施することを推奨します。