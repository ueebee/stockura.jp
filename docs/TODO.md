# TODO - 将来実装予定の機能

## 企業の有効/無効機能

### 概要
上場企業の有効/無効ステータスを管理し、無効化された企業の株価データ取得をスキップする機能。

### 実装済みの準備
- データベース: `Company`モデルに`is_active`フィールドが存在（デフォルト値: True）
- 企業同期サービス: J-Quantsから取得できなくなった企業は自動的に`is_active=False`に更新

### 必要な実装
1. **企業管理画面**
   - 企業一覧表示（is_activeステータス表示付き）
   - 個別企業の有効/無効トグル機能
   - フィルタリング機能（アクティブ/非アクティブ）

2. **日次株価同期の改善**
   - `daily_quotes_sync_service.py`で`is_active=True`の企業のみを対象にする
   - スケジュール実行時も同様の制限を適用

3. **APIエンドポイント**
   - 企業のis_activeステータスを更新するエンドポイント（PATCH /api/v1/companies/{company_id}）
   - 一括更新機能（複数企業の有効/無効切り替え）

4. **UI要素の復活**
   - エンドポイント一覧画面でのステータス表示
   - 詳細画面での有効/無効切り替えボタン

### 実装の影響
- 無効化された企業の株価データ取得をスキップすることで、API使用量の削減
- 同期処理の高速化
- より柔軟な企業データ管理

### 削除されたUI要素（参考）
- `/app/templates/partials/api_endpoints/endpoint_row.html`: ステータス列の表示
- `/app/templates/partials/api_endpoints/endpoint_details_companies.html`: 状態表示と有効化/無効化ボタン