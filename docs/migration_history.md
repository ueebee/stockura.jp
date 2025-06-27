# データベースマイグレーション履歴

## 概要

上場銘柄一覧管理システムのデータベースマイグレーション履歴を記録します。各マイグレーションの目的、変更内容、実行結果を詳細に管理します。

## マイグレーション一覧

### 1. 基盤マイグレーション

#### `2c86595eaba4_create_data_sources_table.py`
- **実行日**: 2025-06-XX
- **目的**: データソース管理テーブルの作成
- **変更内容**:
  - `data_sources`テーブル作成
  - 認証情報の暗号化対応
  - プロバイダー別設定管理

#### `01125040a15b_add_initial_data_sources.py`
- **実行日**: 2025-06-XX  
- **目的**: 初期データソースの投入
- **変更内容**:
  - J-Quants、YFinanceプロバイダー設定
  - 暗号化された認証情報の投入
  - デフォルト設定の適用

### 2. 企業情報マイグレーション

#### `c2e3a9be79f7_add_company_tables.py` 
- **実行日**: 2025-06-26
- **目的**: 上場企業関連テーブルの作成
- **変更内容**:

##### 作成テーブル
1. **`companies`** - 企業基本情報
   ```sql
   CREATE TABLE companies (
       id SERIAL PRIMARY KEY,
       code VARCHAR(10) UNIQUE NOT NULL,
       company_name VARCHAR(200) NOT NULL,
       company_name_english VARCHAR(200),
       sector17_code VARCHAR(10),
       sector33_code VARCHAR(10),
       scale_category VARCHAR(50),
       market_code VARCHAR(10),
       margin_code VARCHAR(10),
       reference_date DATE NOT NULL,
       is_active BOOLEAN NOT NULL DEFAULT TRUE,
       created_at TIMESTAMP NOT NULL,
       updated_at TIMESTAMP NOT NULL
   );
   ```

2. **`sector17_masters`** - 17業種区分マスター
   ```sql
   CREATE TABLE sector17_masters (
       id SERIAL PRIMARY KEY,
       code VARCHAR(10) UNIQUE NOT NULL,
       name VARCHAR(100) NOT NULL,
       name_english VARCHAR(100),
       description TEXT,
       display_order INTEGER NOT NULL DEFAULT 0,
       is_active BOOLEAN NOT NULL DEFAULT TRUE,
       created_at TIMESTAMP NOT NULL,
       updated_at TIMESTAMP NOT NULL
   );
   ```

3. **`sector33_masters`** - 33業種区分マスター
   ```sql
   CREATE TABLE sector33_masters (
       id SERIAL PRIMARY KEY,
       code VARCHAR(10) UNIQUE NOT NULL,
       name VARCHAR(100) NOT NULL,
       name_english VARCHAR(100),
       description TEXT,
       sector17_code VARCHAR(10) NOT NULL,
       display_order INTEGER NOT NULL DEFAULT 0,
       is_active BOOLEAN NOT NULL DEFAULT TRUE,
       created_at TIMESTAMP NOT NULL,
       updated_at TIMESTAMP NOT NULL
   );
   ```

4. **`market_masters`** - 市場区分マスター
   ```sql
   CREATE TABLE market_masters (
       id SERIAL PRIMARY KEY,
       code VARCHAR(10) UNIQUE NOT NULL,
       name VARCHAR(100) NOT NULL,
       name_english VARCHAR(100),
       description TEXT,
       display_order INTEGER NOT NULL DEFAULT 0,
       is_active BOOLEAN NOT NULL DEFAULT TRUE,
       created_at TIMESTAMP NOT NULL,
       updated_at TIMESTAMP NOT NULL
   );
   ```

5. **`company_sync_history`** - 企業データ同期履歴
   ```sql
   CREATE TABLE company_sync_history (
       id SERIAL PRIMARY KEY,
       sync_date DATE NOT NULL,
       sync_type VARCHAR(20) NOT NULL,
       status VARCHAR(20) NOT NULL,
       total_companies INTEGER,
       new_companies INTEGER,
       updated_companies INTEGER,
       deleted_companies INTEGER,
       started_at TIMESTAMP NOT NULL,
       completed_at TIMESTAMP,
       error_message TEXT
   );
   ```

