-- Alter listed_info table to support longer stock codes (up to 6 characters)
-- This is needed because some stock codes are 5-6 characters long (e.g., REITs, preferred stocks)

-- Alter the code column to support up to 6 characters
ALTER TABLE listed_info 
ALTER COLUMN code TYPE VARCHAR(6);

-- Update the comment to reflect the new constraint
COMMENT ON COLUMN listed_info.code IS 'Stock code (4-6 characters, may include letters)';