# データベーススキーマ設計書

## 概要

上場銘柄一覧管理システムのデータベーススキーマ設計書です。PostgreSQL 17を使用し、J-Quants APIから取得する企業情報を効率的に管理するための設計を行います。

## データベース構成

### 使用技術
- **RDBMS**: PostgreSQL 17-bookworm
- **ORM**: SQLAlchemy (非同期対応)
- **マイグレーション**: Alembic
- **拡張機能**: pg_trgm, uuid-ossp, btree_gin

## テーブル設計

### 1. 企業情報テーブル (companies)

企業の基本情報と分類情報を管理する中核テーブル。

```sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,              -- 銘柄コード (例: "7203")
    company_name VARCHAR(200) NOT NULL,            -- 会社名（日本語）
    company_name_english VARCHAR(200),             -- 会社名（英語）
    sector17_code VARCHAR(10),                     -- 17業種区分コード
    sector33_code VARCHAR(10),                     -- 33業種区分コード
    scale_category VARCHAR(50),                    -- 規模区分
    market_code VARCHAR(10),                       -- 市場区分コード
    margin_code VARCHAR(10),                       -- 信用区分
    reference_date DATE NOT NULL,                  -- 情報基準日
    is_active BOOLEAN NOT NULL DEFAULT TRUE,       -- アクティブフラグ
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### 主要インデックス
```sql
-- 基本検索用
CREATE UNIQUE INDEX ix_companies_code ON companies (code);
CREATE INDEX ix_companies_market_code ON companies (market_code);
CREATE INDEX ix_companies_sector17_code ON companies (sector17_code);
CREATE INDEX ix_companies_sector33_code ON companies (sector33_code);

-- 複合検索用
CREATE INDEX ix_companies_market_sector ON companies (market_code, sector17_code);
CREATE INDEX ix_companies_active_market ON companies (is_active, market_code);
CREATE INDEX ix_companies_active_sector17 ON companies (is_active, sector17_code);
CREATE INDEX ix_companies_code_date ON companies (code, reference_date);

-- 全文検索用（GINインデックス）
CREATE INDEX ix_companies_name_search ON companies 
USING gin (company_name gin_trgm_ops);
```

#### 外部キー制約
```sql
ALTER TABLE companies 
ADD CONSTRAINT fk_companies_market_code 
FOREIGN KEY (market_code) REFERENCES market_masters(code) ON DELETE SET NULL;

ALTER TABLE companies 
ADD CONSTRAINT fk_companies_sector17_code 
FOREIGN KEY (sector17_code) REFERENCES sector17_masters(code) ON DELETE SET NULL;