##### 作成インデックス
- **基本インデックス**: 各テーブルの主キー、ユニーク制約
- **検索インデックス**: 企業コード、市場コード、業種コード
- **複合インデックス**: 市場×業種、アクティブ×市場、アクティブ×業種
- **GINインデックス**: 企業名部分一致検索（トリグラム）
- **履歴インデックス**: 同期日時、ステータス

##### 特殊設定
- **PostgreSQL拡張**: `pg_trgm`（トリグラム検索）
- **GINインデックス**: `gin_trgm_ops`による高速部分一致検索

#### `8aff57aa15b6_insert_master_data.py`
- **実行日**: 2025-06-26
- **目的**: マスターデータの投入
- **変更内容**:

##### 市場マスターデータ（10件）
```sql
INSERT INTO market_masters (code, name, name_english, description, display_order, is_active) VALUES
('0101', '東証1部', 'Tokyo Stock Exchange 1st Section', '東京証券取引所第一部（旧制度）', 1, true),
('0102', '東証2部', 'Tokyo Stock Exchange 2nd Section', '東京証券取引所第二部（旧制度）', 2, true),
('0104', 'マザーズ', 'Mothers', '東証マザーズ（旧制度）', 3, true),
('0105', 'TOKYO PRO MARKET', 'TOKYO PRO MARKET', '東京プロマーケット', 4, true),
('0106', 'JASDAQ(スタンダード)', 'JASDAQ Standard', 'JASDAQスタンダード', 5, true),
('0107', 'JASDAQ(グロース)', 'JASDAQ Growth', 'JASDAQグロース', 6, true),
('0109', 'その他', 'Others', 'その他の市場', 7, true),
('0111', 'プライム', 'Prime', '東証プライム市場', 8, true),
('0112', 'スタンダード', 'Standard', '東証スタンダード市場', 9, true),
('0113', 'グロース', 'Growth', '東証グロース市場', 10, true);
```

##### 17業種マスターデータ（18件）
主要業種：
- 食品、エネルギー資源、建設・資材、素材・化学
- 医薬品、自動車・輸送機、鉄鋼・非鉄、機械
- 電機・精密、情報通信・サービスその他、電気・ガス
- 運輸・物流、商社・卸売、小売、銀行
- 金融（除く銀行）、不動産、その他

##### 33業種マスターデータ（34件）
J-Quants API仕様に基づく詳細業種分類：
- 各33業種は対応する17業種コードを持つ
- 水産・農林業(0050)から サービス業(9050)、その他(9999)まで

#### `1479a1bf7b47_add_foreign_key_constraints.py`
- **実行日**: 2025-06-26
- **目的**: 外部キー制約の追加
- **変更内容**:

##### 外部キー制約
```sql
-- 企業⇔市場の整合性
ALTER TABLE companies 
ADD CONSTRAINT fk_companies_market_code 
FOREIGN KEY (market_code) REFERENCES market_masters(code) ON DELETE SET NULL;

-- 企業⇔17業種の整合性
ALTER TABLE companies 
ADD CONSTRAINT fk_companies_sector17_code 
FOREIGN KEY (sector17_code) REFERENCES sector17_masters(code) ON DELETE SET NULL;

-- 企業⇔33業種の整合性
ALTER TABLE companies 
ADD CONSTRAINT fk_companies_sector33_code 
FOREIGN KEY (sector33_code) REFERENCES sector33_masters(code) ON DELETE SET NULL;

-- 33業種⇔17業種の階層関係
ALTER TABLE sector33_masters 
ADD CONSTRAINT fk_sector33_sector17_code 
FOREIGN KEY (sector17_code) REFERENCES sector17_masters(code) ON DELETE RESTRICT;
```

##### 制約の設計方針
- **SET NULL**: マスターデータ削除時は企業データのコードをNULLに
- **RESTRICT**: 参照されている17業種は削除不可（データ整合性保護）

## マイグレーション実行結果

