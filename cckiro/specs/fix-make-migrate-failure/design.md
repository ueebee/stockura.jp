# make migrate 失敗の修正設計

## 1. 詳細な問題分析

### 1.1 エラーの発生箇所

- **ファイル**: `alembic/versions/0bd55ee18e0a_remove_trades_spec_weekly_margin_.py`
- **行番号**: 26 行目
- **問題のコード**: `op.drop_table("weekly_margin_interests")`

### 1.2 テーブル名の変遷

1. **作成時** (`a6c57c53eda3_add_weekly_margin_interest_table.py`):
   - テーブル名: `weekly_margin_interest` (単数形)
   - 作成日: 2025-08-05

2. **削除時** (`0bd55ee18e0a_remove_trades_spec_weekly_margin_.py`):
   - テーブル名: `weekly_margin_interests` (複数形) ← エラーの原因
   - 作成日: 2025-08-07

### 1.3 downgrade 関数でのテーブル名

`0bd55ee18e0a` の downgrade 関数では、正しく `weekly_margin_interests` (複数形) でテーブルを再作成しているが、これは元のテーブル名と一致していない。

## 2. 解決策の設計

### 2.1 修正方針

- テーブル名を単数形 `weekly_margin_interest` に統一する
- `0bd55ee18e0a` マイグレーションファイルを修正する

### 2.2 具体的な修正内容

#### 2.2.1 upgrade 関数の修正

```python
def upgrade() -> None:
    """Upgrade schema."""
    # Drop tables
    op.drop_table("trades_spec")
    op.drop_table("weekly_margin_interest")  # 単数形に修正
    op.drop_table("announcements")
```

#### 2.2.2 downgrade 関数の修正

```python
def downgrade() -> None:
    """Downgrade schema."""
    # ... 他のテーブル作成コード ...
    
    # Re-create weekly_margin_interest table (単数形に修正)
    op.create_table(
        "weekly_margin_interest",  # 単数形に修正
        # ... カラム定義 ...
    )
    # インデックス名も単数形に修正
    op.create_index("idx_weekly_margin_interest_code", "weekly_margin_interest", ["code"], unique=False)
    op.create_index("idx_weekly_margin_interest_date", "weekly_margin_interest", ["date"], unique=False)
    op.create_index("idx_weekly_margin_interest_date_issue_type", "weekly_margin_interest", ["date", "issue_type"], unique=False)
    op.create_index("idx_weekly_margin_interest_issue_type", "weekly_margin_interest", ["issue_type"], unique=False)
```

## 3. 影響範囲の分析

### 3.1 影響を受けるファイル

- `alembic/versions/0bd55ee18e0a_remove_trades_spec_weekly_margin_.py` のみ

### 3.2 他のコンポーネントへの影響

- この修正はマイグレーションファイルのみの変更であり、アプリケーションコードには影響しない
- 既にテーブルが削除される予定なので、アプリケーション側での参照は既に削除されているはず

## 4. リスク評価

### 4.1 低リスク

- 開発環境でのマイグレーションエラーの修正のみ
- 本番環境にはまだ適用されていない可能性が高い

### 4.2 考慮事項

- 既にこのマイグレーションが本番環境で実行されている場合は、別の対応が必要
- 現在の環境では、まだマイグレーションが適用されていない状態

## 5. テスト方法

1. 修正後、`make migrate upgrade` を実行して正常に完了することを確認
2. `make migrate current` で最新のマイグレーションまで適用されていることを確認
3. `make migrate downgrade` でロールバックできることを確認（必要に応じて）

## 6. ロールバック計画

万が一問題が発生した場合：
1. git で変更を元に戻す
2. データベースを初期状態にリセット（`make migrate reset`）
3. 再度マイグレーションを実行