-- Rollback script for listed_info table
DROP INDEX IF EXISTS idx_listed_info_date;
DROP INDEX IF EXISTS idx_listed_info_code;
DROP TABLE IF EXISTS listed_info;