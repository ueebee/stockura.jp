# 画面実装進捗状況

## 概要
Stockura.jpプロジェクトの画面実装状況をまとめたドキュメントです。HTMXを使用したSPA風のUIを実装しています。

更新日: 2025-01-10 (APIエンドポイント管理画面の基本機能を実装)

## 実装済み画面

### 1. ホーム画面 (`/`)
- **ファイル**: `app/templates/home.html`
- **ステータス**: ⚠️ 空のファイル（未実装）
- **機能**: なし

### 2. ダッシュボード (`/dashboard`)
- **ファイル**: 
  - View: `app/api/v1/views/dashboard.py`
  - Template: `app/templates/pages/dashboard.html`
  - Partials: `app/templates/partials/dashboard/activity_list.html`
- **ステータス**: ✅ **完全実装済み**
- **機能**:
  - システム概要とリアルタイムステータス表示
  - データソース状態、本日の同期、エラー状況、データ件数のサマリーカード
  - データソース管理、ジョブモニター、株価分析へのクイックアクセス
  - 最新アクティビティのリアルタイム表示（HTMXで30秒ごとに更新）
  - グラデーション、シャドウ、アニメーションを使用したモダンなUI

### 3. データソース管理 (`/data-sources`)
- **ファイル**:
  - View: `app/api/v1/views/data_sources.py`
  - Template: `app/templates/pages/data_sources.html`
  - Partials: 
    - `app/templates/partials/data_sources/data_source_row.html`
    - `app/templates/partials/data_sources/data_source_table.html`
    - `app/templates/partials/data_sources/data_source_card.html`
- **ステータス**: ✅ **完全実装済み**
- **機能**:
  - 登録済みデータソースの一覧表示（J-Quants API、Yahoo Finance API）
  - データソース名、プロバイダー、APIバージョン、レート制限の表示
  - 有効/無効の切り替え機能（HTMXで即座に反映）
  - APIトークン管理とレート制限についての説明パネル
  - レスポンシブデザイン対応

### 4. APIエンドポイント管理 (`/data-sources/{id}/endpoints`)
- **ファイル**:
  - View: `app/api/v1/views/api_endpoints.py`
  - Template: `app/templates/pages/api_endpoints.html`
  - Partials:
    - `app/templates/partials/api_endpoints/endpoint_row.html`
    - `app/templates/partials/api_endpoints/endpoint_details.html`
    - `app/templates/partials/api_endpoints/execution_result.html`
- **ステータス**: ✅ **基本機能実装済み**（2025-01-10）
- **機能**:
  - データソースごとのAPIエンドポイント一覧表示
  - エンドポイント別の有効/無効切り替え（HTMXで即座に反映）
  - エンドポイント詳細情報の表示（クリックで展開）
  - パラメータ情報の表示（必須/オプション/デフォルト値）
  - レート制限とバッチサイズの表示
  - 初回アクセス時の自動エンドポイント作成
  - データソース種別（J-Quants/Yahoo Finance）に応じた適切なエンドポイント
- **未実装機能**:
  - エンドポイント固有パラメータの設定画面
  - 実行スケジュールの設定機能
  - 手動実行の実際のAPI呼び出し処理
  - 実行履歴の詳細表示

### 5. ジョブ管理 (`/jobs`)
- **ファイル**:
  - View: `app/api/v1/views/jobs.py`
  - Template: `app/templates/pages/jobs.html`
- **ステータス**: 🔨 スケルトンのみ（「準備中」表示）
- **機能**: 未実装

### 6. 分析画面 (`/analysis`)
- **ファイル**:
  - View: `app/api/v1/views/analysis.py`
  - Template: `app/templates/pages/analysis.html`
- **ステータス**: 🔨 スケルトンのみ（「準備中」表示）
- **機能**: 未実装

### 7. 設定画面 (`/settings`)
- **ファイル**:
  - View: `app/api/v1/views/settings.py`
  - Template: `app/templates/pages/settings.html`
- **ステータス**: 🔨 スケルトンのみ（「準備中」表示）
- **機能**: 未実装

## 未実装画面（計画中）

### 8. 企業一覧画面 (`/companies`)
- **ステータス**: 🔄 計画中
- **予定機能**:
  - 上場企業一覧表示
  - 検索・フィルタリング機能
  - 詳細情報へのリンク
  - ページネーション

### 9. 企業詳細画面 (`/companies/{code}`)
- **ステータス**: 🔄 計画中
- **予定機能**:
  - 企業基本情報表示
  - 業種・市場情報
  - 株価チャート
  - 関連ニュース

### 10. 株価データ画面 (`/daily-quotes`)
- **ステータス**: 🔄 計画中
- **予定機能**:
  - 日次株価データ一覧
  - チャート表示
  - データエクスポート
  - 期間選択機能

