# アーカイブされた SQL マイグレーション

このディレクトリには、 Alembic 導入前に使用していた SQL ベースのマイグレーションファイルが保存されています。

## アーカイブされたファイル

- `001_create_listed_info_table.sql` - listed_info テーブルの初期作成
- `001_rollback_listed_info_table.sql` - listed_info テーブルのロールバック
- `002_alter_listed_info_code_length.sql` - code カラムの長さ変更（4 文字）
- `003_alter_listed_info_code_length_10.sql` - code カラムの長さ変更（10 文字）

## 注意事項

これらのファイルは参照用として保存されています。
現在のマイグレーションは Alembic で管理されているため、これらのファイルは使用されません。

## Alembic への移行

2025 年 7 月 28 日に Alembic ベースのマイグレーションシステムに移行しました。
現在のマイグレーションは`/alembic/versions/`ディレクトリで管理されています。