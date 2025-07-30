# aiohttp セッションクローズエラー修正の実装計画

## 1. 実装概要
aiohttp セッションの適切なクローズ処理を実装し、「 Unclosed client session 」警告を解消します。

## 2. 実装手順

### Phase 1: 現状調査（5 分）
#### 1.1 影響ファイルの確認
- [ ] `app/infrastructure/redis/auth_repository_impl.py`の確認
- [ ] `app/infrastructure/jquants/auth_repository_impl.py`の確認
- [ ] 同様のパターンを使用している他のファイルの調査

### Phase 2: RedisAuthRepository の修正（20 分）
#### 2.1 必要なインポートの追加
```python
import asyncio
import aiohttp
```

#### 2.2 get_refresh_token メソッドの修正
- [ ] TCPConnector の設定追加
- [ ] タイムアウト設定の追加
- [ ] 明示的なクローズ処理の追加
- [ ] エラーハンドリングの改善

#### 2.3 get_id_token メソッドの修正
- [ ] 同様の修正を適用
- [ ] コードの一貫性を保つ

### Phase 3: JQuantsAuthRepository の修正（15 分）
#### 3.1 同様の問題がある場合の修正
- [ ] get_refresh_token メソッドの修正
- [ ] get_id_token メソッドの修正

### Phase 4: テストと検証（20 分）
#### 4.1 単体テストの作成・更新
- [ ] セッションクローズのテスト
- [ ] エラー時のクリーンアップテスト

#### 4.2 Docker 環境での動作確認
- [ ] Celery ワーカーの再起動
- [ ] タスク実行とログ確認
- [ ] 警告メッセージが出ないことを確認

### Phase 5: ドキュメント更新（10 分）
#### 5.1 progress.md の作成・更新
- [ ] 実装の進捗を記録
- [ ] 問題と解決策の記録

## 3. 実装の詳細

### 3.1 修正後の get_refresh_token メソッド
```python
async def get_refresh_token(
    self, email: str, password: str
) -> Optional[RefreshToken]:
    """メールアドレスとパスワードからリフレッシュトークンを取得"""
    # TCP コネクターの設定
    connector = aiohttp.TCPConnector(
        force_close=True,  # 接続を強制的にクローズ
        limit=100,         # 接続数の制限
        ttl_dns_cache=300  # DNS キャッシュの TTL
    )
    
    # タイムアウトの設定
    timeout = aiohttp.ClientTimeout(
        total=30,      # 全体のタイムアウト
        connect=10,    # 接続タイムアウト
        sock_read=10   # 読み取りタイムアウト
    )
    
    session = None
    try:
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        payload = {"mailaddress": email, "password": password}
        
        async with session.post(
            f"{self.BASE_URL}{self.REFRESH_TOKEN_ENDPOINT}",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status == 200:
                data = await response.json()
                return RefreshToken(value=data["refreshToken"])
            elif response.status == 400:
                raise AuthenticationError("メールアドレスまたはパスワードが正しくありません。")
            else:
                raise AuthenticationError(
                    f"認証エラーが発生しました。ステータスコード: {response.status}"
                )
                
    except aiohttp.ClientError as e:
        raise NetworkError(f"ネットワークエラーが発生しました: {str(e)}")
    except (KeyError, json.JSONDecodeError) as e:
        raise AuthenticationError(f"レスポンスの解析に失敗しました: {str(e)}")
    finally:
        # セッションを確実にクローズ
        if session:
            await session.close()
            # TCP コネクションが完全にクローズされるまで少し待つ
            await asyncio.sleep(0.1)
```

### 3.2 共通のセッション作成関数（オプション）
```python
def _create_session(self) -> aiohttp.ClientSession:
    """共通のセッション設定を持つ ClientSession を作成"""
    connector = aiohttp.TCPConnector(
        force_close=True,
        limit=100,
        ttl_dns_cache=300
    )
    
    timeout = aiohttp.ClientTimeout(
        total=30,
        connect=10,
        sock_read=10
    )
    
    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    )
```

## 4. リスクと対策

### 4.1 パフォーマンスへの影響
- **リスク**: セッション作成・破棄のオーバーヘッド
- **対策**: 必要に応じてセッションプールの検討（将来的な改善）

### 4.2 互換性の問題
- **リスク**: 既存の動作への影響
- **対策**: 外部インターフェースは変更せず、内部実装のみ修正

### 4.3 エラーハンドリング
- **リスク**: セッションクローズ時のエラー
- **対策**: finally ブロックで確実にクローズし、エラーはログ記録のみ

## 5. 検証項目

### 5.1 機能検証
- [ ] J-Quants API への認証が正常に動作
- [ ] トークン取得が成功
- [ ] エラー時の適切なエラーメッセージ

### 5.2 リソース検証
- [ ] 「 Unclosed client session 」警告が出ない
- [ ] メモリリークが発生しない
- [ ] 長時間実行での安定性

### 5.3 パフォーマンス検証
- [ ] レスポンスタイムの大幅な劣化がない
- [ ] 並行実行時の問題がない

## 6. 総作業時間見積もり
- Phase 1: 5 分
- Phase 2: 20 分
- Phase 3: 15 分
- Phase 4: 20 分
- Phase 5: 10 分
- **合計**: 約 70 分（1 時間 10 分）