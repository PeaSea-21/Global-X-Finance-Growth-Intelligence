PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS industry_classifications (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES markets(id),
    exchange_code TEXT NOT NULL CHECK (exchange_code IN ('TWSE', 'TPEX')),
    scheme TEXT NOT NULL DEFAULT 'OFFICIAL_INDUSTRY_CODE',
    official_industry_code TEXT NOT NULL,
    official_industry_name TEXT NOT NULL,
    normalized_sector TEXT NOT NULL,
    mapping_status TEXT NOT NULL CHECK (mapping_status IN (
        'MAPPED_COMMON_STOCK',
        'UNKNOWN',
        'EXCLUDED_ETF_FUND',
        'EXCLUDED_NON_COMMON_STOCK'
    )),
    source_authority TEXT NOT NULL,
    source_endpoint TEXT NOT NULL,
    source_field_code TEXT NOT NULL,
    source_field_name TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exchange_code, scheme, official_industry_code)
);

CREATE TABLE IF NOT EXISTS security_industry_mappings (
    id TEXT PRIMARY KEY,
    security_id TEXT NOT NULL REFERENCES official_securities(id),
    industry_classification_id TEXT REFERENCES industry_classifications(id),
    exchange_code TEXT NOT NULL CHECK (exchange_code IN ('TWSE', 'TPEX')),
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    official_industry_code TEXT NOT NULL,
    official_industry_name TEXT NOT NULL,
    normalized_sector TEXT NOT NULL,
    mapping_status TEXT NOT NULL CHECK (mapping_status IN (
        'MAPPED_COMMON_STOCK',
        'UNKNOWN',
        'EXCLUDED_ETF_FUND',
        'EXCLUDED_NON_COMMON_STOCK'
    )),
    source_id TEXT NOT NULL REFERENCES sources(id),
    raw_item_id TEXT NOT NULL REFERENCES raw_items(id),
    source_endpoint TEXT NOT NULL,
    source_field_code TEXT NOT NULL,
    source_field_name TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (security_id)
);

CREATE INDEX IF NOT EXISTS idx_industry_classifications_sector
    ON industry_classifications(normalized_sector, mapping_status);
CREATE INDEX IF NOT EXISTS idx_security_industry_mappings_security
    ON security_industry_mappings(security_id, collected_at);
CREATE INDEX IF NOT EXISTS idx_security_industry_mappings_ticker
    ON security_industry_mappings(exchange_code, ticker);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('015_industry_mapping');
