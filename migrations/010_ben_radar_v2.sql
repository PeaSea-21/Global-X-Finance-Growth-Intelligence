PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ben_news_runs (
    id TEXT PRIMARY KEY,
    source_key TEXT NOT NULL,
    source_name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    attempted_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
    fetched_count INTEGER NOT NULL DEFAULT 0,
    valid_item_count INTEGER NOT NULL DEFAULT 0,
    error_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_ben_news_runs_source_time
    ON ben_news_runs(source_key, attempted_at);

CREATE TABLE IF NOT EXISTS ben_news_items (
    id TEXT PRIMARY KEY,
    raw_item_id TEXT NOT NULL UNIQUE REFERENCES raw_items(id),
    source_key TEXT NOT NULL,
    original_title TEXT NOT NULL,
    source_name TEXT NOT NULL,
    published_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    original_url TEXT NOT NULL UNIQUE,
    public_summary TEXT,
    market TEXT NOT NULL,
    language TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ben_news_items_published
    ON ben_news_items(published_at);
CREATE INDEX IF NOT EXISTS idx_ben_news_items_source
    ON ben_news_items(source_key);

CREATE TABLE IF NOT EXISTS ben_stock_history (
    id TEXT PRIMARY KEY,
    stock_code TEXT NOT NULL,
    company_name TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    opening_price TEXT NOT NULL,
    highest_price TEXT NOT NULL,
    lowest_price TEXT NOT NULL,
    closing_price TEXT NOT NULL,
    trade_volume INTEGER NOT NULL,
    trade_value INTEGER,
    source_url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    raw_payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_ben_stock_history_code_date
    ON ben_stock_history(stock_code, trade_date);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('010_ben_radar_v2');
