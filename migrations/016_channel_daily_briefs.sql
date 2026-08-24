PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ben_channel_profiles (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    channel_type TEXT NOT NULL CHECK (
        channel_type IN ('SIGNAL_HEAVY', 'EVENT_HEAVY', 'CROSS_ENTITY')
    ),
    profile_version TEXT NOT NULL,
    profile_status TEXT NOT NULL,
    market TEXT NOT NULL DEFAULT 'TW',
    timezone TEXT NOT NULL DEFAULT 'Asia/Taipei',
    primary_build_time TEXT NOT NULL,
    daily_target INTEGER NOT NULL CHECK (daily_target > 0),
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (channel_id, profile_version)
);

CREATE TABLE IF NOT EXISTS ben_channel_brief_runs (
    id TEXT PRIMARY KEY,
    market TEXT NOT NULL,
    market_session_date TEXT NOT NULL,
    session_state TEXT NOT NULL CHECK (
        session_state IN ('WAITING_FOR_CLOSE', 'SOURCE_PENDING', 'READY', 'DEGRADED', 'FAILED')
    ),
    scheduled_for TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    data_as_of TEXT NOT NULL,
    replay_mode INTEGER NOT NULL DEFAULT 0 CHECK (replay_mode IN (0, 1)),
    source_readiness_json TEXT NOT NULL,
    coverage_status TEXT NOT NULL,
    ranking_method TEXT NOT NULL CHECK (
        ranking_method IN ('AI_RANKED', 'RULE_BASED_FALLBACK')
    ),
    ranking_detail_json TEXT NOT NULL DEFAULT '{}',
    config_version TEXT NOT NULL,
    input_fingerprint TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    error_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ben_channel_daily_briefs (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES ben_channel_brief_runs(id),
    profile_id TEXT NOT NULL REFERENCES ben_channel_profiles(id),
    channel_id TEXT NOT NULL,
    market_session_date TEXT NOT NULL,
    brief_version INTEGER NOT NULL CHECK (brief_version > 0),
    status TEXT NOT NULL CHECK (status IN ('READY', 'HONEST_SHORTAGE', 'UNAVAILABLE')),
    target_count INTEGER NOT NULL CHECK (target_count > 0),
    qualified_count INTEGER NOT NULL CHECK (qualified_count >= 0),
    ranking_method TEXT NOT NULL CHECK (
        ranking_method IN ('AI_RANKED', 'RULE_BASED_FALLBACK')
    ),
    shortage_reasons_json TEXT NOT NULL DEFAULT '[]',
    generated_at TEXT NOT NULL,
    data_as_of TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (channel_id, market_session_date, brief_version)
);

CREATE TABLE IF NOT EXISTS ben_channel_topic_assignments (
    id TEXT PRIMARY KEY,
    brief_id TEXT NOT NULL REFERENCES ben_channel_daily_briefs(id),
    candidate_id TEXT NOT NULL,
    candidate_type TEXT NOT NULL CHECK (
        candidate_type IN ('MARKET_SIGNAL', 'DISCLOSURE', 'NEWS_EVENT', 'X_EVENT', 'CROSS_ENTITY')
    ),
    candidate_rank INTEGER NOT NULL CHECK (candidate_rank > 0),
    candidate_tier TEXT NOT NULL CHECK (candidate_tier IN ('PRIMARY', 'BACKUP')),
    editorial_status TEXT NOT NULL CHECK (
        editorial_status IN ('READY_TO_PITCH', 'NEEDS_RESEARCH', 'WATCH_ONLY')
    ),
    title TEXT NOT NULL,
    why_now_json TEXT NOT NULL,
    why_channel_json TEXT NOT NULL,
    facts_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    opinion_evidence_json TEXT NOT NULL DEFAULT '[]',
    security_ids_json TEXT NOT NULL DEFAULT '[]',
    stock_details_json TEXT NOT NULL DEFAULT '[]',
    industry_keys_json TEXT NOT NULL DEFAULT '[]',
    unknowns_json TEXT NOT NULL DEFAULT '[]',
    risk_flags_json TEXT NOT NULL DEFAULT '[]',
    ranking_reasons_json TEXT NOT NULL,
    candidate_payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (brief_id, candidate_id),
    UNIQUE (brief_id, candidate_rank)
);

CREATE INDEX IF NOT EXISTS idx_ben_channel_profiles_channel
    ON ben_channel_profiles(channel_id, profile_version);
CREATE INDEX IF NOT EXISTS idx_ben_channel_runs_session
    ON ben_channel_brief_runs(market, market_session_date, generated_at);
CREATE INDEX IF NOT EXISTS idx_ben_channel_briefs_channel_session
    ON ben_channel_daily_briefs(channel_id, market_session_date, brief_version);
CREATE INDEX IF NOT EXISTS idx_ben_channel_assignments_brief_rank
    ON ben_channel_topic_assignments(brief_id, candidate_rank);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('016_channel_daily_briefs');
