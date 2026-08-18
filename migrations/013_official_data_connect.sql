PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS official_source_permissions (
    source_id TEXT PRIMARY KEY REFERENCES sources(id),
    technical_status TEXT NOT NULL CHECK (technical_status IN (
        'TECHNICALLY_VERIFIED',
        'INTERNAL_USE_VERIFIED',
        'PUBLIC_DISPLAY_VERIFIED',
        'REDISTRIBUTION_REQUIRES_LICENSE',
        'UNKNOWN'
    )),
    internal_use_status TEXT NOT NULL CHECK (internal_use_status IN (
        'TECHNICALLY_VERIFIED',
        'INTERNAL_USE_VERIFIED',
        'PUBLIC_DISPLAY_VERIFIED',
        'REDISTRIBUTION_REQUIRES_LICENSE',
        'UNKNOWN'
    )),
    public_display_status TEXT NOT NULL CHECK (public_display_status IN (
        'TECHNICALLY_VERIFIED',
        'INTERNAL_USE_VERIFIED',
        'PUBLIC_DISPLAY_VERIFIED',
        'REDISTRIBUTION_REQUIRES_LICENSE',
        'UNKNOWN'
    )),
    redistribution_status TEXT NOT NULL CHECK (redistribution_status IN (
        'TECHNICALLY_VERIFIED',
        'INTERNAL_USE_VERIFIED',
        'PUBLIC_DISPLAY_VERIFIED',
        'REDISTRIBUTION_REQUIRES_LICENSE',
        'UNKNOWN'
    )),
    evidence_url TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS official_securities (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES markets(id),
    exchange_code TEXT NOT NULL CHECK (exchange_code IN ('TWSE', 'TPEX')),
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    security_type TEXT NOT NULL DEFAULT 'UNKNOWN',
    currency TEXT NOT NULL DEFAULT 'TWD',
    timezone TEXT NOT NULL DEFAULT 'Asia/Taipei',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    mapping_status TEXT NOT NULL,
    first_source_id TEXT NOT NULL REFERENCES sources(id),
    latest_raw_item_id TEXT REFERENCES raw_items(id),
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exchange_code, ticker)
);

CREATE TABLE IF NOT EXISTS official_market_data_daily (
    id TEXT PRIMARY KEY,
    security_id TEXT NOT NULL REFERENCES official_securities(id),
    market_id TEXT NOT NULL REFERENCES markets(id),
    exchange_code TEXT NOT NULL CHECK (exchange_code IN ('TWSE', 'TPEX')),
    ticker TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    opening_price TEXT,
    highest_price TEXT,
    lowest_price TEXT,
    closing_price TEXT,
    price_change TEXT,
    trade_volume INTEGER,
    trade_value INTEGER,
    transaction_count INTEGER,
    data_status TEXT NOT NULL CHECK (data_status IN ('EOD', 'UNKNOWN')),
    source_id TEXT NOT NULL REFERENCES sources(id),
    raw_item_id TEXT NOT NULL REFERENCES raw_items(id),
    collected_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (security_id, trade_date)
);

CREATE TABLE IF NOT EXISTS official_disclosures (
    id TEXT PRIMARY KEY,
    security_id TEXT REFERENCES official_securities(id),
    market_id TEXT NOT NULL REFERENCES markets(id),
    exchange_code TEXT NOT NULL CHECK (exchange_code IN ('TWSE', 'TPEX')),
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    announced_at TEXT,
    announcement_date TEXT,
    event_date TEXT,
    subject TEXT NOT NULL,
    details TEXT,
    clause TEXT,
    mapping_status TEXT NOT NULL CHECK (mapping_status IN (
        'MAPPED_EXISTING_SECURITY',
        'MAPPED_DISCLOSURE_SECURITY',
        'UNMAPPED_INVALID_CODE'
    )),
    source_id TEXT NOT NULL REFERENCES sources(id),
    raw_item_id TEXT NOT NULL UNIQUE REFERENCES raw_items(id),
    official_url TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_official_securities_exchange_ticker
    ON official_securities(exchange_code, ticker);
CREATE INDEX IF NOT EXISTS idx_official_market_data_security_date
    ON official_market_data_daily(security_id, trade_date);
CREATE INDEX IF NOT EXISTS idx_official_market_data_exchange_date
    ON official_market_data_daily(exchange_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_official_disclosures_security_announced
    ON official_disclosures(security_id, announced_at);
CREATE INDEX IF NOT EXISTS idx_official_disclosures_ticker_date
    ON official_disclosures(exchange_code, ticker, announcement_date);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('013_official_data_connect');
