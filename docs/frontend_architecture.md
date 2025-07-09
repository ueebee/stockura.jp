# フロントエンドアーキテクチャ設計

## 技術スタック

### コア技術
- **FastAPI** - バックエンドAPI
- **HTMX** - HTMLドリブンなインタラクティブ機能
- **Jinja2** - サーバーサイドテンプレート
- **Alpine.js** - 軽量な状態管理（必要な箇所のみ）
- **Tailwind CSS + DaisyUI** - スタイリング

### なぜHTMXか？
- RailsのHotwireと同じ「HTML-over-the-wire」アプローチ
- JavaScriptの記述量を90%以上削減
- サーバーサイドでビジネスロジックを完結
- プログレッシブエンハンスメント対応

## ディレクトリ構造

```
stockura.jp/
├── app/
│   ├── templates/           # Jinja2テンプレート
│   │   ├── base.html       # ベースレイアウト
│   │   ├── layouts/        # レイアウトテンプレート
│   │   │   ├── dashboard.html
│   │   │   └── auth.html
│   │   ├── pages/          # ページテンプレート
│   │   │   ├── dashboard/
│   │   │   ├── data_sources/
│   │   │   ├── jobs/
│   │   │   └── analysis/
│   │   └── partials/       # HTMXで更新する部分テンプレート
│   │       ├── data_source_row.html
│   │       ├── job_status.html
│   │       └── notification.html
│   ├── static/             # 静的ファイル
│   │   ├── css/
│   │   │   └── main.css    # Tailwind CSS
│   │   ├── js/
│   │   │   ├── htmx.min.js
│   │   │   ├── alpine.min.js
│   │   │   └── app.js      # 最小限のカスタムJS
│   │   └── img/
│   └── views/              # ビューロジック（HTMXエンドポイント）
│       ├── dashboard.py
│       ├── data_sources.py
│       └── jobs.py
```

## 実装パターン

### 1. 基本的なHTMXパターン

```html
<!-- データソース一覧の自動更新 -->
<div id="data-sources-table" 
     hx-get="/api/v1/data-sources/table" 
     hx-trigger="every 5s">
    <!-- サーバーから返されるHTMLで更新 -->
</div>

<!-- フォーム送信 -->
<form hx-post="/api/v1/data-sources" 
      hx-target="#data-sources-table"
      hx-swap="innerHTML">
    <input name="name" type="text">
    <button type="submit">追加</button>
</form>
```

### 2. リアルタイム更新（SSE）

```html
<!-- ジョブ実行状況のリアルタイム監視 -->
<div hx-ext="sse" 
     sse-connect="/api/v1/jobs/stream"
     sse-swap="message">
    <div id="job-status">
        <!-- SSEで更新される -->
    </div>
</div>
```

### 3. モーダル・ダイアログ

```html
<!-- DaisyUIのモーダルをHTMXで制御 -->
<button hx-get="/api/v1/data-sources/new" 
        hx-target="#modal-content"
        onclick="document.getElementById('modal').showModal()">
    新規追加
</button>

<dialog id="modal" class="modal">
    <div id="modal-content">
        <!-- 動的にロード -->
    </div>
</dialog>
```

## API設計

### HTMXエンドポイント規約

```python
# views/data_sources.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

# ページ全体を返す
@router.get("/data-sources", response_class=HTMLResponse)
async def data_sources_page(request: Request):
    return templates.TemplateResponse(
        "pages/data_sources/index.html",
        {"request": request}
    )

# 部分HTMLを返す（HTMX用）
@router.get("/data-sources/table", response_class=HTMLResponse)
async def data_sources_table(request: Request):
    data_sources = await get_data_sources()
    return templates.TemplateResponse(
        "partials/data_source_table.html",
        {"request": request, "data_sources": data_sources}
    )

# フォーム処理
@router.post("/data-sources", response_class=HTMLResponse)
async def create_data_source(request: Request, form_data: DataSourceForm):
    # データ作成
    new_data_source = await create_data_source_in_db(form_data)
    
    # 成功時は部分HTMLを返す
    return templates.TemplateResponse(
        "partials/data_source_row.html",
        {"request": request, "data_source": new_data_source},
        headers={"HX-Trigger": "dataSourceCreated"}
    )
```

## スタイリング戦略

### Tailwind CSS + DaisyUI設定

```javascript
// tailwind.config.js
module.exports = {
  content: ["./app/templates/**/*.html"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark", "corporate"],
  },
}
```

### コンポーネント例

```html
<!-- データソースカード -->
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">
            J-Quants
            <div class="badge badge-success">有効</div>
        </h2>
        <p>最終同期: 2024-01-15 10:30</p>
        <div class="card-actions justify-end">
            <button class="btn btn-primary btn-sm"
                    hx-post="/api/v1/data-sources/jquants/sync"
                    hx-indicator="#sync-spinner">
                同期実行
            </button>
            <span id="sync-spinner" class="loading loading-spinner htmx-indicator"></span>
        </div>
    </div>
</div>
```

## 進化的な開発アプローチ

### Phase 1: 基本機能
- 静的なページレイアウト
- 基本的なCRUD操作
- シンプルなフォーム

### Phase 2: インタラクティブ機能
- リアルタイム更新（ポーリング）
- 動的なフォームバリデーション
- プログレス表示

### Phase 3: 高度な機能
- WebSocket/SSEによるリアルタイム通信
- チャート（Chart.jsを動的に初期化）
- ドラッグ&ドロップ（Alpine.js）

## メリット

1. **開発速度**: SPAより高速に開発可能
2. **保守性**: サーバーサイドにロジックが集中
3. **パフォーマンス**: 初期表示が高速
4. **SEO**: サーバーサイドレンダリング
5. **アクセシビリティ**: プログレッシブエンハンスメント