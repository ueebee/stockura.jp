# 相対的日付指定モード実装計画

## 1. 実装概要

期間指定モードにおいて、現在のJST時刻を基準とした相対的な日付指定機能を追加します。プリセットボタンまたはドロップダウンで簡単に期間を選択できるようにします。

## 2. UI設計

### 2.1 レイアウト案

```
期間指定モード
├── 相対日付プリセット（新規追加）
│   ├── 過去7日間
│   ├── 過去30日間
│   ├── 過去90日間
│   ├── 今月
│   ├── 先月
│   └── カスタム（手動入力）
│
└── 日付入力フィールド（既存）
    ├── 開始日
    └── 終了日
```

### 2.2 実装方法

1. **プリセットボタングループ**を期間指定モードのセクションに追加
2. 各プリセットを選択すると、自動的に開始日・終了日が設定される
3. 「カスタム」を選択した場合は、手動で日付を入力可能

## 3. 技術実装詳細

### 3.1 Alpine.jsコンポーネントの拡張

```javascript
// 追加するデータプロパティ
datePreset: 'custom', // デフォルトはカスタム

// 追加するメソッド
selectDatePreset(preset) {
    this.datePreset = preset;
    
    // 現在のJST日時を取得
    const now = new Date();
    const jstNow = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
    
    // 昨日のJST日付を基準とする（当日のデータは通常まだ存在しないため）
    const yesterday = new Date(jstNow);
    yesterday.setDate(yesterday.getDate() - 1);
    
    switch(preset) {
        case 'last7days':
            this.fromDate = this.addDays(yesterday, -6).toISOString().split('T')[0];
            this.toDate = yesterday.toISOString().split('T')[0];
            break;
        case 'last30days':
            this.fromDate = this.addDays(yesterday, -29).toISOString().split('T')[0];
            this.toDate = yesterday.toISOString().split('T')[0];
            break;
        case 'last90days':
            this.fromDate = this.addDays(yesterday, -89).toISOString().split('T')[0];
            this.toDate = yesterday.toISOString().split('T')[0];
            break;
        case 'thisMonth':
            const firstDayOfMonth = new Date(jstNow.getFullYear(), jstNow.getMonth(), 1);
            this.fromDate = firstDayOfMonth.toISOString().split('T')[0];
            this.toDate = yesterday.toISOString().split('T')[0];
            break;
        case 'lastMonth':
            const firstDayOfLastMonth = new Date(jstNow.getFullYear(), jstNow.getMonth() - 1, 1);
            const lastDayOfLastMonth = new Date(jstNow.getFullYear(), jstNow.getMonth(), 0);
            this.fromDate = firstDayOfLastMonth.toISOString().split('T')[0];
            this.toDate = lastDayOfLastMonth.toISOString().split('T')[0];
            break;
        case 'custom':
            // 手動入力モード - 日付は変更しない
            break;
    }
},

// ユーティリティメソッド
addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}
```

### 3.2 UIコンポーネント

```html
<!-- 相対日付プリセット -->
<div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-2">期間選択</label>
    <div class="grid grid-cols-3 gap-2">
        <button type="button"
                @click="selectDatePreset('last7days')"
                :class="{'bg-blue-50 border-blue-500 text-blue-700': datePreset === 'last7days', 'bg-white border-gray-300 text-gray-700': datePreset !== 'last7days'}"
                class="px-3 py-2 border rounded-md text-sm font-medium transition-colors hover:bg-gray-50">
            過去7日間
        </button>
        <!-- 他のプリセットボタン -->
    </div>
</div>
```

## 4. 実装手順

1. **Alpine.jsコンポーネントの更新**
   - `datePreset`プロパティの追加
   - `selectDatePreset()`メソッドの実装
   - `addDays()`ユーティリティメソッドの実装

2. **HTMLテンプレートの更新**
   - プリセットボタングループの追加
   - 既存の日付入力フィールドとの統合

3. **動作確認**
   - 各プリセットが正しく日付を設定することを確認
   - JST時刻での計算が正しく行われることを確認
   - カスタムモードでの手動入力が機能することを確認

## 5. 注意事項

1. **タイムゾーン処理**
   - すべての日付計算はJSTで行う
   - ブラウザのローカルタイムゾーンに依存しない実装

2. **データの可用性**
   - 当日のデータは通常まだ存在しないため、昨日を基準とする
   - 休日・祝日の考慮は行わない（API側で処理）

3. **ユーザビリティ**
   - プリセット選択後も手動で日付を調整可能
   - 選択されたプリセットが視覚的に分かりやすい

---

作成日: 2025-07-17
作成者: Claude