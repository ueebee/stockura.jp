-- PostgreSQL初期化スクリプト
-- Docker起動時に自動実行される

-- トリグラム検索用拡張を有効化
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 将来的に必要になる可能性のある拡張も事前に有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID生成
CREATE EXTENSION IF NOT EXISTS btree_gin;    -- GINインデックス拡張