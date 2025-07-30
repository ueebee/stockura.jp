# aiohttp セッションクローズエラー修正の設計書

## 1. 設計概要
aiohttp の ClientSession が適切にクローズされていない問題を解決するため、コンテキストマネージャーパターンを適用し、セッションのライフサイクル管理を改善します。

## 2. 問題分析
### 2.1 現在の実装の問題点
- `RedisAuthRepository`の`get_refresh_token`と`get_id_token`メソッドで`async with`を使用しているが、セッションが正しくクローズされていない
- 問題の根本原因：
  - Celery ワーカーのフォークプロセスモデルと asyncio イベントループの相互作用
  - 複数のセッションが同時に作成され、一部が適切にクリーンアップされない

### 2.2 影響範囲
- `app/infrastructure/redis/auth_repository_impl.py`
- `app/infrastructure/jquants/auth_repository_impl.py`（同様の実装がある場合）

## 3. 設計方針
### 3.1 基本方針
1. **明示的なセッション管理**: セッションのライフサイクルを明確にする
2. **エラーセーフ**: 例外発生時も確実にクリーンアップ
3. **最小限の変更**: 既存のインターフェースを保持

### 3.2 解決アプローチ
1. **セッション管理の改善**
   - `async with`ブロックを適切に使用
   - セッションクローズを確実に実行
   - タイムアウト設定の追加

2. **リソース管理**
   - コンテキストマネージャーの適切な使用
   - 明示的なクリーンアップ処理

## 4. 詳細設計
### 4.1 セッション管理クラスの導入
```python
class ManagedClientSession:
    """管理された aiohttp クライアントセッション"""
    
    def __init__(self, **kwargs):
        self._session_kwargs = kwargs
        self._session = None
    
    async def __aenter__(self):
        self._session = ClientSession(**self._session_kwargs)
        return self._session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            # 小さな遅延を入れて接続が確実にクローズされるのを待つ
            await asyncio.sleep(0)
```

### 4.2 既存メソッドの修正
#### 4.2.1 get_refresh_token メソッド
```python
async def get_refresh_token(self, email: str, password: str) -> Optional[RefreshToken]:
    """メールアドレスとパスワードからリフレッシュトークンを取得"""
    connector = aiohttp.TCPConnector(force_close=True)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with ClientSession(connector=connector, timeout=timeout) as session:
        try:
            payload = {"mailaddress": email, "password": password}
            
            async with session.post(
                f"{self.BASE_URL}{self.REFRESH_TOKEN_ENDPOINT}",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                # レスポンス処理...
                
        except ClientError as e:
            raise NetworkError(f"ネットワークエラーが発生しました: {str(e)}")
        finally:
            # セッションが確実にクローズされることを保証
            await session.close()
```

### 4.3 エラーハンドリングの強化
- セッションクローズ時のエラーをキャッチし、ログに記録
- メインの処理に影響を与えないようにする

## 5. 実装の影響
### 5.1 パフォーマンスへの影響
- セッションの作成・破棄によるわずかなオーバーヘッド
- タイムアウト設定により、ハングする可能性を低減

### 5.2 互換性
- 外部インターフェースは変更なし
- 内部実装のみの修正

## 6. テスト計画
### 6.1 単体テスト
- セッションが正常にクローズされることを確認
- 例外発生時のクリーンアップを検証

### 6.2 統合テスト
- Celery タスク実行時の動作確認
- 長時間実行時のリソースリーク確認

## 7. 代替案の検討
### 7.1 セッションプールの使用
- 利点：パフォーマンス向上
- 欠点：実装の複雑性、 Celery ワーカーとの相性

### 7.2 グローバルセッションの使用
- 利点：シンプル
- 欠点：フォークプロセスモデルでの問題

## 8. 決定事項
- 各リクエストごとに新しいセッションを作成・破棄する方式を採用
- `force_close=True`オプションで TCP 接続を確実にクローズ
- タイムアウト設定で無限待機を防止