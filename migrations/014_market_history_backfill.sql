PRAGMA foreign_keys = ON;

ALTER TABLE official_securities
    ADD COLUMN history_status TEXT NOT NULL DEFAULT 'UNKNOWN'
    CHECK (history_status IN ('UNKNOWN', 'READY', 'INSUFFICIENT_HISTORY'));

ALTER TABLE official_securities
    ADD COLUMN history_trade_days INTEGER NOT NULL DEFAULT 0;

ALTER TABLE official_securities
    ADD COLUMN history_first_date TEXT;

ALTER TABLE official_securities
    ADD COLUMN history_last_date TEXT;

CREATE INDEX IF NOT EXISTS idx_official_securities_history_status
    ON official_securities(exchange_code, history_status);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('014_market_history_backfill');
