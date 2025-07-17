# 日次株価データ取得のページネーション対応 改善計画

## 1. 問題の概要

### 現象
- 2024-11-27のデータ取得が不完全（1,700件/約4,400件 = 38.5%のみ）
- それ以前のデータは正常に取得できている（約4,311件）
- 明らかにページネーションの問題

### 原因
J-Quants APIは大量データの場合、ページネーション機能を使用してデータを分割して返す。現在の実装では、一部のコンポーネントでページネーションが考慮されていない可能性がある。

## 2. 現状分析

### 2.1 J-Quants API仕様
```python
# 初回リクエスト
response = requests.get("https://api.jquants.com/v1/prices/daily_quotes?date=2024-11-27", headers=headers)
data = response.json()["daily_quotes"]

# ページネーションがある場合
while "pagination_key" in response.json():
    pagination_key = response.json()["pagination_key"]
    response = requests.get(
        f"https://api.jquants.com/v1/prices/daily_quotes?date=2024-11-27&pagination_key={pagination_key}", 
        headers=headers
    )
    data += response.json()["daily_quotes"]
```

### 2.2 現在の実装状況

#### JQuantsクライアント（`app/services/jquants_client.py`）
- ❌ `get_stock_prices_by_date`メソッド: 
  - 全銘柄取得時（codes=None）: ✅ ページネーション対応済み
  - **特定銘柄指定時（codes指定）: ❌ ページネーション未対応** ← **問題箇所**
- ✅ `get_stock_prices_by_code`メソッド: ページネーション対応済み
- ✅ `get_daily_quotes`メソッド: `pagination_key`パラメータをサポート

#### DailyQuotesSyncService（`app/services/daily_quotes_sync_service.py`）
- ✅ `_sync_full_data`メソッド: `client.get_stock_prices_by_date(date_str)`を使用（全銘柄取得なので問題なし）
- ✅ `_sync_incremental_data`メソッド: `client.get_stock_prices_by_date(date_str)`を使用（全銘柄取得なので問題なし）
- ⚠️ `_sync_single_stock_data`メソッド: `client.get_stock_prices_by_date(date_str, codes=[code])`を使用（ページネーション未対応の処理を使用）

## 3. 調査計画

### 3.1 DailyQuotesSyncServiceの実装確認（完了）
- ✅ `_sync_full_data`メソッド: ページネーション対応のメソッドを使用していることを確認
- ✅ `_sync_incremental_data`メソッド: ページネーション対応のメソッドを使用していることを確認
- 結論: **コード実装上は問題なし**

### 3.2 問題の原因（特定完了）

**根本原因**: `get_stock_prices_by_date`メソッドの特定銘柄指定時にページネーション未対応

```python
# 問題のあるコード（app/services/jquants_client.py 337-344行目）
if codes:
    all_data = []
    for code in codes:
        response = await self.get_daily_quotes(code=code, date=date)
        if "daily_quotes" in response:
            all_data.extend(response["daily_quotes"])  # ページネーション考慮なし！
    return all_data
```

**なぜ2024-11-27で問題が発生したか？**
- 期間指定（full）モードでは全銘柄取得（ページネーション対応済み）を使用
- それにも関わらず1,700件（約38.5%）しか取得できていない
- 考えられる原因：
  1. APIのページネーション処理中にエラーが発生し、最初のページのみが処理された
  2. APIレスポンス自体が不完全だった（API側の問題）
  3. エラーハンドリングにより部分的なデータで処理が継続された

## 4. 改善計画

### 4.1 短期的な対応

1. **ログ機能の強化**（最優先）
   - ページネーション処理の詳細ログを追加
   - エラー発生時の詳細情報を記録
   - APIレスポンスの内容（pagination_keyの有無など）をログ出力

2. **エラーハンドリングの改善**
   - ページネーション処理中のエラーを適切に検知
   - 部分的なデータ取得を検出する仕組みを追加
   - 期待されるデータ件数との乖離を検証

