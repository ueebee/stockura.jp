# make migrate 失敗の修正実装計画

## 1. 実装手順

### Step 1: マイグレーションファイルのバックアップ
**目的**: 万が一の修正ミスに備える
```bash
cp alembic/versions/0bd55ee18e0a_remove_trades_spec_weekly_margin_.py \
   alembic/versions/0bd55ee18e0a_remove_trades_spec_weekly_margin_.py.backup
```

### Step 2: マイグレーションファイルの修正
**対象ファイル**: `alembic/versions/0bd55ee18e0a_remove_trades_spec_weekly_margin_.py`

#### 2.1 upgrade 関数の修正（26 行目）
```python
# 修正前
op.drop_table("weekly_margin_interests")

# 修正後  
op.drop_table("weekly_margin_interest")
```

#### 2.2 downgrade 関数の修正（50-67 行目）
テーブル名とインデックス名を全て単数形に変更：

```python
# テーブル作成部分（50 行目）
op.create_table(
    "weekly_margin_interest",  # 単数形に修正
    # ... カラム定義は変更なし ...
)

# インデックス作成部分（64-67 行目）
op.create_index("idx_weekly_margin_interest_code", "weekly_margin_interest", ["code"], unique=False)
op.create_index("idx_weekly_margin_interest_date", "weekly_margin_interest", ["date"], unique=False)
op.create_index("idx_weekly_margin_interest_date_issue_type", "weekly_margin_interest", ["date", "issue_type"], unique=False)
op.create_index("idx_weekly_margin_interest_issue_type", "weekly_margin_interest", ["issue_type"], unique=False)
```

### Step 3: 動作確認
1. **現在の状態確認**
   ```bash
   make migrate current
   ```

2. **マイグレーション実行**
   ```bash
   make migrate upgrade
   ```

3. **最終状態確認**
   ```bash
   make migrate current
   ```

### Step 4: エラーチェック
- エラーが発生した場合は、エラーメッセージを記録
- 必要に応じてロールバック

## 2. 実装時の注意事項

### 2.1 コーディング規約
- インデントはスペース 4 つ
- 既存のコードスタイルに合わせる
- 不要なコメントは追加しない

### 2.2 エラーハンドリング
- マイグレーション実行時のエラーは詳細にログを確認
- データベース接続エラーの場合は、 Docker 環境が起動しているか確認

## 3. 検証項目

### 3.1 修正前の確認
- [ ] 現在のマイグレーション状態を記録
- [ ] エラーメッセージを再確認

### 3.2 修正後の確認
- [ ] マイグレーションが正常に完了
- [ ] すべてのテーブルが適切に削除された
- [ ] データベーススキーマが期待通りの状態

## 4. タイムライン

1. **バックアップ作成**: 1 分
2. **ファイル修正**: 5 分
3. **動作確認**: 3 分
4. **文書更新**: 2 分

**合計所要時間**: 約 11 分

## 5. リスク管理

### 5.1 想定されるリスク
- マイグレーションファイルの構文エラー
- データベース接続の問題
- 他の開発者との競合

### 5.2 対応策
- バックアップファイルからの復元
- Docker 環境の再起動
- Git 操作での変更の取り消し

## 6. 完了基準

1. `make migrate upgrade` が正常に終了する
2. エラーメッセージが表示されない
3. `make migrate current` で最新のマイグレーションが適用されている
4. progress.md に実装完了を記録する