PRAGMA foreign_keys = ON;

ALTER TABLE normalized_items ADD COLUMN market_id TEXT REFERENCES markets(id);
ALTER TABLE normalized_items ADD COLUMN dataset_id TEXT;
ALTER TABLE normalized_items ADD COLUMN record_type TEXT;
ALTER TABLE normalized_items ADD COLUMN data_date TEXT;
ALTER TABLE normalized_items ADD COLUMN stock_code TEXT;
ALTER TABLE normalized_items ADD COLUMN company_name TEXT;
ALTER TABLE normalized_items ADD COLUMN opening_price TEXT;
ALTER TABLE normalized_items ADD COLUMN highest_price TEXT;
ALTER TABLE normalized_items ADD COLUMN lowest_price TEXT;
ALTER TABLE normalized_items ADD COLUMN closing_price TEXT;
ALTER TABLE normalized_items ADD COLUMN trade_volume TEXT;
ALTER TABLE normalized_items ADD COLUMN trade_value TEXT;
ALTER TABLE normalized_items ADD COLUMN price_change TEXT;
ALTER TABLE normalized_items ADD COLUMN market_index_name TEXT;
ALTER TABLE normalized_items ADD COLUMN market_index_close TEXT;
ALTER TABLE normalized_items ADD COLUMN market_index_change_points TEXT;
ALTER TABLE normalized_items ADD COLUMN market_index_change_percent TEXT;
ALTER TABLE normalized_items ADD COLUMN industry_category TEXT;
ALTER TABLE normalized_items ADD COLUMN company_count TEXT;
ALTER TABLE normalized_items ADD COLUMN issued_shares TEXT;
ALTER TABLE normalized_items ADD COLUMN foreign_mainland_shares TEXT;
ALTER TABLE normalized_items ADD COLUMN foreign_holding_percentage TEXT;

ALTER TABLE entities ADD COLUMN entity_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_market_type_key
    ON entities(market_id, entity_type, entity_key)
    WHERE entity_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_normalized_items_market_date
    ON normalized_items(market_id, data_date);
CREATE INDEX IF NOT EXISTS idx_normalized_items_dataset
    ON normalized_items(dataset_id);
CREATE INDEX IF NOT EXISTS idx_normalized_items_stock_code
    ON normalized_items(stock_code);

CREATE TABLE IF NOT EXISTS official_signal_cards (
    id TEXT PRIMARY KEY,
    normalized_item_id TEXT NOT NULL REFERENCES normalized_items(id),
    entity_id TEXT REFERENCES entities(id),
    market_id TEXT NOT NULL REFERENCES markets(id),
    signal_label TEXT NOT NULL CHECK (signal_label = 'RULE_BASED_OFFICIAL_SIGNAL'),
    signal_type TEXT NOT NULL CHECK (
        signal_type IN (
            'HIGH_TRADE_VOLUME',
            'HIGH_TRADE_VALUE',
            'NOTABLE_DAILY_CHANGE',
            'FOREIGN_HOLDING_RATIO'
        )
    ),
    data_date TEXT NOT NULL,
    metric_value TEXT NOT NULL,
    calculation_basis TEXT NOT NULL,
    formula_version TEXT NOT NULL,
    evidence_raw_item_id TEXT NOT NULL REFERENCES raw_items(id),
    official_url TEXT NOT NULL,
    freshness_status TEXT NOT NULL CHECK (
        freshness_status IN (
            'CURRENT_OFFICIAL_DATA',
            'OFFICIAL_LATEST_AVAILABLE_DATA',
            'UNKNOWN_DATA_DATE'
        )
    ),
    risk_notice TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (normalized_item_id, signal_type, formula_version)
);

CREATE INDEX IF NOT EXISTS idx_official_signal_cards_market_date
    ON official_signal_cards(market_id, data_date);
CREATE INDEX IF NOT EXISTS idx_official_signal_cards_type
    ON official_signal_cards(signal_type);
CREATE INDEX IF NOT EXISTS idx_official_signal_cards_entity
    ON official_signal_cards(entity_id);
CREATE INDEX IF NOT EXISTS idx_official_signal_cards_raw
    ON official_signal_cards(evidence_raw_item_id);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('003_normalized_signals');

