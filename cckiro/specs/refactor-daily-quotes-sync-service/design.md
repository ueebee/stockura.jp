# DailyQuotesSyncService リファクタリング設計書

## 1. アーキテクチャ概要

### 1.1 全体構成
```
┌─────────────────────────────────────────────────────────────┐
│                    DailyQuotesSyncService                    │
│                     (メインサービス)                         │
├─────────────────────────────────────────────────────────────┤
│ - 同期処理の制御                                            │
│ - 履歴管理                                                  │
│ - エラーハンドリングの統括                                  │
└─────────────────┬───────────────┬──────────────┬───────────┘
                  │               │              │
                  ▼               ▼              ▼
    ┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
    │ DailyQuotes      │ │ DailyQuotes     │ │ DailyQuotes      │
    │ DataFetcher      │ │ DataMapper      │ │ Repository       │
    ├──────────────────┤ ├─────────────────┤ ├──────────────────┤
    │ - API通信        │ │ - データ検証    │ │ - DB操作         │
    │ - データ取得     │ │ - 型変換        │ │ - 一括処理       │
    │ - レート制限     │ │ - 整合性チェック│ │ - トランザクション│
    └──────────────────┘ └─────────────────┘ └──────────────────┘
```

### 1.2 レイヤー構成
1. **サービス層**: DailyQuotesSyncService（ビジネスロジック）
2. **データ取得層**: DailyQuotesDataFetcher（外部API通信）
3. **データ変換層**: DailyQuotesDataMapper（検証・変換）
4. **永続化層**: DailyQuotesRepository（データベース操作）

## 2. インターフェース設計

### 2.1 IDailyQuotesDataFetcher
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date