### 11. レポート画面 (`/reports`)
- **ステータス**: 🔄 計画中
- **予定機能**:
  - 定期レポート生成
  - カスタムレポート作成
  - PDFエクスポート
  - スケジューリング

### 12. ユーザー管理画面 (`/users`)
- **ステータス**: 🔄 計画中
- **予定機能**:
  - ユーザー一覧
  - 権限管理
  - アクセスログ
  - APIキー管理

### 13. システム監視画面 (`/monitoring`)
- **ステータス**: 🔄 計画中
- **予定機能**:
  - システムメトリクス
  - エラーログ
  - パフォーマンス監視
  - アラート設定

## 技術スタック

### フロントエンド
- **テンプレートエンジン**: Jinja2
- **UIフレームワーク**: TailwindCSS
- **動的更新**: HTMX
- **チャート**: Chart.js（予定）
- **アイコン**: Heroicons

### バックエンド
- **フレームワーク**: FastAPI
- **ビューレンダリング**: FastAPI + Jinja2Templates
- **静的ファイル**: FastAPI StaticFiles

## ディレクトリ構造

```
app/
├── api/
│   └── v1/
│       └── views/          # HTMXビューエンドポイント
│           ├── __init__.py
│           ├── dashboard.py
│           ├── data_sources.py
│           ├── jobs.py
│           ├── analysis.py
│           └── settings.py
├── templates/
│   ├── base.html          # ベーステンプレート
│   ├── home.html          # ホームページ
│   ├── pages/             # 各ページのテンプレート
│   │   ├── dashboard.html
│   │   ├── data_sources.html
│   │   ├── jobs.html
│   │   ├── analysis.html
│   │   └── settings.html
│   └── partials/          # 部分テンプレート（HTMX用）
│       └── dashboard/
│           └── activity_list.html
└── static/                # 静的ファイル
    ├── css/
    ├── js/
    └── images/
```

## 実装優先順位

### Phase 1（現在の状況）
1. ✅ 基本レイアウト・ナビゲーション
2. ✅ ダッシュボード（完全実装済み）
3. ✅ データソース管理（完全実装済み）
4. ✅ APIエンドポイント管理（基本機能実装済み）
5. 🔨 ジョブ管理（スケルトンのみ）
6. 🔨 分析画面（スケルトンのみ）
7. 🔨 設定画面（スケルトンのみ）

### Phase 2（次回実装予定）
1. 🔄 企業一覧画面
2. 🔄 企業詳細画面
3. 🔄 株価データ画面

### Phase 3（将来実装予定）
1. 📋 レポート画面
2. 📋 ユーザー管理画面
3. 📋 システム監視画面

## HTMX実装パターン

### 1. ページ遷移
```html
<a href="/dashboard" hx-get="/dashboard" hx-target="#main-content" hx-push-url="true">
    ダッシュボード
</a>
```

### 2. 部分更新
```html
<div hx-get="/dashboard/activity" hx-trigger="every 30s" hx-target="#activity-list">
    <!-- アクティビティリストが30秒ごとに更新される -->
</div>
```

### 3. フォーム送信
```html
<form hx-post="/api/v1/data-sources" hx-target="#result" hx-swap="innerHTML">
    <!-- フォーム内容 -->
</form>
```

## 今後の開発計画

### 短期目標（1-2週間）
1. Phase 1の未完成画面の実装
   - ✅ ~~データソース管理画面の完成~~ (2025-01-09完了)
   - ✅ ~~APIエンドポイント管理画面の基本実装~~ (2025-01-10完了)
   - APIエンドポイントパラメータ設定機能の追加
   - ジョブ管理画面の完成
   - 分析画面の完成
   - 設定画面の完成
2. 企業一覧画面の実装
   - 検索機能
   - フィルタリング
   - ページネーション

### 中期目標（1ヶ月）
1. 株価データ画面の実装
2. レポート機能の基本実装
3. データエクスポート機能

### 長期目標（3ヶ月）
1. ユーザー管理システム
2. 高度な分析機能
3. リアルタイムデータ更新
4. モバイル対応最適化

## 注意事項

1. **HTMX統合**: すべての画面でHTMXを使用してSPA風の動作を実現
2. **レスポンシブデザイン**: TailwindCSSを使用してモバイル対応
3. **パフォーマンス**: 部分更新により高速なユーザー体験を提供
4. **アクセシビリティ**: ARIA属性の適切な使用
5. **セキュリティ**: CSRFトークン、XSS対策の実装

## 関連ドキュメント

- [技術アーキテクチャ](./technical_architecture.md)
- [データベース設計](./database_schema_design.md)
- [API仕様](./api_specification.md)
- [テスト進捗レポート](./test_progress_report.md)