3. **バグ修正**（発見した問題の修正）
   - `get_stock_prices_by_date`メソッドの特定銘柄指定時の処理にページネーション対応を追加（将来の問題を防ぐため）
   - 修正コード:
   ```python
   if codes:
       all_data = []
       for code in codes:
           pagination_key = None
           while True:
               response = await self.get_daily_quotes(
                   code=code, 
                   date=date,
                   pagination_key=pagination_key
               )
               if "daily_quotes" in response:
                   all_data.extend(response["daily_quotes"])
               
               pagination_key = response.get("pagination_key")
               if not pagination_key:
                   break
       return all_data
   ```

2. **問題のあるデータの再取得**（バグ修正後）
   - 2024-11-27のデータを再取得
   - 全銘柄（約4,400件）が取得できることを確認

3. **ログ機能の強化**（同時実装）
   - ページネーション処理の詳細ログ追加
   - 各ページで取得したデータ件数をログ出力

### 4.2 中長期的な対応
1. **監視機能の追加**
   - 日次のデータ取得件数を監視
   - 期待値（アクティブ企業数）と大幅に異なる場合はアラート

2. **ログの改善**
   - ページネーション処理の詳細ログ追加
   - 各ページで取得したデータ件数の記録

3. **エラーハンドリングの強化**
   - ページネーション中のエラーに対する再試行機能
   - 部分的な取得失敗時の復旧機能

## 5. リスクと対策

### リスク
1. 過去データの再取得により、APIレート制限に達する可能性
2. 大量データの処理によるメモリ使用量の増加
3. ページネーション処理の追加による処理時間の増加

### 対策
1. レート制限を考慮した処理間隔の調整
2. バッチ処理とメモリ管理の最適化
3. 非同期処理とプログレス表示の改善

## 6. 成功基準

1. 全ての日付で、アクティブ企業数の95%以上のデータが取得できること
2. ページネーション処理が正常に動作し、全ページのデータが取得できること
3. エラーログが出力されず、正常に処理が完了すること

## 7. タイムライン

- **Phase 1**（即時）: 問題の詳細調査と原因特定
- **Phase 2**（1日以内）: 修正の実装とテスト
- **Phase 3**（1週間以内）: 本番環境での動作確認と過去データの再取得
- **Phase 4**（2週間以内）: 監視機能の追加と長期的な改善

## 8. 具体的な実装提案

### 8.1 ログ強化とエラーハンドリングの実装案

