# 定期実行を考慮したUI改善案

## 1. 現在の問題点

現在の表示：
- 「過去7日間」をクリック → 開始日: 2025-07-10、終了日: 2025-07-16

問題：
- これは**今実行した場合**の日付
- 明日実行される場合は実際には 2025-07-11 〜 2025-07-17 になる
- ユーザーは固定の日付だと誤解する可能性がある

## 2. 改善案

### 案1: 相対表現での表示（推奨）

```
期間選択: 過去7日間

期間設定: 実行日の前日から7日間遡る
（本日実行の場合: 2025-07-10 〜 2025-07-16）
```

### 案2: 動的プレビュー表示

```
期間選択: 過去7日間

実行タイミング別プレビュー:
- 本日実行: 2025-07-10 〜 2025-07-16
- 明日実行: 2025-07-11 〜 2025-07-17
```

### 案3: 説明文での表示

```
期間選択: 過去7日間

この設定は実行時に動的に計算されます。
実行日の前日を基準に、過去7日間のデータを取得します。
```

## 3. 実装提案

### 3.1 UI表示の改善

```html
<!-- 期間指定モードのパラメータ -->
<div x-show="syncMode === 'full'" x-transition class="space-y-4">
    <!-- 相対日付プリセット -->
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">期間選択</label>
        <div class="grid grid-cols-3 gap-2">
            <!-- プリセットボタン（既存） -->
        </div>
    </div>
    
    <!-- 日付表示エリアの改善 -->
    <div x-show="datePreset !== 'custom'" class="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div class="flex items-start">
            <svg class="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="text-sm text-blue-800">
                <p class="font-medium">動的期間設定</p>
                <p class="mt-1">実行時に自動的に計算されます：実行日の前日から
                    <span x-text="datePreset === 'last7days' ? '7日間' : 
                                  datePreset === 'last30days' ? '30日間' : 
                                  datePreset === 'last90days' ? '90日間' : 
                                  datePreset === 'thisMonth' ? '今月1日から前日まで' : 
                                  datePreset === 'lastMonth' ? '先月全体' : ''"></span>
                </p>
                <p class="mt-1 text-xs">現在実行すると: 
                    <span x-text="fromDate"></span> 〜 <span x-text="toDate"></span>
                </p>
            </div>
        </div>
    </div>
    
    <!-- 既存の日付入力フィールド -->
    <div class="grid grid-cols-2 gap-4" x-show="datePreset === 'custom'">
        <!-- 既存のフィールド -->
    </div>
</div>
```

### 3.2 定期実行設定画面での表示案

```html
<!-- 定期実行設定時の表示 -->
<div class="space-y-4">
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">実行スケジュール</label>
        <select class="...">
            <option>毎日 午前6時</option>
            <option>毎週月曜日 午前6時</option>
            <option>毎月1日 午前6時</option>
        </select>
    </div>
    
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">取得期間</label>
        <select class="...">
            <option value="last7days">実行日から過去7日間</option>
            <option value="last30days">実行日から過去30日間</option>
            <option value="yesterday">前日のみ</option>
        </select>
    </div>
    
    <!-- 次回実行時の予測表示 -->
    <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
        <p class="text-sm font-medium text-gray-700">次回実行予定</p>
        <p class="text-sm text-gray-600 mt-1">2025年7月18日 6:00</p>
        <p class="text-sm text-gray-600">取得期間: 2025-07-11 〜 2025-07-17</p>
    </div>
</div>
```

## 4. 推奨実装

1. **手動実行時**: 現在の表示を維持しつつ、「現在実行すると」という文言を追加
2. **定期実行設定時**: 相対的な表現を使い、次回実行時の予測を表示
3. **共通**: アイコンと説明文で動的計算であることを明示

これにより、ユーザーは日付が動的に計算されることを理解しやすくなります。

---

作成日: 2025-07-17
作成者: Claude