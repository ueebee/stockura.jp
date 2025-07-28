# 手動テストガイド - fetch-listed-info 機能

このドキュメントでは、`fetch-listed-info`機能の手動テスト方法について説明します。

## 目次
1. [事前準備](#事前準備)
2. [基本的な動作確認](#基本的な動作確認)
3. [詳細な機能テスト](#詳細な機能テスト)
4. [エラーケースの確認](#エラーケースの確認)
5. [データベースの確認](#データベースの確認)
6. [トラブルシューティング](#トラブルシューティング)

## 事前準備

### 1. 環境変数の設定

J-Quants API の認証情報を環境変数に設定します。

```bash
# .env ファイルに追加
echo "JQUANTS_EMAIL=your-email@example.com" >> .env
echo "JQUANTS_PASSWORD=your-password" >> .env

# または、環境変数として直接エクスポート
export JQUANTS_EMAIL="your-email@example.com"
export JQUANTS_PASSWORD="your-password"
```

### 2. データベースの準備

PostgreSQL が起動していることを確認し、マイグレーションを実行します。

```bash
# PostgreSQL の起動確認
pg_isready

# データベースへの接続確認
psql -U postgres -d stockura -c "SELECT 1;"

# マイグレーションの実行
psql -U postgres -d stockura -f sql/migrations/001_create_listed_info_table.sql

# テーブルが作成されたことを確認
psql -U postgres -d stockura -c "\dt listed_info"
```

### 3. 依存関係の確認

必要な Python パッケージがインストールされていることを確認します。

```bash
# 依存関係のインストール
pip install -r requirements.txt

# click パッケージの確認
python -c "import click; print(click.__version__)"
```

## 基本的な動作確認

### 1. ヘルプの表示

まず、コマンドが正しく認識されることを確認します。

```bash
python scripts/fetch_listed_info.py --help
```

期待される出力：
```
Usage: fetch_listed_info.py [OPTIONS]

  J-Quants API から上場銘柄情報を取得してデータベースに保存する

Options:
  -c, --code TEXT      銘柄コード（4 桁の数字）。指定しない場合は全銘柄を取得
  -d, --date TEXT      基準日（YYYYMMDD 形式）。指定しない場合は最新データを取得
  -e, --email TEXT     J-Quants API のメールアドレス
  -p, --password TEXT  J-Quants API のパスワード
  --help               Show this message and exit.
```

### 2. 特定銘柄の情報取得（小規模テスト）

まず、単一銘柄でテストを行います。

```bash
# トヨタ自動車（7203）の最新情報を取得
python scripts/fetch_listed_info.py --code 7203
```

期待される出力例：
```
J-Quants API に接続中...
認証成功
データ取得中... (code: 7203, date: 最新)

✅ 処理完了:
  - 取得件数: 1 件
  - 保存件数: 1 件
```

### 3. 特定日付の銘柄情報取得

過去の特定日付のデータを取得します。

```bash
# 2024 年 1 月 4 日のトヨタ自動車の情報を取得
python scripts/fetch_listed_info.py --code 7203 --date 20240104
```

### 4. データベースの確認

取得したデータがデータベースに保存されていることを確認します。

```bash
# 保存されたデータを確認
psql -U postgres -d stockura -c "SELECT * FROM listed_info WHERE code = '7203' ORDER BY date DESC LIMIT 5;"
```

## 詳細な機能テスト

### 1. 複数銘柄の取得（中規模テスト）

特定の日付で複数銘柄を取得します（API の制限により時間がかかる場合があります）。

```bash
# 2024 年 1 月 4 日の全銘柄情報を取得（注意：時間がかかります）
python scripts/fetch_listed_info.py --date 20240104
```

実行中の表示例：
```
J-Quants API に接続中...
認証成功
データ取得中... (code: 全銘柄, date: 20240104)

✅ 処理完了:
  - 取得件数: 3800 件
  - 保存件数: 3800 件
```

### 2. 進捗の確認

大量データ取得中は、ログで進捗を確認できます。別ターミナルで以下を実行：

```bash
# アプリケーションログの確認
tail -f logs/app.log | grep "listed_info"
```

### 3. バッチ処理の確認

1000 件ごとにバッチ処理されることを確認：

```bash
# ログでバッチ処理を確認
grep "Saved batch" logs/app.log
```

期待される出力例：
```
Saved batch 1 - 1000 records
Saved batch 2 - 1000 records
Saved batch 3 - 1000 records
Saved batch 4 - 800 records
```

## エラーケースの確認

### 1. 認証エラーのテスト

```bash
# 間違った認証情報でテスト
python scripts/fetch_listed_info.py --email wrong@example.com --password wrongpass
```

期待される出力：
```
J-Quants API に接続中...
エラー: J-Quants API の認証に失敗しました。
```

### 2. 無効な銘柄コードのテスト

```bash
# 無効な銘柄コード
python scripts/fetch_listed_info.py --code 999  # 3 桁
python scripts/fetch_listed_info.py --code 99999  # 5 桁
python scripts/fetch_listed_info.py --code ABCD  # 文字
```

### 3. 無効な日付フォーマットのテスト

```bash
# 無効な日付フォーマット
python scripts/fetch_listed_info.py --date 2024-01-04  # ハイフン区切り
python scripts/fetch_listed_info.py --date 240104  # 6 桁
```

期待される出力：
```
エラー: 無効な日付形式です: 2024-01-04
```

### 4. ネットワークエラーのシミュレーション

```bash
# ネットワークを切断してテスト（Wi-Fi をオフにするなど）
python scripts/fetch_listed_info.py --code 7203
```

## データベースの確認

### 1. 保存されたデータの統計情報

```sql
-- 日付別のレコード数
psql -U postgres -d stockura -c "
SELECT date, COUNT(*) as count 
FROM listed_info 
GROUP BY date 
ORDER BY date DESC 
LIMIT 10;
"

-- 市場別の銘柄数
psql -U postgres -d stockura -c "
SELECT market_code_name, COUNT(DISTINCT code) as count 
FROM listed_info 
WHERE date = (SELECT MAX(date) FROM listed_info)
GROUP BY market_code_name 
ORDER BY count DESC;
"

-- セクター別の銘柄数
psql -U postgres -d stockura -c "
SELECT sector_17_code_name, COUNT(DISTINCT code) as count 
FROM listed_info 
WHERE date = (SELECT MAX(date) FROM listed_info)
GROUP BY sector_17_code_name 
ORDER BY count DESC 
LIMIT 10;
"
```

### 2. 特定銘柄の履歴確認

```sql
-- トヨタ自動車の情報履歴
psql -U postgres -d stockura -c "
SELECT date, company_name, market_code_name, sector_17_code_name 
FROM listed_info 
WHERE code = '7203' 
ORDER BY date DESC 
LIMIT 10;
"
```

### 3. データの整合性確認

```sql
-- 重複データがないことを確認
psql -U postgres -d stockura -c "
SELECT date, code, COUNT(*) 
FROM listed_info 
GROUP BY date, code 
HAVING COUNT(*) > 1;
"

-- NULL 値の確認
psql -U postgres -d stockura -c "
SELECT COUNT(*) as total,
       COUNT(company_name_english) as with_english_name,
       COUNT(margin_code) as with_margin_code
FROM listed_info 
WHERE date = (SELECT MAX(date) FROM listed_info);
"
```

## トラブルシューティング

### 1. psycopg2 エラーが発生する場合

```bash
# psycopg2-binary を再インストール
pip uninstall psycopg2 psycopg2-binary
pip install psycopg2-binary
```

### 2. click コマンドが認識されない場合

```bash
# Python パスを確認
python -c "import sys; print('\n'.join(sys.path))"

# 直接実行
cd /path/to/stockura
python -m app.presentation.cli.commands.fetch_listed_info_command
```

### 3. データベース接続エラーの場合

```bash
# PostgreSQL の状態確認
sudo systemctl status postgresql

# 接続情報の確認
echo $DATABASE_URL

# .env ファイルの確認
cat .env | grep DATABASE_URL
```

### 4. API レート制限エラーの場合

J-Quants API にはレート制限があります。エラーが発生した場合は、しばらく待ってから再実行してください。

```bash
# 1 時間後に再実行
sleep 3600 && python scripts/fetch_listed_info.py
```

## パフォーマンステスト

### 1. 実行時間の計測

```bash
# time コマンドで実行時間を計測
time python scripts/fetch_listed_info.py --code 7203

# 全銘柄取得の時間計測（注意：長時間かかります）
time python scripts/fetch_listed_info.py --date 20240104
```

### 2. メモリ使用量の確認

```bash
# 別ターミナルで実行
while true; do ps aux | grep fetch_listed_info | grep -v grep; sleep 1; done
```

## クリーンアップ

テスト後のデータクリーンアップ：

```bash
# 特定日付のデータを削除
psql -U postgres -d stockura -c "DELETE FROM listed_info WHERE date = '2024-01-04';"

# 全データを削除（注意！）
psql -U postgres -d stockura -c "TRUNCATE TABLE listed_info;"

# テーブルを削除して再作成
psql -U postgres -d stockura -f sql/migrations/001_rollback_listed_info_table.sql
psql -U postgres -d stockura -f sql/migrations/001_create_listed_info_table.sql
```

## まとめ

このガイドに従って手動テストを実行することで、`fetch-listed-info`機能が正しく動作することを確認できます。問題が発生した場合は、ログファイルとデータベースの状態を確認し、トラブルシューティングセクションを参照してください。