### 実行ログ
```bash
# 2025-06-26 実行
$ docker compose exec web alembic upgrade head

INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO [alembic.runtime.migration] Will assume transactional DDL.
INFO [alembic.runtime.migration] Running upgrade c2e3a9be79f7 -> 8aff57aa15b6, insert_master_data
INFO [alembic.runtime.migration] Running upgrade 8aff57aa15b6 -> 1479a1bf7b47, add_foreign_key_constraints
```

### データ投入確認
```sql
-- 市場マスター: 10件投入確認
SELECT COUNT(*) FROM market_masters; -- 結果: 10

-- 17業種マスター: 18件投入確認  
SELECT COUNT(*) FROM sector17_masters; -- 結果: 18

-- 33業種マスター: 34件投入確認
SELECT COUNT(*) FROM sector33_masters; -- 結果: 34

-- 外部キー制約確認
SELECT constraint_name, table_name 
FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public';
```

### パフォーマンステスト
```sql
-- GINインデックス動作確認
EXPLAIN ANALYZE SELECT * FROM companies WHERE company_name LIKE '%トヨタ%';
-- 結果: Seq Scan (データ未投入のため、インデックス未使用)

-- 外部キー結合テスト
SELECT s33.name, s17.name as sector17_name 
FROM sector33_masters s33 
JOIN sector17_masters s17 ON s33.sector17_code = s17.code 
LIMIT 5;
-- 結果: 正常動作確認
```

## 環境別適用状況

### 開発環境 (Local Docker)
- **適用済み**: 全5マイグレーション
- **データ確認**: ✅ 完了
- **制約確認**: ✅ 完了

### テスト環境
- **状況**: 未適用
- **適用予定**: 次回デプロイ時

### 本番環境  
- **状況**: 未適用
- **適用予定**: フェーズ2実装完了後

## ロールバック手順

### 緊急時ロールバック
```bash
# 外部キー制約のみ削除
$ docker compose exec web alembic downgrade 8aff57aa15b6

# マスターデータを含む全削除
$ docker compose exec web alembic downgrade c2e3a9be79f7

# 企業関連テーブル全削除
$ docker compose exec web alembic downgrade 01125040a15b
```

### 部分ロールバック
```sql
-- マスターデータのみ削除（手動）
DELETE FROM sector33_masters;
DELETE FROM sector17_masters;  
DELETE FROM market_masters;
```

## 注意事項・既知の問題

### 1. PostgreSQL拡張機能依存
- **pg_trgm**: Docker初期化時に自動有効化
- **新環境**: `docker/postgres/init.sql`により自動設定
- **既存環境**: 手動で`CREATE EXTENSION pg_trgm;`が必要

### 2. GINインデックスの制限
- **更新コスト**: 通常のBTreeインデックスより高い
- **容量**: インデックスサイズが大きい
- **推奨**: 検索中心のワークロードで有効

### 3. 外部キー制約の影響
- **マスターデータ更新**: 慎重な順序で実行必要
- **パフォーマンス**: INSERT/UPDATE時に制約チェック発生
- **デッドロック**: 大量同時更新時に注意

## 今後のマイグレーション計画

### フェーズ2: API統合機能
- **予定**: 2025-07-XX
- **内容**: 
  - APIレスポンスキャッシュテーブル
  - 同期設定テーブル
  - エラーログテーブル

### フェーズ3: パフォーマンス最適化
- **予定**: 2025-08-XX
- **内容**:
  - パーティショニング設定
  - 分析用マテリアライズドビュー
  - 統計情報テーブル

### フェーズ4: 運用機能強化
- **予定**: 2025-09-XX
- **内容**:
  - 監査ログテーブル
  - ユーザー権限管理
  - バックアップ設定

## 運用監視

### 日次チェック項目
```sql
-- 1. マイグレーション状態確認
SELECT version_num FROM alembic_version;

-- 2. テーブル容量確認
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 3. 外部キー制約状態確認
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint WHERE contype = 'f';

-- 4. インデックス使用統計
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### 週次メンテナンス
```sql
-- 統計情報更新
ANALYZE;

-- 不要な領域回収
VACUUM;

-- インデックス再構築（必要時）
REINDEX TABLE companies;
```

この履歴により、システムの成長とともにデータベース構造の変遷を適切に管理できます。