```python
# app/services/jquants_client.py の get_stock_prices_by_date メソッドを改善
async def get_stock_prices_by_date(self, date: str, codes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    logger.info(f"Fetching stock prices for date: {date}")
    
    if codes:
        # 特定銘柄指定時もページネーション対応を追加
        all_data = []
        for code in codes:
            pagination_key = None
            code_data = []
            page_count = 0
            
            try:
                while True:
                    page_count += 1
                    response = await self.get_daily_quotes(
                        code=code,
                        date=date,
                        pagination_key=pagination_key
                    )
                    
                    if "daily_quotes" in response:
                        quotes = response["daily_quotes"]
                        code_data.extend(quotes)
                        logger.info(f"Code {code}, Page {page_count}: Retrieved {len(quotes)} quotes")
                    
                    pagination_key = response.get("pagination_key")
                    if not pagination_key:
                        break
                
                all_data.extend(code_data)
            except Exception as e:
                logger.error(f"Error fetching data for code {code}: {e}")
                # エラーが発生した場合は、その銘柄のデータ取得をスキップ
                continue
                
        return all_data
    else:
        # 全銘柄取得
        all_data = []
        pagination_key = None
        page_count = 0
        
        try:
            while True:
                page_count += 1
                logger.info(f"Fetching page {page_count} for date: {date}")
                
                response = await self.get_daily_quotes(
                    date=date,
                    pagination_key=pagination_key
                )
                
                # レスポンス内容の詳細ログ
                logger.info(f"API Response keys: {response.keys()}")
                
                if "daily_quotes" in response:
                    quotes = response["daily_quotes"]
                    all_data.extend(quotes)
                    logger.info(f"Page {page_count}: Retrieved {len(quotes)} quotes, total: {len(all_data)}")
                else:
                    logger.warning(f"No 'daily_quotes' in response for page {page_count}")
                
                # ページネーションキーの詳細ログ
                pagination_key = response.get("pagination_key")
                if pagination_key:
                    logger.info(f"Pagination key found: {pagination_key[:20]}... (truncated)")
                else:
                    logger.info(f"No more pages. Total pages: {page_count}")
                    break
                    
        except Exception as e:
            logger.error(f"Error during pagination for date {date}, page {page_count}: {e}")
            logger.error(f"Partial data retrieved: {len(all_data)} quotes")
            # エラーが発生しても、取得済みのデータは返す（ただし警告を出す）
            if len(all_data) < 1000:  # 明らかに少ない場合
                logger.error("Critical: Very few data retrieved, possible pagination failure")
        
        # データ検証を追加
        expected_min_count = 4000  # アクティブ企業数の約90%
        if len(all_data) < expected_min_count:
            logger.warning(f"Data validation failed: Retrieved only {len(all_data)} quotes for {date}, expected at least {expected_min_count}")
        
        logger.info(f"Total {len(all_data)} quotes retrieved for date: {date}")
        return all_data
```

### 8.2 エラーハンドリングの改善案

```python
# DailyQuotesSyncService の _sync_full_data メソッドに検証を追加
async def _sync_full_data(self, ...):
    # 既存の実装...
    
    while current_date <= to_date:
        try:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Processing date: {date_str}")
            
            quotes_data = await client.get_stock_prices_by_date(date_str)
            
            # データ件数の検証を追加
            active_companies_count = await self._get_active_companies_count(session)
            min_expected = int(active_companies_count * 0.9)  # 90%以上を期待
            
            if quotes_data and len(quotes_data) < min_expected:
                logger.error(
                    f"Insufficient data for {date_str}: got {len(quotes_data)}, "
                    f"expected at least {min_expected} (90% of {active_companies_count} active companies)"
                )
                # オプション: エラーとして扱うか、警告として継続するか
                # raise Exception(f"Insufficient data retrieved for {date_str}")
            
            # 既存の処理を続行...
```

### 8.3 監視機能の実装案

```python
# 新しいメソッドを追加
async def validate_daily_quotes_completeness(self, date: date) -> Dict[str, Any]:
    """
    指定日のデータ取得完全性を検証
    """
    async with async_session_maker() as session:
        # アクティブ企業数を取得
        active_companies = await self._get_active_companies_count(session)
        
        # 実際に取得されたデータ数を確認
        stmt = select(func.count(DailyQuote.id)).where(
            DailyQuote.trade_date == date
        )
        result = await session.execute(stmt)
        actual_count = result.scalar()
        
        completeness_rate = (actual_count / active_companies * 100) if active_companies > 0 else 0
        
        return {
            "date": date.isoformat(),
            "active_companies": active_companies,
            "actual_records": actual_count,
            "completeness_rate": f"{completeness_rate:.1f}%",
            "is_complete": completeness_rate >= 90.0,
            "missing_records": max(0, active_companies - actual_count)
        }
```

## 9. 次のアクション

1. **即時対応**
   - 2024-11-27のデータを手動で再取得し、問題が再現するか確認
   - 取得時のログを詳細に記録

2. **短期対応**
   - ログ強化の実装
   - エラーハンドリングの改善
   - データ完全性検証機能の追加

3. **中期対応**
   - 自動リトライ機能の実装
   - 監視ダッシュボードの構築
   - アラート機能の追加

---

作成日: 2025-07-17
更新日: 2025-07-17
作成者: Claude