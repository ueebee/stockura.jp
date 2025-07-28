-- Create listed_info table for J-Quants listed company information
CREATE TABLE IF NOT EXISTS listed_info (
    date DATE NOT NULL,
    code VARCHAR(4) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    company_name_english VARCHAR(255),
    sector_17_code VARCHAR(10),
    sector_17_code_name VARCHAR(255),
    sector_33_code VARCHAR(10),
    sector_33_code_name VARCHAR(255),
    scale_category VARCHAR(50),
    market_code VARCHAR(10),
    market_code_name VARCHAR(50),
    margin_code VARCHAR(10),
    margin_code_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (date, code)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_listed_info_code ON listed_info(code);
CREATE INDEX IF NOT EXISTS idx_listed_info_date ON listed_info(date);

-- Add comment to table
COMMENT ON TABLE listed_info IS 'J-Quants listed company information';
COMMENT ON COLUMN listed_info.date IS 'Base date for the listing information';
COMMENT ON COLUMN listed_info.code IS '4-digit stock code';
COMMENT ON COLUMN listed_info.company_name IS 'Company name in Japanese';
COMMENT ON COLUMN listed_info.company_name_english IS 'Company name in English';
COMMENT ON COLUMN listed_info.sector_17_code IS '17-sector classification code';
COMMENT ON COLUMN listed_info.sector_17_code_name IS '17-sector classification name';
COMMENT ON COLUMN listed_info.sector_33_code IS '33-sector classification code';
COMMENT ON COLUMN listed_info.sector_33_code_name IS '33-sector classification name';
COMMENT ON COLUMN listed_info.scale_category IS 'Market capitalization scale category';
COMMENT ON COLUMN listed_info.market_code IS 'Market segment code';
COMMENT ON COLUMN listed_info.market_code_name IS 'Market segment name';
COMMENT ON COLUMN listed_info.margin_code IS 'Margin trading classification code (Standard/Premium plans only)';
COMMENT ON COLUMN listed_info.margin_code_name IS 'Margin trading classification name (Standard/Premium plans only)';