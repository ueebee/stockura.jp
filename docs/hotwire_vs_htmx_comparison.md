# Hotwire vs HTMX 比較分析

## 概要比較

### Hotwire
- **開発元**: Basecamp (DHH)
- **リリース**: 2020年12月
- **構成**: Turbo + Stimulus
- **エコシステム**: Rails中心
- **ファイルサイズ**: Turbo (~27KB) + Stimulus (~30KB) = 約57KB

### HTMX
- **開発元**: Big Sky Software
- **リリース**: 2020年（前身のintercooler.jsは2013年）
- **構成**: 単一ライブラリ
- **エコシステム**: 言語/フレームワーク非依存
- **ファイルサイズ**: 約14KB (gzipped)

## 機能比較

| 機能 | Hotwire | HTMX |
|------|---------|------|
| 部分的なHTML更新 | ✅ Turbo Frames | ✅ hx-target |
| ページ遷移の高速化 | ✅ Turbo Drive | ✅ hx-boost |
| WebSocket/SSE | ✅ Turbo Streams | ✅ SSE拡張 |
| フォーム処理 | ✅ | ✅ |
| 履歴管理 | ✅ 自動 | ✅ hx-push-url |
| プログレス表示 | ✅ 組み込み | ✅ hx-indicator |
| JavaScript連携 | ✅ Stimulus必須 | ⚠️ Alpine.js推奨 |

## 実装の違い

### Hotwire（Turbo）の例
```html
<!-- Turbo Frame -->
<turbo-frame id="messages">
  <a href="/messages/1">メッセージを表示</a>
</turbo-frame>

<!-- Turbo Stream (WebSocket) -->
<turbo-stream action="append" target="messages">
  <template>
    <div id="message_1">新しいメッセージ</div>
  </template>
</turbo-stream>

<!-- Stimulus連携 -->
<div data-controller="hello">
  <input data-hello-target="name" type="text">
  <button data-action="click->hello#greet">挨拶</button>
</div>
```

### HTMXの例
```html
<!-- 部分更新 -->
<div id="messages">
  <a href="/messages/1" 
     hx-get="/messages/1" 
     hx-target="#messages">
    メッセージを表示
  </a>
</div>

<!-- SSE (Server-Sent Events) -->
<div hx-ext="sse" 
     sse-connect="/messages/stream" 
     sse-swap="message">
</div>

<!-- Alpine.js連携（オプション） -->
<div x-data="{ name: '' }">
  <input x-model="name" type="text">
  <button @click="alert('Hello ' + name)">挨拶</button>
</div>
```

## FastAPIプロジェクトでHTMXを推奨する理由

### 1. **言語・フレームワーク非依存**
- **HTMX**: どんなバックエンドでも使用可能
- **Hotwire**: Rails向けに最適化、他では追加実装が必要

### 2. **シンプルさ**
- **HTMX**: HTML属性だけで完結、追加の概念が少ない
- **Hotwire**: Turbo Frame、Turbo Stream、Stimulusの概念理解が必要

### 3. **ファイルサイズ**
- **HTMX**: 14KB（単体で動作）
- **Hotwire**: 57KB以上（Turbo + Stimulus）

### 4. **Python/FastAPIサポート**
- **HTMX**: 
  - `fastapi-htmx`パッケージあり
  - 多数の実装例とコミュニティ
  - FastAPIの思想と相性が良い
- **Hotwire**: 
  - Python向けの公式サポートなし
  - 自前でTurbo Stream形式の実装が必要

### 5. **学習曲線**
- **HTMX**: 
  - HTML属性を覚えるだけ
  - 既存の知識で始められる
- **Hotwire**: 
  - Rails Way の理解が前提
  - Stimulusの学習が追加で必要

### 6. **拡張性**
```python
# HTMXはシンプルなレスポンスヘッダーで制御
@app.post("/items")
async def create_item(request: Request):
    # 処理...
    return HTMLResponse(
        content=html_fragment,
        headers={
            "HX-Trigger": "itemCreated",  # イベント発火
            "HX-Push-Url": "/items/123"   # URL更新
        }
    )

# Hotwireは特定のフォーマットが必要
# <turbo-stream>タグを含むHTMLを構築する必要がある
```

## それでもHotwireを選ぶ場合

### Hotwireが適している状況
1. **既存のRailsアプリ**からの移行
2. **Basecampスタイル**のUIを目指す
3. **Stimulusのコンポーネント**システムが必要
4. チーム内に**Rails経験者が多い**

### FastAPIでHotwireを使う場合の実装
```python
# カスタム実装が必要
class TurboStream:
    @staticmethod
    def append(target: str, content: str) -> str:
        return f'''
        <turbo-stream action="append" target="{target}">
          <template>{content}</template>
        </turbo-stream>
        '''

@app.websocket("/turbo-stream")
async def turbo_stream(websocket: WebSocket):
    await websocket.accept()
    # Turbo Stream形式で送信
    await websocket.send_text(
        TurboStream.append("messages", "<div>新着</div>")
    )
```

## 結論

### FastAPIプロジェクトには**HTMX**を推奨する理由：

1. **即座に使える** - 特別な設定不要
2. **コミュニティ** - FastAPI + HTMX の実績多数
3. **シンプル** - HTML属性だけで実装
4. **軽量** - 14KBで全機能
5. **柔軟** - 必要に応じてAlpine.jsなど追加可能

### ただし、以下の場合はHotwireも検討：
- Railsからの移行プロジェクト
- Stimulusのようなコンポーネントシステムが必須
- チームがRails/Hotwireに精通している

FastAPIの「シンプルで高速」という思想には、HTMXの方がより適合していると考えられます。