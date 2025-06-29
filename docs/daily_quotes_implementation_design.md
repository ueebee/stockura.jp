# Daily Quotes データ取得機能 設計ドキュメント

## 概要

J-Quants API の daily_quotes エンドポイントから株価データを取得し、データベースに保存・管理する機能を実装します。既存の company データ管理システムのアーキテクチャを流用し、一貫性のある設計を採用します。

## システム構成

### 1. アーキテクチャ概要

```
[J-Quants API] 
    ↓
[JQuantsDailyQuotesClient] 
    ↓ 
[DailyQuotesSyncService] 
    ↓
[Database (daily_quotes table)]
    ↓
[REST API Endpoints]
```

### 2. 主要コンポーネント

#### 2.1 データベースモデル (`DailyQuote`)
- 株価データを格納するメインテーブル
- 企業コードと日付の複合主キー
- 調整前後の価格データを両方保存

#### 2.2 J-Quants クライアント拡張
- 既存の `JQuantsClientManager` を拡張
- daily_quotes専用クライアント `JQuantsDailyQuotesClient` を追加

#### 2.3 同期サービス (`DailyQuotesSyncService`)
- 株価データの取得と保存を管理
- バッチ処理とリアルタイム更新をサポート
- エラーハンドリングと再試行機能

#### 2.4 REST API エンドポイント
- 株価データの検索・取得API
- 同期実行・履歴管理API

#### 2.5 バックグラウンドタスク
- 定期的な株価データ同期
- 大量データの並列処理

## データベース設計

### 3.1 daily_quotes テーブル

```sql
CREATE TABLE daily_quotes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,                    -- 銘柄コード
    trade_date DATE NOT NULL,                     -- 取引日
    
    -- 調整前価格データ
    open_price DECIMAL(10,2),                     -- 始値
    high_price DECIMAL(10,2),                     -- 高値
    low_price DECIMAL(10,2),                      -- 安値
    close_price DECIMAL(10,2),                    -- 終値
    volume BIGINT,                                -- 取引高
    turnover_value BIGINT,                        -- 取引代金
    
    -- 調整後価格データ
    adjustment_factor DECIMAL(10,6) DEFAULT 1.0,  -- 調整係数
    adjustment_open DECIMAL(10,2),                -- 調整後始値
    adjustment_high DECIMAL(10,2),                -- 調整後高値
    adjustment_low DECIMAL(10,2),                 -- 調整後安値
    adjustment_close DECIMAL(10,2),               -- 調整後終値
    adjustment_volume BIGINT,                     -- 調整後取引高
    
    -- 制限フラグ
    upper_limit_flag BOOLEAN DEFAULT FALSE,       -- ストップ高フラグ
    lower_limit_flag BOOLEAN DEFAULT FALSE,       -- ストップ安フラグ
    
    -- Premium限定（将来拡張用）
    morning_open DECIMAL(10,2),                   -- 前場始値
    morning_high DECIMAL(10,2),                   -- 前場高値
    morning_low DECIMAL(10,2),                    -- 前場安値
    morning_close DECIMAL(10,2),                  -- 前場終値
    morning_volume BIGINT,                        -- 前場取引高
    morning_turnover_value BIGINT,                -- 前場取引代金
    
    afternoon_open DECIMAL(10,2),                 -- 後場始値
    afternoon_high DECIMAL(10,2),                 -- 後場高値
    afternoon_low DECIMAL(10,2),                  -- 後場安値
    afternoon_close DECIMAL(10,2),                -- 後場終値
    afternoon_volume BIGINT,                      -- 後場取引高
    afternoon_turnover_value BIGINT,              -- 後場取引代金
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 制約
    UNIQUE(code, trade_date),
    FOREIGN KEY (code) REFERENCES companies(code)
);

-- インデックス
CREATE INDEX idx_daily_quotes_code_date ON daily_quotes(code, trade_date DESC);
CREATE INDEX idx_daily_quotes_date ON daily_quotes(trade_date DESC);
CREATE INDEX idx_daily_quotes_code ON daily_quotes(code);
CREATE INDEX idx_daily_quotes_volume ON daily_quotes(volume DESC);
```

### 3.2 daily_quotes_sync_history テーブル

