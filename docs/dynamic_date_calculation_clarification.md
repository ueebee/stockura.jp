# 定期実行時の動的日付計算に関する説明

## 1. 現在の実装状況

### Phase 2で実装したもの
- **手動実行時**の相対日付プリセット選択UI
- プリセットを選択すると、**その時点で**日付を計算して入力フィールドに設定
- 計算された具体的な日付（例：2025-07-10 〜 2025-07-16）がAPIに送信される

### 定期実行で必要なもの
- プリセット名（例：`last7days`）を**保存**
- **実行時点で**動的に日付を計算
- 毎回異なる日付でAPIを呼び出す

## 2. 定期実行の動作例

### 例：「過去7日間」を毎日午前6時に実行

| 実行日 | 計算される期間 |
|--------|--------------|
| 2025-07-18 6:00 | 2025-07-11 〜 2025-07-17 |
| 2025-07-19 6:00 | 2025-07-12 〜 2025-07-18 |
| 2025-07-20 6:00 | 2025-07-13 〜 2025-07-19 |

## 3. Phase 3での実装内容

### 3.1 スケジュール保存時
```python
# スケジュール設定をDBに保存
schedule = DailyQuotesSchedule(
    name="過去7日間の日次更新",
    sync_type="full",
    relative_preset="last7days",  # プリセット名を保存
    cron_expression="0 6 * * *",   # 毎日午前6時
    is_active=True
)
```

### 3.2 Celeryタスク実行時
```python
async def execute_scheduled_sync(schedule_id: int):
    # スケジュール設定を取得
    schedule = await get_schedule(schedule_id)
    
    # 実行時点で日付を計算
    if schedule.relative_preset:
        from_date, to_date = calculate_dates_from_preset(
            schedule.relative_preset,
            base_date=datetime.now(JST)  # 実行時点の日時
        )
    
    # 計算された日付でデータ同期を実行
    await sync_daily_quotes(
        sync_type=schedule.sync_type,
        from_date=from_date,
        to_date=to_date
    )
```

### 3.3 日付計算関数
```python
def calculate_dates_from_preset(preset: str, base_date: datetime):
    """プリセット名から実行時点の日付を動的に計算"""
    yesterday = base_date - timedelta(days=1)
    
    if preset == "last7days":
        from_date = yesterday - timedelta(days=6)
        to_date = yesterday
    elif preset == "last30days":
        from_date = yesterday - timedelta(days=29)
        to_date = yesterday
    # ... 他のプリセット
    
    return from_date.date(), to_date.date()
```

## 4. 現在のPhase 2実装の活用

現在実装したUI機能は、Phase 3で以下のように活用されます：

1. **スケジュール作成画面**で、同じプリセットボタンを使用
2. 選択したプリセットの**名前**を保存（日付ではなく）
3. プレビュー機能で「今実行したらこの期間になります」を表示

## 5. まとめ

- **Phase 2（完了）**: 手動実行時の便利なUI機能
- **Phase 3（これから）**: 定期実行時の動的日付計算機能

Phase 2の実装は意図と異なるものではなく、Phase 3の基盤として正しく機能します。Phase 3では、プリセット名を保存し、実行時に動的に日付を計算する機能を追加します。

---

作成日: 2025-07-17
作成者: Claude