PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS markets (
    id TEXT PRIMARY KEY,
    country_code TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL,
    primary_language TEXT NOT NULL,
    timezone TEXT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_pack_versions (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES markets(id),
    version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    config_json TEXT NOT NULL,
    status TEXT NOT NULL,
    effective_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (market_id, version)
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    publisher TEXT NOT NULL,
    publisher_group TEXT NOT NULL,
    market_id TEXT NOT NULL REFERENCES markets(id),
    source_type TEXT NOT NULL,
    signal_role TEXT NOT NULL,
    reliability_level TEXT NOT NULL CHECK (reliability_level IN ('A','B','C','D','UNKNOWN')),
    verified_at TEXT NOT NULL,
    evidence_url TEXT NOT NULL,
    registry_status TEXT NOT NULL,
    collection_status TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        registry_status <> 'ACTIVE' OR
        (length(trim(source_url)) > 0 AND length(trim(publisher)) > 0 AND
         length(trim(publisher_group)) > 0 AND length(trim(verified_at)) > 0 AND
         length(trim(evidence_url)) > 0)
    )
);

CREATE TABLE IF NOT EXISTS collection_runs (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES markets(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    item_count INTEGER NOT NULL DEFAULT 0 CHECK (item_count >= 0),
    error_code TEXT,
    error_message TEXT,
    collector_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_items (
    id TEXT PRIMARY KEY,
    collection_run_id TEXT REFERENCES collection_runs(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    original_url TEXT,
    canonical_url TEXT,
    original_content TEXT NOT NULL,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    raw_payload_json TEXT NOT NULL,
    data_label TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (original_url IS NOT NULL OR length(trim(content_hash)) > 0),
    UNIQUE (source_id, original_url),
    UNIQUE (source_id, content_hash)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_items_original_url
    ON raw_items(original_url) WHERE original_url IS NOT NULL AND original_url <> '';
CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_items_content_hash
    ON raw_items(content_hash);

CREATE TRIGGER IF NOT EXISTS raw_items_evidence_immutable
BEFORE UPDATE OF original_content, raw_payload_json, original_url, content_hash ON raw_items
FOR EACH ROW
WHEN NEW.original_content IS NOT OLD.original_content
  OR NEW.raw_payload_json IS NOT OLD.raw_payload_json
  OR NEW.original_url IS NOT OLD.original_url
  OR NEW.content_hash IS NOT OLD.content_hash
BEGIN
    SELECT RAISE(ABORT, 'raw evidence fields are immutable');
END;

CREATE TABLE IF NOT EXISTS normalized_items (
    id TEXT PRIMARY KEY,
    raw_item_id TEXT NOT NULL UNIQUE REFERENCES raw_items(id),
    language TEXT NOT NULL,
    title TEXT,
    body TEXT NOT NULL,
    author TEXT,
    normalized_published_at TEXT,
    normalization_version TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    market_id TEXT REFERENCES markets(id),
    identifiers_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS item_entities (
    item_id TEXT NOT NULL REFERENCES normalized_items(id),
    entity_id TEXT NOT NULL REFERENCES entities(id),
    relation_type TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id, entity_id, relation_type)
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES markets(id),
    topic_key TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    clustering_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (market_id, topic_key)
);

CREATE TABLE IF NOT EXISTS topic_items (
    topic_id TEXT NOT NULL REFERENCES topics(id),
    normalized_item_id TEXT NOT NULL REFERENCES normalized_items(id),
    relevance_score REAL NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (topic_id, normalized_item_id)
);

CREATE TABLE IF NOT EXISTS trend_snapshots (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id),
    measured_at TEXT NOT NULL,
    trend_score REAL,
    audience_fit REAL,
    commercial_fit REAL,
    commercial_fit_type TEXT NOT NULL CHECK (commercial_fit_type = 'PREDICTED'),
    compliance_risk TEXT NOT NULL DEFAULT 'UNKNOWN',
    independent_source_count INTEGER NOT NULL DEFAULT 0 CHECK (independent_source_count >= 0),
    metrics_json TEXT NOT NULL DEFAULT '{}',
    scoring_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    topic_id TEXT REFERENCES topics(id),
    normalized_item_id TEXT REFERENCES normalized_items(id),
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('UNVERIFIED','SUPPORTED','REFUTED','SOURCE_CONFLICT','UNKNOWN')),
    subject_entity_id TEXT REFERENCES entities(id),
    asserted_at TEXT,
    extractor_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_links (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    raw_item_id TEXT NOT NULL REFERENCES raw_items(id),
    relation TEXT NOT NULL CHECK (relation IN ('SUPPORTS','CONTRADICTS','CONTEXT')),
    excerpt TEXT,
    source_url TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (claim_id, raw_item_id, relation)
);

CREATE TABLE IF NOT EXISTS content_drafts (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES markets(id),
    topic_id TEXT NOT NULL REFERENCES topics(id),
    account_profile_id TEXT,
    draft_type TEXT NOT NULL CHECK (draft_type IN ('ORGANIC','PROMOTED')),
    body TEXT NOT NULL,
    cta TEXT,
    commercial_fit_type TEXT NOT NULL CHECK (commercial_fit_type = 'PREDICTED'),
    commercial_fit_score REAL CHECK (commercial_fit_score IS NULL OR (commercial_fit_score >= 0 AND commercial_fit_score <= 1)),
    status TEXT NOT NULL,
    generation_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_runs (
    id TEXT PRIMARY KEY,
    content_draft_id TEXT REFERENCES content_drafts(id),
    topic_id TEXT REFERENCES topics(id),
    verifier_type TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    result TEXT NOT NULL,
    findings_json TEXT NOT NULL DEFAULT '{}',
    evidence_read_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policy_snapshots (
    id TEXT PRIMARY KEY,
    market_id TEXT REFERENCES markets(id),
    policy_name TEXT NOT NULL,
    policy_url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content_text TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (policy_url, content_hash)
);

CREATE TABLE IF NOT EXISTS compliance_checks (
    id TEXT PRIMARY KEY,
    content_draft_id TEXT NOT NULL REFERENCES content_drafts(id),
    policy_snapshot_id TEXT REFERENCES policy_snapshots(id),
    result TEXT NOT NULL CHECK (result IN ('PASS_PRECHECK','REVIEW_REQUIRED','BLOCKED','UNKNOWN')),
    risk_level TEXT NOT NULL,
    findings_json TEXT NOT NULL DEFAULT '{}',
    product_info_status TEXT NOT NULL DEFAULT 'UNKNOWN' CHECK (product_info_status IN ('PROVIDED','UNKNOWN','NEEDS_VERIFICATION')),
    advertiser_license_status TEXT NOT NULL DEFAULT 'UNKNOWN' CHECK (advertiser_license_status IN ('PROVIDED','UNKNOWN','NEEDS_VERIFICATION')),
    checked_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
      result <> 'PASS_PRECHECK' OR
      (product_info_status = 'PROVIDED' AND advertiser_license_status = 'PROVIDED')
    )
);

CREATE TABLE IF NOT EXISTS review_decisions (
    id TEXT PRIMARY KEY,
    content_draft_id TEXT REFERENCES content_drafts(id),
    topic_id TEXT REFERENCES topics(id),
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT,
    decided_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_pack_versions_market ON market_pack_versions(market_id);
CREATE INDEX IF NOT EXISTS idx_market_pack_versions_effective ON market_pack_versions(effective_at);
CREATE INDEX IF NOT EXISTS idx_sources_market ON sources(market_id);
CREATE INDEX IF NOT EXISTS idx_sources_publisher_group ON sources(publisher_group);
CREATE INDEX IF NOT EXISTS idx_sources_verified_at ON sources(verified_at);
CREATE INDEX IF NOT EXISTS idx_collection_runs_market ON collection_runs(market_id);
CREATE INDEX IF NOT EXISTS idx_collection_runs_source ON collection_runs(source_id);
CREATE INDEX IF NOT EXISTS idx_collection_runs_started ON collection_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_raw_items_source ON raw_items(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_items_run ON raw_items(collection_run_id);
CREATE INDEX IF NOT EXISTS idx_raw_items_published ON raw_items(published_at);
CREATE INDEX IF NOT EXISTS idx_raw_items_fetched ON raw_items(fetched_at);
CREATE INDEX IF NOT EXISTS idx_normalized_items_published ON normalized_items(normalized_published_at);
CREATE INDEX IF NOT EXISTS idx_entities_market ON entities(market_id);
CREATE INDEX IF NOT EXISTS idx_item_entities_entity ON item_entities(entity_id);
CREATE INDEX IF NOT EXISTS idx_topics_market ON topics(market_id);
CREATE INDEX IF NOT EXISTS idx_topics_first_seen ON topics(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_topics_last_seen ON topics(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_topic_items_item ON topic_items(normalized_item_id);
CREATE INDEX IF NOT EXISTS idx_trend_snapshots_topic ON trend_snapshots(topic_id);
CREATE INDEX IF NOT EXISTS idx_trend_snapshots_measured ON trend_snapshots(measured_at);
CREATE INDEX IF NOT EXISTS idx_claims_topic ON claims(topic_id);
CREATE INDEX IF NOT EXISTS idx_claims_item ON claims(normalized_item_id);
CREATE INDEX IF NOT EXISTS idx_claims_subject ON claims(subject_entity_id);
CREATE INDEX IF NOT EXISTS idx_claims_asserted ON claims(asserted_at);
CREATE INDEX IF NOT EXISTS idx_evidence_links_claim ON evidence_links(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_links_raw ON evidence_links(raw_item_id);
CREATE INDEX IF NOT EXISTS idx_evidence_links_observed ON evidence_links(observed_at);
CREATE INDEX IF NOT EXISTS idx_content_drafts_market ON content_drafts(market_id);
CREATE INDEX IF NOT EXISTS idx_content_drafts_topic ON content_drafts(topic_id);
CREATE INDEX IF NOT EXISTS idx_verification_runs_draft ON verification_runs(content_draft_id);
CREATE INDEX IF NOT EXISTS idx_verification_runs_topic ON verification_runs(topic_id);
CREATE INDEX IF NOT EXISTS idx_verification_runs_started ON verification_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_policy_snapshots_market ON policy_snapshots(market_id);
CREATE INDEX IF NOT EXISTS idx_policy_snapshots_fetched ON policy_snapshots(fetched_at);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_draft ON compliance_checks(content_draft_id);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_policy ON compliance_checks(policy_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_checked ON compliance_checks(checked_at);
CREATE INDEX IF NOT EXISTS idx_review_decisions_draft ON review_decisions(content_draft_id);
CREATE INDEX IF NOT EXISTS idx_review_decisions_topic ON review_decisions(topic_id);
CREATE INDEX IF NOT EXISTS idx_review_decisions_decided ON review_decisions(decided_at);

-- Audit-time indexes. SQLite does not create these automatically for timestamps.
CREATE INDEX IF NOT EXISTS idx_markets_created ON markets(created_at);
CREATE INDEX IF NOT EXISTS idx_markets_updated ON markets(updated_at);
CREATE INDEX IF NOT EXISTS idx_market_pack_versions_created ON market_pack_versions(created_at);
CREATE INDEX IF NOT EXISTS idx_sources_created ON sources(created_at);
CREATE INDEX IF NOT EXISTS idx_sources_updated ON sources(updated_at);
CREATE INDEX IF NOT EXISTS idx_collection_runs_finished ON collection_runs(finished_at);
CREATE INDEX IF NOT EXISTS idx_collection_runs_created ON collection_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_raw_items_created ON raw_items(created_at);
CREATE INDEX IF NOT EXISTS idx_normalized_items_created ON normalized_items(created_at);
CREATE INDEX IF NOT EXISTS idx_normalized_items_updated ON normalized_items(updated_at);
CREATE INDEX IF NOT EXISTS idx_entities_created ON entities(created_at);
CREATE INDEX IF NOT EXISTS idx_entities_updated ON entities(updated_at);
CREATE INDEX IF NOT EXISTS idx_item_entities_created ON item_entities(created_at);
CREATE INDEX IF NOT EXISTS idx_topics_created ON topics(created_at);
CREATE INDEX IF NOT EXISTS idx_topics_updated ON topics(updated_at);
CREATE INDEX IF NOT EXISTS idx_topic_items_created ON topic_items(created_at);
CREATE INDEX IF NOT EXISTS idx_trend_snapshots_created ON trend_snapshots(created_at);
CREATE INDEX IF NOT EXISTS idx_claims_created ON claims(created_at);
CREATE INDEX IF NOT EXISTS idx_claims_updated ON claims(updated_at);
CREATE INDEX IF NOT EXISTS idx_evidence_links_created ON evidence_links(created_at);
CREATE INDEX IF NOT EXISTS idx_content_drafts_created ON content_drafts(created_at);
CREATE INDEX IF NOT EXISTS idx_content_drafts_updated ON content_drafts(updated_at);
CREATE INDEX IF NOT EXISTS idx_verification_runs_finished ON verification_runs(finished_at);
CREATE INDEX IF NOT EXISTS idx_verification_runs_created ON verification_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_policy_snapshots_created ON policy_snapshots(created_at);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_created ON compliance_checks(created_at);
CREATE INDEX IF NOT EXISTS idx_review_decisions_created ON review_decisions(created_at);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('001_initial');