```sql
CREATE TABLE daily_quotes_sync_history (
    id SERIAL PRIMARY KEY,
    sync_date DATE NOT NULL,                      -- 同期対象日
    sync_type VARCHAR(20) NOT NULL,               -- full/incremental/single_stock
    status VARCHAR(20) NOT NULL,                  -- running/completed/failed
    
    -- 統計情報
    target_companies INT,                         -- 対象企業数
    total_records INT,                            -- 総レコード数
    new_records INT,                              -- 新規レコード数
    updated_records INT,                          -- 更新レコード数
    skipped_records INT,                          -- スキップレコード数
    
    -- 実行情報
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- 処理詳細
    from_date DATE,                               -- 処理開始日
    to_date DATE,                                 -- 処理終了日
    specific_codes TEXT[],                        -- 特定銘柄指定の場合
    
    INDEX(sync_date, status),
    INDEX(started_at)
);
```

## API 設計

### 4.1 エンドポイント一覧

#### 株価データ取得系

```python
# 特定銘柄の株価データ取得
GET /api/v1/daily-quotes/{code}
  ?from_date=2024-01-01
  &to_date=2024-01-31
  &limit=100
  &offset=0

# 複数銘柄の株価データ取得
GET /api/v1/daily-quotes
  ?codes=1301,1302,1303
  &date=2024-01-15
  &market_code=0111
  &sector17_code=1

# 特定日の全銘柄データ取得
GET /api/v1/daily-quotes/by-date/{date}
  ?limit=1000
  &offset=0
```

#### 同期管理系

```python
# 株価データ同期実行
POST /api/v1/daily-quotes/sync
{
  "sync_type": "full",           # full/incremental/single_stock
  "target_date": "2024-01-15",   # 対象日（任意）
  "from_date": "2024-01-01",     # 期間指定開始日（任意）
  "to_date": "2024-01-31",       # 期間指定終了日（任意）
  "codes": ["1301", "1302"]      # 特定銘柄（任意）
}

# 同期履歴取得
GET /api/v1/daily-quotes/sync/history
  ?limit=50
  &offset=0
  &status=completed

# 同期ステータス取得
GET /api/v1/daily-quotes/sync/status/{sync_id}
```

### 4.2 レスポンス形式

#### 株価データレスポンス

```json
{
  "data": [
    {
      "code": "1301",
      "trade_date": "2024-01-15",
      "open_price": 1000.0,
      "high_price": 1050.0,
      "low_price": 990.0,
      "close_price": 1030.0,
      "volume": 1500000,
      "turnover_value": 1545000000,
      "adjustment_factor": 1.0,
      "adjustment_open": 1000.0,
      "adjustment_high": 1050.0,
      "adjustment_low": 990.0,
      "adjustment_close": 1030.0,
      "adjustment_volume": 1500000,
      "upper_limit_flag": false,
      "lower_limit_flag": false
    }
  ],
  "pagination": {
    "total": 1000,
    "limit": 100,
    "offset": 0,
    "has_next": true
  }
}
```

## 実装コンポーネント

### 5.1 ファイル構成

```
app/
├── models/
│   └── daily_quote.py              # データベースモデル
├── schemas/
│   └── daily_quote.py              # Pydanticスキーマ
├── services/
│   ├── jquants_client.py           # 既存拡張（DailyQuotesClient追加）
│   └── daily_quotes_sync_service.py # 同期サービス
├── api/v1/endpoints/
│   └── daily_quotes.py             # APIエンドポイント
├── tasks/
│   └── daily_quotes_tasks.py       # Celeryタスク
└── alembic/versions/
    └── xxx_add_daily_quotes.py     # マイグレーション

tests/
├── test_models/
│   └── test_daily_quote.py
├── test_services/
│   └── test_daily_quotes_sync_service.py
├── test_api/
│   └── test_daily_quotes_api.py
└── test_tasks/
    └── test_daily_quotes_tasks.py
```

### 5.2 主要クラス設計

#### 5.2.1 JQuantsDailyQuotesClient

```python
class JQuantsDailyQuotesClient:
    """J-Quants daily_quotes APIクライアント"""
    
    async def get_daily_quotes(
        self,
        code: Optional[str] = None,
        date: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        pagination_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """株価データを取得"""
        
    async def get_stock_prices_by_code(
        self, 
        code: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """特定銘柄の株価データを取得"""
        
    async def get_stock_prices_by_date(
        self,
        date: str,
        codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """特定日の株価データを取得"""
```

