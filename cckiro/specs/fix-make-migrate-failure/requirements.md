# make migrate 失敗の修正要件

## 1. 問題の概要

`make migrate upgrade` コマンドを実行すると以下のエラーが発生する：

```
(sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedTableError'>: table "weekly_margin_interests" does not exist
[SQL: 
DROP TABLE weekly_margin_interests]
```

## 2. 問題の原因

マイグレーションファイルでテーブル名に不一致がある：

- マイグレーション `a6c57c53eda3` では `weekly_margin_interest` テーブル（単数形）を作成
- マイグレーション `0bd55ee18e0a` では `weekly_margin_interests` テーブル（複数形）を削除しようとしている

## 3. 修正要件

### 3.1 必須要件

1. **テーブル名の一貫性を保つ**
   - マイグレーションファイル間でテーブル名を統一する
   - 単数形 `weekly_margin_interest` に統一する

2. **既存のマイグレーションを修正**
   - `0bd55ee18e0a_remove_trades_spec_weekly_margin_.py` のテーブル名を修正
   - 削除対象のテーブル名を `weekly_margin_interests` から `weekly_margin_interest` に変更

3. **エラーなくマイグレーションが実行できること**
   - `make migrate upgrade` が正常に完了すること
   - データベーススキーマの整合性が保たれること

### 3.2 確認項目

1. 修正後に `make migrate current` で現在の状態を確認できること
2. 修正後に `make migrate upgrade` が正常に実行されること
3. 他の関連するコードに影響がないこと

## 4. 制約事項

1. 既存のマイグレーションヒストリーとの整合性を保つ必要がある
2. 本番環境への影響を最小限に抑える必要がある
3. ロールバック可能な修正であること

## 5. 成功基準

1. `make migrate upgrade` コマンドが正常に完了する
2. すべてのマイグレーションが適用される
3. データベーススキーマが意図した状態になっている