ALTER TABLE companies 
ADD CONSTRAINT fk_companies_sector33_code 
FOREIGN KEY (sector33_code) REFERENCES sector33_masters(code) ON DELETE SET NULL;
```

### 2. 市場区分マスターテーブル (market_masters)

J-Quants APIで定義されている市場区分コードのマスターデータ。

```sql
CREATE TABLE market_masters (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,              -- 市場コード
    name VARCHAR(100) NOT NULL,                    -- 市場名（日本語）
    name_english VARCHAR(100),                     -- 市場名（英語）
    description TEXT,                              -- 市場説明
    display_order INTEGER NOT NULL DEFAULT 0,      -- 表示順序
    is_active BOOLEAN NOT NULL DEFAULT TRUE,       -- アクティブフラグ
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### マスターデータ一覧
| コード | 名称 | 英語名称 | 説明 |
|--------|------|----------|------|
| 0101 | 東証1部 | Tokyo Stock Exchange 1st Section | 東京証券取引所第一部（旧制度） |
| 0102 | 東証2部 | Tokyo Stock Exchange 2nd Section | 東京証券取引所第二部（旧制度） |
| 0104 | マザーズ | Mothers | 東証マザーズ（旧制度） |
| 0105 | TOKYO PRO MARKET | TOKYO PRO MARKET | 東京プロマーケット |
| 0106 | JASDAQ(スタンダード) | JASDAQ Standard | JASDAQスタンダード |
| 0107 | JASDAQ(グロース) | JASDAQ Growth | JASDAQグロース |
| 0109 | その他 | Others | その他の市場 |
| 0111 | プライム | Prime | 東証プライム市場 |
| 0112 | スタンダード | Standard | 東証スタンダード市場 |
| 0113 | グロース | Growth | 東証グロース市場 |

### 3. 17業種区分マスターテーブル (sector17_masters)

J-Quants APIで定義されている17業種区分のマスターデータ。

```sql
CREATE TABLE sector17_masters (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,              -- 17業種コード
    name VARCHAR(100) NOT NULL,                    -- 業種名（日本語）
    name_english VARCHAR(100),                     -- 業種名（英語）
    description TEXT,                              -- 業種説明
    display_order INTEGER NOT NULL DEFAULT 0,      -- 表示順序
    is_active BOOLEAN NOT NULL DEFAULT TRUE,       -- アクティブフラグ
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### マスターデータ一覧
| コード | 名称 | 英語名称 |
|--------|------|----------|
| 1 | 食品 | Food |
| 2 | エネルギー資源 | Energy Resources |
| 3 | 建設・資材 | Construction & Materials |
| 4 | 素材・化学 | Materials & Chemicals |
| 5 | 医薬品 | Pharmaceuticals |
| 6 | 自動車・輸送機 | Automobiles & Transportation Equipment |
| 7 | 鉄鋼・非鉄 | Steel & Non-Ferrous Metals |
| 8 | 機械 | Machinery |
| 9 | 電機・精密 | Electronics & Precision Instruments |
| 10 | 情報通信・サービスその他 | Information & Communication Services, Others |
| 11 | 電気・ガス | Electricity & Gas |
| 12 | 運輸・物流 | Transportation & Logistics |
| 13 | 商社・卸売 | Trading Companies & Wholesale |
| 14 | 小売 | Retail |
| 15 | 銀行 | Banking |
| 16 | 金融（除く銀行） | Financial Services, excluding Banking |
| 17 | 不動産 | Real Estate |
| 99 | その他 | Others |

### 4. 33業種区分マスターテーブル (sector33_masters)

J-Quants APIで定義されている33業種区分のマスターデータ。17業種区分の詳細分類。

```sql
CREATE TABLE sector33_masters (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,              -- 33業種コード
    name VARCHAR(100) NOT NULL,                    -- 業種名（日本語）
    name_english VARCHAR(100),                     -- 業種名（英語）
    description TEXT,                              -- 業種説明
    sector17_code VARCHAR(10) NOT NULL,            -- 対応する17業種コード
    display_order INTEGER NOT NULL DEFAULT 0,      -- 表示順序
    is_active BOOLEAN NOT NULL DEFAULT TRUE,       -- アクティブフラグ
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### 外部キー制約
```sql
ALTER TABLE sector33_masters 
ADD CONSTRAINT fk_sector33_sector17_code 
FOREIGN KEY (sector17_code) REFERENCES sector17_masters(code) ON DELETE RESTRICT;
```

#### インデックス
```sql
CREATE INDEX ix_sector33_masters_sector17_code ON sector33_masters (sector17_code);
CREATE INDEX ix_sector33_sector17_order ON sector33_masters (sector17_code, display_order);
```

#### 主要マスターデータ（抜粋）
| コード | 名称 | 17業種コード | 英語名称 |
|--------|------|--------------|----------|
| 0050 | 水産・農林業 | 1 | Fisheries and Forestry |
| 1050 | 鉱業 | 2 | Mining |
| 2050 | 建設業 | 3 | Construction |
| 3050 | 食料品 | 1 | Food Products |
| 3200 | 化学 | 4 | Chemicals |
| 3250 | 医薬品 | 5 | Pharmaceuticals |
| 3700 | 輸送用機器 | 6 | Transportation Equipment |
| 3450 | 鉄鋼 | 7 | Iron and Steel |
| 3600 | 機械 | 8 | Machinery |
| 3650 | 電気機器 | 9 | Electrical Machinery |
| 5250 | 情報・通信業 | 10 | Information and Communications |
| 4050 | 電気・ガス業 | 11 | Electric Power and Gas |
| 5050 | 陸運業 | 12 | Land Transportation |
| 6050 | 卸売業 | 13 | Wholesale Trade |
| 6100 | 小売業 | 14 | Retail Trade |
| 7050 | 銀行業 | 15 | Banking |
| 7100 | 証券・商品先物取引業 | 16 | Securities and Commodity Futures |
| 8050 | 不動産業 | 17 | Real Estate |
| 9050 | サービス業 | 10 | Services |

### 5. 企業データ同期履歴テーブル (company_sync_history)

J-Quants APIからの企業データ同期履歴を管理。

```sql
CREATE TABLE company_sync_history (
    id SERIAL PRIMARY KEY,
    sync_date DATE NOT NULL,                       -- 同期対象日
    sync_type VARCHAR(20) NOT NULL,                -- 同期タイプ（full/incremental）
    status VARCHAR(20) NOT NULL,                   -- 同期状態（running/completed/failed）
    total_companies INTEGER,                       -- 総企業数
    new_companies INTEGER,                         -- 新規企業数
    updated_companies INTEGER,                     -- 更新企業数
    deleted_companies INTEGER,                     -- 削除企業数
    started_at TIMESTAMP NOT NULL,                 -- 開始時刻
    completed_at TIMESTAMP,                        -- 完了時刻
    error_message TEXT                             -- エラーメッセージ
);
```

#### インデックス
```sql
CREATE INDEX ix_sync_history_date_status ON company_sync_history (sync_date, status);
CREATE INDEX ix_sync_history_started_at ON company_sync_history (started_at);
```

## パフォーマンス最適化

### 1. GINインデックスによる高速テキスト検索

企業名の部分一致検索を高速化するため、PostgreSQLのGINインデックスとトリグラム拡張を使用。

```sql
-- トリグラム拡張の有効化
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GINインデックスによる部分一致検索
CREATE INDEX ix_companies_name_search ON companies 
USING gin (company_name gin_trgm_ops);
```

#### 使用例
```sql
-- 以下の検索が高速実行される
SELECT * FROM companies WHERE company_name LIKE '%トヨタ%';
SELECT * FROM companies WHERE company_name % 'トヨタ自動車';  -- 類似度検索
```

### 2. 複合インデックスによる効率的フィルタリング

よく使用される検索パターンに対応した複合インデックス。

```sql
-- アクティブ企業の市場別検索
CREATE INDEX ix_companies_active_market ON companies (is_active, market_code);

-- アクティブ企業の業種別検索
CREATE INDEX ix_companies_active_sector17 ON companies (is_active, sector17_code);

-- 市場×業種の複合検索
CREATE INDEX ix_companies_market_sector ON companies (market_code, sector17_code);
```

### 3. 外部キー最適化

マスターテーブルとの結合を効率化するインデックス設計。

```sql
-- マスターテーブルのコードフィールドにユニークインデックス
CREATE UNIQUE INDEX ix_market_masters_code ON market_masters (code);
CREATE UNIQUE INDEX ix_sector17_masters_code ON sector17_masters (code);
CREATE UNIQUE INDEX ix_sector33_masters_code ON sector33_masters (code);

-- 表示順序での効率的ソート
CREATE INDEX ix_market_active_order ON market_masters (is_active, display_order);
```

## データ整合性設計

### 1. 外部キー制約による参照整合性

企業テーブルとマスターテーブル間の整合性を保証。

```sql
-- 市場コードの整合性
FOREIGN KEY (market_code) REFERENCES market_masters(code) ON DELETE SET NULL

-- 業種コードの整合性
FOREIGN KEY (sector17_code) REFERENCES sector17_masters(code) ON DELETE SET NULL
FOREIGN KEY (sector33_code) REFERENCES sector33_masters(code) ON DELETE SET NULL

-- 33業種と17業種の階層関係
FOREIGN KEY (sector17_code) REFERENCES sector17_masters(code) ON DELETE RESTRICT
```

### 2. 削除制御方針

- **企業⇔マスター**: `ON DELETE SET NULL` (マスター削除時は企業のコードをNULLに)
- **33業種⇔17業種**: `ON DELETE RESTRICT` (参照されている17業種は削除不可)

### 3. 論理削除による履歴保持

物理削除ではなく`is_active`フラグによる論理削除を採用。

## セキュリティ設計

### 1. データアクセス制御

PostgreSQLのロール・権限機能による細かな制御。

```sql
-- アプリケーション用ロール
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';

-- 読み取り専用ロール
CREATE ROLE app_readonly WITH LOGIN PASSWORD 'readonly_password';

-- 権限設定
GRANT SELECT, INSERT, UPDATE, DELETE ON companies TO app_user;
GRANT SELECT ON market_masters TO app_user;
GRANT SELECT ON sector17_masters TO app_user;
GRANT SELECT ON sector33_masters TO app_user;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
```

### 2. データマスキング

機密情報の適切な保護。

```sql
-- ビューによる制限された情報の提供
CREATE VIEW public_companies AS
SELECT 
    code,
    company_name,
    market_code,
    sector17_code,
    is_active
FROM companies 
WHERE is_active = true;
```

## バックアップ・復旧戦略

### 1. 定期バックアップ

```bash
# 日次フルバックアップ
pg_dump -h localhost -U postgres -d stockura > backup_$(date +%Y%m%d).sql

# 継続的なWALアーカイブ
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

### 2. ポイントインタイム復旧

WALファイルによる任意時点への復旧機能。

## 監視・メンテナンス

### 1. パフォーマンス監視

```sql
-- スロークエリの監視
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC;

-- インデックス使用状況
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes;
```

### 2. 容量管理

```sql
-- テーブルサイズ監視
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public';
```

## マイグレーション管理

### 1. Alembicによるバージョン管理

現在適用済みのマイグレーション：

1. `2c86595eaba4_create_data_sources_table.py` - データソーステーブル作成
2. `01125040a15b_add_initial_data_sources.py` - 初期データソース投入
3. `c2e3a9be79f7_add_company_tables.py` - 企業関連テーブル作成
4. `8aff57aa15b6_insert_master_data.py` - マスターデータ投入
5. `1479a1bf7b47_add_foreign_key_constraints.py` - 外部キー制約追加

### 2. 環境別設定

```python
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://postgres:postgres@localhost/stockura

# 本番環境用設定
[production]
sqlalchemy.url = postgresql://app_user:${DB_PASSWORD}@prod-db:5432/stockura
```

## 今後の拡張計画

### 1. パーティショニング

大量データ対応のための年次パーティショニング。

```sql
-- 年次パーティション（企業データ）
CREATE TABLE companies_2025 PARTITION OF companies
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### 2. レプリケーション

読み込み性能向上のためのリードレプリカ構成。

### 3. 分析用データマート

BI・分析用の集計テーブル設計。

```sql
-- 業種別企業数サマリー
CREATE MATERIALIZED VIEW sector_company_summary AS
SELECT 
    s17.code as sector17_code,
    s17.name as sector17_name,
    COUNT(c.id) as company_count,
    COUNT(CASE WHEN c.market_code = '0111' THEN 1 END) as prime_count
FROM sector17_masters s17
LEFT JOIN companies c ON s17.code = c.sector17_code AND c.is_active = true
GROUP BY s17.code, s17.name;
```

これらの設計により、スケーラブルで保守性の高い企業情報管理システムを構築できます。