#### 5.2.2 DailyQuotesSyncService

```python
class DailyQuotesSyncService:
    """株価データ同期サービス"""
    
    async def sync_daily_quotes(
        self,
        data_source_id: int,
        sync_type: str = "full",
        target_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        specific_codes: Optional[List[str]] = None
    ) -> DailyQuotesSyncHistory:
        """株価データの同期を実行"""
        
    async def sync_full_historical_data(
        self,
        data_source_id: int,
        from_date: date,
        to_date: date
    ) -> DailyQuotesSyncHistory:
        """指定期間の全株価データを同期"""
        
    async def sync_incremental_data(
        self,
        data_source_id: int,
        target_date: Optional[date] = None
    ) -> DailyQuotesSyncHistory:
        """増分データを同期"""
```

## データ処理戦略

### 6.1 同期戦略

#### 初回同期 (Full Sync)
1. 全上場企業リストを取得
2. 企業ごとに過去データを期間指定で取得
3. バッチ処理でデータベースに保存
4. エラー時は中断点から再開可能

#### 日次同期 (Incremental Sync)
1. 前営業日のデータを全銘柄で取得
2. 新規データのみ挿入
3. 既存データは更新（調整が入った場合）

#### リアルタイム同期
1. 特定銘柄の最新データを取得
2. WebSocket通知と連携可能

### 6.2 パフォーマンス最適化

#### データベース最適化
- パーティショニング（月別）
- 適切なインデックス設計
- バルクインサート使用

#### API呼び出し最適化
- レート制限遵守（J-Quants: 5000req/5min）
- 並列処理制御
- エラー時の指数バックオフ

#### メモリ最適化
- ストリーミング処理
- バッチサイズ調整
- 定期的なメモリクリア

## エラーハンドリング

### 7.1 API エラー処理

```python
# レート制限エラー
if response.status_code == 429:
    await asyncio.sleep(retry_after)
    return await self._retry_request()

# 認証エラー  
if response.status_code in [401, 403]:
    await self.refresh_token()
    return await self._retry_request()

# サーバーエラー
if response.status_code >= 500:
    await asyncio.sleep(exponential_backoff)
    return await self._retry_request()
```

### 7.2 データ整合性チェック

```python
def validate_daily_quote_data(self, data: Dict) -> bool:
    """株価データの整合性をチェック"""
    # 必須フィールドの存在確認
    # 数値範囲の妥当性チェック
    # 日付の妥当性チェック
    # 四本値の論理的整合性チェック
```

## セキュリティ考慮事項

### 8.1 APIアクセス制御
- JWT認証によるAPI保護
- レート制限の実装
- IPアドレス制限（必要に応じて）

### 8.2 データ保護
- 機密情報のログ出力禁止
- データベース接続の暗号化
- APIキーの安全な管理

## 監視・ログ

### 9.1 メトリクス
- 同期成功率
- API呼び出し回数/レスポンシ時間
- データ量統計
- エラー発生率

### 9.2 アラート
- 同期失敗時の通知
- API制限超過警告
- データ異常検知

## 実装スケジュール

### Phase 1: 基盤実装 (Week 1-2)
- [ ] データベースモデル作成
- [ ] マイグレーション実装
- [ ] J-Quants クライアント拡張

### Phase 2: 同期機能実装 (Week 3-4)
- [ ] 同期サービス実装
- [ ] バックグラウンドタスク実装
- [ ] エラーハンドリング実装

### Phase 3: API実装 (Week 5-6)
- [ ] REST API エンドポイント実装
- [ ] Pydantic スキーマ実装
- [ ] API ドキュメント作成

### Phase 4: テスト・最適化 (Week 7-8)
- [ ] 単体テスト実装
- [ ] 統合テスト実装
- [ ] パフォーマンス最適化
- [ ] 本番環境デプロイ

## 参考資料

- [J-Quants API Documentation](https://jpx.gitbook.io/j-quants-ja/)
- 既存 company 実装コード
- SQLAlchemy 2.0 Documentation
- FastAPI Documentation