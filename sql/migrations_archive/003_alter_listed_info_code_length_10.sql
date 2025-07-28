-- Alter listed_info table to support even longer stock codes (up to 10 characters)
-- This is needed because J-Quants API may return various code formats including ETFs, REITs, etc.

-- Alter the code column to support up to 10 characters
ALTER TABLE listed_info 
ALTER COLUMN code TYPE VARCHAR(10);

-- Update the comment to reflect the new constraint
COMMENT ON COLUMN listed_info.code IS 'Stock code (up to 10 characters, may include letters, numbers, hyphens, and underscores)';