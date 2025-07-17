# 日次株価データ取得機能 改善計画

## 1. 概要

日次株価データ取得機能に対する以下3つの改善を実施します：

1. **実行履歴へのパラメーター表示機能**
2. **相対的日付指定モード**
3. **定期実行機能**

## 2. 改善要件の詳細

### 2.1 実行履歴へのパラメーター表示

#### 現状
- 実行履歴には同期タイプ（incremental/full）のみ表示
- どの期間のデータを取得したかが履歴から確認できない

#### 改善内容
- 実行時のパラメーター（対象日、開始日、終了日など）を履歴に表示
- 同期履歴テーブルのデータを活用（既にDBには保存されている）

#### 表示例
```
実行日時: 2025-07-17 20:29:18
同期タイプ: full (期間指定)
パラメーター: 2024-07-10 〜 2025-07-14
ステータス: 完了
```

### 2.2 相対的日付指定モード

#### 現状
- 期間指定モードでは絶対的な日付（YYYY-MM-DD）のみ指定可能
- 毎回手動で日付を計算する必要がある

#### 改善内容
- 現在のJST時刻を基準とした相対的な日付指定を追加
- プリセットボタンまたはドロップダウンで選択可能に

#### 指定オプション例
- 過去7日間
- 過去30日間
- 過去90日間
- 過去1年間
- 今月のデータ
- 先月のデータ
- カスタム（従来の絶対日付指定）

### 2.3 定期実行機能

#### 現状
- 手動実行のみ
- 定期的なデータ取得には手動操作が必要

#### 改善内容
- Celery Beat（既に導入済み）を使用した定期実行
- 相対的日付指定と組み合わせて動的なスケジュール設定

#### 定期実行オプション例
- 毎日午前6時に前日のデータを取得（incremental）
- 毎週月曜日に過去7日間のデータを取得（full）
- 毎月1日に前月のデータを取得（full）

## 3. 技術的実装方針

### 3.1 実行履歴のパラメーター表示

#### 実装箇所
1. **バックエンド** (`/app/api/v1/endpoints/daily_quotes.py`)
   - 履歴取得APIのレスポンスにパラメーター情報を追加
   - DailyQuotesSyncHistoryモデルの既存フィールドを活用

2. **フロントエンド** (`/app/templates/partials/sync_history_rows.html`)
   - 履歴表示テンプレートにパラメーター列を追加
   - 同期タイプに応じて適切なパラメーターを表示

### 3.2 相対的日付指定モード

#### 実装箇所
1. **フロントエンド** (`/app/templates/partials/api_endpoints/endpoint_details_daily_quotes.html`)
   - 日付指定UI に相対指定オプションを追加
   - Alpine.jsで日付計算ロジックを実装

2. **JavaScript** (`/app/templates/base.html`)
   - dailyQuotesSyncManagerコンポーネントに相対日付計算機能を追加
   - プリセット選択時の日付自動設定

#### 実装例
```javascript
// 相対日付計算関数
calculateRelativeDate(preset) {
    const today = new Date();
    const jstToday = new Date(today.toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
    
    switch(preset) {
        case 'last7days':
            this.fromDate = this.addDays(jstToday, -7);
            this.toDate = this.addDays(jstToday, -1);
            break;
        // ... その他のプリセット
    }
}
```

### 3.3 定期実行機能

#### 実装箇所
1. **スケジュール設定画面** (新規作成)
   - `/app/templates/partials/api_endpoints/daily_quotes_schedule.html`
   - スケジュール設定フォーム

2. **バックエンド** (`/app/api/v1/endpoints/daily_quotes.py`)
   - スケジュール登録・更新・削除API
   - Celery Beatのdynamic schedule管理

3. **Celeryタスク** (`/app/tasks/daily_quotes_tasks.py`)
   - 相対日付を考慮したタスク実行ロジック

#### データベース設計
```python
class DailyQuotesSchedule(Base):
    __tablename__ = "daily_quotes_schedules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sync_type = Column(String, nullable=False)  # incremental/full
    relative_preset = Column(String)  # last7days, last30days, etc.
    cron_expression = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

## 4. 実装順序と工数見積もり

### Phase 1: 実行履歴のパラメーター表示（2-3時間）
1. バックエンドAPIの修正
2. フロントエンドテンプレートの更新
3. 動作確認

### Phase 2: 相対的日付指定モード（4-5時間）
1. UI設計とモックアップ作成
2. Alpine.jsコンポーネントの拡張
3. 日付計算ロジックの実装
4. UIの実装とスタイリング
5. 動作確認とテスト

### Phase 3: 定期実行機能（6-8時間）
1. データベーススキーマの設計
2. スケジュール管理APIの実装
3. 設定画面の実装
4. Celery Beat連携の実装
5. 統合テスト

## 5. リスクと注意事項

### 5.1 タイムゾーンの考慮
- 相対日付計算は必ずJSTで行う
- Celery BeatのスケジュールもJSTで設定
- データベースはUTCで保存、表示時にJST変換

### 5.2 パフォーマンスへの影響
- 定期実行による負荷を考慮
- 同時実行の制御（既に実行中の場合はスキップ）

### 5.3 エラーハンドリング
- 定期実行失敗時の通知機能
- リトライロジックの実装

## 6. 期待される効果

1. **運用効率の向上**
   - 手動操作の削減
   - 定期的なデータ取得の自動化

2. **ユーザビリティの向上**
   - 実行履歴の可視性向上
   - 日付指定の簡便化

3. **データの網羅性向上**
   - 定期実行により取得漏れを防止
   - 一貫したデータ取得パターンの確立

## 7. 将来の拡張性

1. **通知機能**
   - 定期実行の成功/失敗をメールやSlackで通知

2. **レポート機能**
   - 定期実行の統計情報をダッシュボードに表示

3. **条件付き実行**
   - 市場営業日のみ実行
   - 特定の条件（データ量など）での実行制御

---

作成日: 2025-07-17
作成者: Claude