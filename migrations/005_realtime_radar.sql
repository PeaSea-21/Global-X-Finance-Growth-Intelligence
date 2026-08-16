PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS realtime_sources (
    id TEXT PRIMARY KEY,
    registry_source_id TEXT NOT NULL UNIQUE,
    core_source_id TEXT REFERENCES sources(id),
    platform TEXT NOT NULL CHECK (platform IN ('X','YOUTUBE','WEB','API','FORUM','UNKNOWN')),
    source_type TEXT NOT NULL,
    account_handle TEXT,
    profile_url TEXT,
    channel_name TEXT,
    channel_id TEXT,
    channel_url TEXT,
    publisher TEXT NOT NULL,
    publisher_group TEXT NOT NULL,
    market TEXT NOT NULL,
    language TEXT NOT NULL,
    category TEXT NOT NULL,
    verified_at TEXT,
    verification_evidence_url TEXT,
    monitoring_method TEXT NOT NULL,
    source_status TEXT NOT NULL CHECK (
        source_status IN (
            'VERIFIED_ACTIVE', 'VERIFIED_MANUAL_ONLY',
            'NEEDS_VERIFICATION', 'BLOCKED', 'UNKNOWN'
        )
    ),
    monitoring_status TEXT NOT NULL,
    expected_interval_minutes INTEGER CHECK (
        expected_interval_minutes IS NULL OR expected_interval_minutes > 0
    ),
    last_success_at TEXT,
    last_failure_at TEXT,
    last_failure_reason TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0 CHECK (consecutive_failures >= 0),
    latest_content_published_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        source_status <> 'VERIFIED_ACTIVE' OR
        (verified_at IS NOT NULL AND length(trim(verified_at)) > 0 AND
         verification_evidence_url IS NOT NULL AND
         length(trim(verification_evidence_url)) > 0 AND
         expected_interval_minutes IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS radar_runs (
    id TEXT PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    realtime_source_id TEXT NOT NULL REFERENCES realtime_sources(id),
    collection_run_id TEXT REFERENCES collection_runs(id),
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS','FAILED','SKIPPED_NOT_DUE')),
    fetched_count INTEGER NOT NULL DEFAULT 0 CHECK (fetched_count >= 0),
    new_count INTEGER NOT NULL DEFAULT 0 CHECK (new_count >= 0),
    duplicate_count INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_count >= 0),
    request_latency_seconds REAL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS radar_items (
    id TEXT PRIMARY KEY,
    raw_item_id TEXT NOT NULL UNIQUE REFERENCES raw_items(id),
    realtime_source_id TEXT NOT NULL REFERENCES realtime_sources(id),
    external_item_id TEXT,
    source_type TEXT NOT NULL,
    title_or_text TEXT NOT NULL,
    source_account TEXT NOT NULL,
    published_at TEXT,
    discovered_at TEXT NOT NULL,
    detection_latency_minutes REAL,
    fact_or_opinion TEXT NOT NULL CHECK (fact_or_opinion IN ('FACT','OPINION','UNKNOWN')),
    evidence_url TEXT NOT NULL,
    duplicate_status TEXT NOT NULL CHECK (duplicate_status IN ('EXACT_NEW','EXACT_DUPLICATE')),
    publisher_group TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS radar_scheduler_state (
    realtime_source_id TEXT PRIMARY KEY REFERENCES realtime_sources(id),
    next_due_at TEXT NOT NULL,
    last_cycle_id TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_realtime_sources_status ON realtime_sources(source_status);
CREATE INDEX IF NOT EXISTS idx_realtime_sources_platform ON realtime_sources(platform);
CREATE INDEX IF NOT EXISTS idx_realtime_sources_group ON realtime_sources(publisher_group);
CREATE INDEX IF NOT EXISTS idx_radar_runs_cycle ON radar_runs(cycle_id);
CREATE INDEX IF NOT EXISTS idx_radar_runs_source_started ON radar_runs(realtime_source_id, started_at);
CREATE INDEX IF NOT EXISTS idx_radar_items_published ON radar_items(published_at);
CREATE INDEX IF NOT EXISTS idx_radar_items_discovered ON radar_items(discovered_at);
CREATE INDEX IF NOT EXISTS idx_radar_items_group ON radar_items(publisher_group);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('005_realtime_radar');