class IDailyQuotesDataFetcher(ABC):
    """日次株価データ取得インターフェース"""
    
    @abstractmethod
    async def fetch_quotes_by_date(
        self, 
        target_date: date,
        codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """指定日の株価データを取得"""
        pass
    
    @abstractmethod
    async def fetch_quotes_by_date_range(
        self,
        from_date: date,
        to_date: date,
        codes: Optional[List[str]] = None
    ) -> Dict[date, List[Dict[str, Any]]]:
        """日付範囲の株価データを取得"""
        pass
```

### 2.2 IDailyQuotesDataMapper
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

class IDailyQuotesDataMapper(ABC):
    """日次株価データマッピングインターフェース"""
    
    @abstractmethod
    def map_to_model(self, api_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """APIデータをモデル用にマッピング"""
        pass
    
    @abstractmethod
    def validate_quote_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """株価データの妥当性検証"""
        pass
    
    @abstractmethod
    def convert_price_fields(self, value: Any) -> Optional[Decimal]:
        """価格フィールドの安全な変換"""
        pass
```

### 2.3 IDailyQuotesRepository
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from app.models.daily_quote import DailyQuote

class IDailyQuotesRepository(ABC):
    """日次株価データリポジトリインターフェース"""
    
    @abstractmethod
    async def find_by_code_and_date(
        self, 
        code: str, 
        trade_date: date
    ) -> Optional[DailyQuote]:
        """銘柄コードと日付で検索"""
        pass
    
    @abstractmethod
    async def bulk_upsert(
        self, 
        quotes_data: List[Dict[str, Any]]
    ) -> Tuple[int, int, int]:
        """一括更新（新規、更新、スキップ件数を返す）"""
        pass
    
    @abstractmethod
    async def find_latest_date_by_code(self, code: str) -> Optional[date]:
        """銘柄の最新取引日を取得"""
        pass
    
    @abstractmethod
    async def check_company_exists(self, code: str) -> bool:
        """企業マスタに存在するか確認"""
        pass
    
    @abstractmethod
    async def get_active_company_codes(self) -> List[str]:
        """アクティブな企業コードリストを取得"""
        pass
    
    @abstractmethod
    async def commit_batch(self) -> None:
        """バッチコミット"""
        pass
```

## 3. コンポーネント詳細設計

### 3.1 DailyQuotesSyncService
**責務**
- 同期処理のオーケストレーション
- 同期履歴の管理
- エラーハンドリングの統括
- 同期タイプ（full/incremental/single_stock）の制御

**主要メソッド**
- `sync()`: エントリーポイント
- `_orchestrate_sync()`: 同期処理の調整
- `_create_sync_history()`: 履歴作成
- `_update_sync_history()`: 履歴更新

### 3.2 DailyQuotesDataFetcher
**責務**
- J-Quants APIとの通信
- レート制限の管理
- API認証の処理
- エラーリトライ

**実装詳細**
- JQuantsClientManagerを使用
- レート制限: 5000req/5min を考慮
- 非同期処理でAPI呼び出し
- タイムアウト設定: 30秒

### 3.3 DailyQuotesDataMapper
**責務**
- APIレスポンスのデータ検証
- 型変換（Decimal, int, bool）
- データの整合性チェック（OHLC妥当性）
- 欠損データの処理

**検証ルール**
- 必須フィールドの存在確認
- 日付フォーマットの検証
- 価格データの論理的整合性
- 数値データの範囲チェック

### 3.4 DailyQuotesRepository
**責務**
- データベースCRUD操作
- トランザクション管理
- 一括処理の最適化
- 企業マスタとの整合性確認

**実装詳細**
- Companyテーブルとの結合で企業存在確認
- 企業が存在しない株価データはスキップ
- アクティブな企業のみを対象とする

**パフォーマンス考慮**
- 100件ごとのバッチコミット
- bulk_insert_mappingsの使用
- インデックスを活用したクエリ
- 企業存在確認はキャッシュ可能

## 4. エラーハンドリング設計

### 4.1 エラー分類と処理方針
1. **API関連エラー**
   - 認証エラー: APIError(401)として即座に失敗
   - レート制限: RateLimitError、待機後リトライ
   - ネットワークエラー: 3回までリトライ

2. **データ検証エラー**
   - 個別データエラー: 警告ログ、処理継続
   - 必須データ欠損: DataValidationError、スキップ

3. **データベースエラー**
   - トランザクションエラー: ロールバック、再試行
   - 制約違反: 個別処理、統計に反映

### 4.2 エラーハンドラー統合
```python
# 既存のErrorHandlerクラスを活用
await ErrorHandler.handle_sync_error(
    error=e,
    service_name="DailyQuotesSyncService",
    context=context,
    db=session,
    sync_history_id=sync_history.id
)
```

## 5. データフロー

### 5.1 Full Sync
```
1. 日付範囲の決定（デフォルト: 過去1年）
2. 各日付についてループ
   a. DataFetcher: API呼び出し
   b. DataMapper: データ検証・変換
   c. Repository: 一括更新
   d. 100件ごとにコミット
3. 履歴更新・完了
```

### 5.2 Incremental Sync
```
1. 対象日の決定（デフォルト: 前営業日）
2. DataFetcher: 単一日付のAPI呼び出し
3. DataMapper: データ検証・変換
4. Repository: 一括更新
5. 履歴更新・完了
```

### 5.3 Single Stock Sync
```
1. 対象銘柄リストの検証
2. 各銘柄についてループ
   a. DataFetcher: 銘柄指定API呼び出し
   b. DataMapper: データ検証・変換
   c. Repository: 更新
3. 履歴更新・完了
```

## 6. 移行戦略

### 6.1 実装順序
1. インターフェース定義の作成
2. 各コンポーネントの実装
3. 新DailyQuotesSyncServiceの実装
4. 単体テストの作成
5. 統合テストの実施
6. 既存コードの置き換え

### 6.2 テスト戦略
- 各コンポーネントの単体テスト
- モックを使用した統合テスト
- 実データを使用したE2Eテスト
- パフォーマンステスト

## 7. 拡張性の考慮

### 7.1 将来の拡張ポイント
- 新しいデータソースの追加（Yahoo Finance等）
- リアルタイムデータの対応
- 分析機能の追加
- キャッシュ層の導入

### 7.2 プラグイン機構
- インターフェースベースの設計により、実装の差し替えが容易
- 設定ベースでのコンポーネント切り替え