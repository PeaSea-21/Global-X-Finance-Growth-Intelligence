PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ben_x_accounts (
    id TEXT PRIMARY KEY,
    handle TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    follower_snapshot INTEGER,
    region TEXT NOT NULL DEFAULT '',
    profile_url TEXT NOT NULL,
    account_role TEXT NOT NULL,
    market_scope TEXT NOT NULL,
    impact_path TEXT NOT NULL DEFAULT '',
    account_priority TEXT NOT NULL CHECK (
        account_priority IN ('CORE','WATCH','LOW_CONFIDENCE')
    ),
    usage_note TEXT NOT NULL DEFAULT '',
    publisher_group TEXT NOT NULL,
    expected_interval_minutes INTEGER NOT NULL CHECK (
        expected_interval_minutes IN (10,30,60)
    ),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
    last_success_timestamp INTEGER,
    last_run_at TEXT,
    monitoring_status TEXT NOT NULL DEFAULT 'NOT_STARTED' CHECK (
        monitoring_status IN (
            'NOT_STARTED','SUCCESS','NO_NEW','PRIVATE','NOT_FOUND',
            'RATE_LIMITED','FAILED','DISABLED'
        )
    ),
    last_http_status INTEGER,
    last_error TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0 CHECK (consecutive_failures >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ben_x_runs (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES ben_x_accounts(id),
    attempted_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('SUCCESS','NO_NEW','PRIVATE','NOT_FOUND','RATE_LIMITED','FAILED','DISABLED')
    ),
    http_status INTEGER,
    retry_after TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    fetched_count INTEGER NOT NULL DEFAULT 0 CHECK (fetched_count >= 0),
    kept_count INTEGER NOT NULL DEFAULT 0 CHECK (kept_count >= 0),
    new_count INTEGER NOT NULL DEFAULT 0 CHECK (new_count >= 0),
    duplicate_count INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_count >= 0),
    repost_count INTEGER NOT NULL DEFAULT 0 CHECK (repost_count >= 0),
    error_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ben_x_posts (
    id TEXT PRIMARY KEY,
    raw_item_id TEXT NOT NULL UNIQUE REFERENCES raw_items(id),
    account_id TEXT NOT NULL REFERENCES ben_x_accounts(id),
    platform TEXT NOT NULL DEFAULT 'X' CHECK (platform = 'X'),
    post_id TEXT NOT NULL,
    author_handle TEXT NOT NULL,
    author_name TEXT NOT NULL,
    publisher_group TEXT NOT NULL,
    account_role TEXT NOT NULL,
    account_priority TEXT NOT NULL,
    original_text TEXT NOT NULL,
    original_language TEXT NOT NULL DEFAULT 'UNKNOWN',
    created_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    original_url TEXT NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    reposts INTEGER NOT NULL DEFAULT 0,
    quotes INTEGER NOT NULL DEFAULT 0,
    replies INTEGER NOT NULL DEFAULT 0,
    views INTEGER,
    follower_count INTEGER,
    follower_count_source TEXT NOT NULL CHECK (
        follower_count_source IN ('FXTWITTER','CSV_SNAPSHOT','UNKNOWN')
    ),
    external_urls_json TEXT NOT NULL DEFAULT '[]',
    mentioned_accounts_json TEXT NOT NULL DEFAULT '[]',
    hashtags_json TEXT NOT NULL DEFAULT '[]',
    related_companies_json TEXT NOT NULL DEFAULT '[]',
    related_tickers_json TEXT NOT NULL DEFAULT '[]',
    is_repost INTEGER NOT NULL DEFAULT 0 CHECK (is_repost IN (0,1)),
    is_quote INTEGER NOT NULL DEFAULT 0 CHECK (is_quote IN (0,1)),
    quoted_post_id TEXT,
    raw_source_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_engagement_at TEXT NOT NULL,
    UNIQUE(platform, post_id)
);

CREATE TABLE IF NOT EXISTS ben_x_engagement_snapshots (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    reposts INTEGER NOT NULL DEFAULT 0,
    quotes INTEGER NOT NULL DEFAULT 0,
    replies INTEGER NOT NULL DEFAULT 0,
    views INTEGER,
    follower_count INTEGER,
    UNIQUE(post_id, fetched_at)
);

CREATE TABLE IF NOT EXISTS ben_translation_cache (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    target_language TEXT NOT NULL CHECK (target_language IN ('zh-tw','zh-cn')),
    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    translation_status TEXT NOT NULL CHECK (
        translation_status IN ('OPENCC_CONVERTED','NOT_AVAILABLE','ORIGINAL_CHINESE')
    ),
    translation_method TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_hash, target_language)
);

CREATE TABLE IF NOT EXISTS ben_endpoint_diagnostics (
    id TEXT PRIMARY KEY,
    source_key TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    request_method TEXT NOT NULL DEFAULT 'GET',
    attempted_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    http_status INTEGER,
    retry_after TEXT,
    rate_limit_headers_json TEXT NOT NULL DEFAULT '{}',
    content_type TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    final_status TEXT NOT NULL CHECK (
        final_status IN ('SUCCESS','DEGRADED_RATE_LIMITED','FAILED')
    ),
    error_reason TEXT,
    response_excerpt TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ben_x_accounts_priority ON ben_x_accounts(account_priority, enabled);
CREATE INDEX IF NOT EXISTS idx_ben_x_runs_account_time ON ben_x_runs(account_id, attempted_at);
CREATE INDEX IF NOT EXISTS idx_ben_x_posts_created ON ben_x_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_ben_x_posts_group ON ben_x_posts(publisher_group);
CREATE INDEX IF NOT EXISTS idx_ben_x_posts_author ON ben_x_posts(author_handle);
CREATE INDEX IF NOT EXISTS idx_ben_endpoint_diag_source_time ON ben_endpoint_diagnostics(source_key, attempted_at);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('011_ben_x_intelligence');
