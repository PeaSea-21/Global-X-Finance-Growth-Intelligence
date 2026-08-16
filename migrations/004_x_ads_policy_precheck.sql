ALTER TABLE policy_snapshots ADD COLUMN jurisdiction TEXT NOT NULL DEFAULT 'GLOBAL';
ALTER TABLE policy_snapshots ADD COLUMN product_category TEXT NOT NULL DEFAULT 'ALL';
ALTER TABLE policy_snapshots ADD COLUMN source_url TEXT;
ALTER TABLE policy_snapshots ADD COLUMN page_updated_at TEXT NOT NULL DEFAULT 'UNKNOWN';
ALTER TABLE policy_snapshots ADD COLUMN normalized_summary TEXT NOT NULL DEFAULT '';
ALTER TABLE policy_snapshots ADD COLUMN snapshot_version TEXT NOT NULL DEFAULT 'v1';
ALTER TABLE policy_snapshots ADD COLUMN supersedes_snapshot_id TEXT REFERENCES policy_snapshots(id);
ALTER TABLE policy_snapshots ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'UNKNOWN';

UPDATE policy_snapshots
SET source_url = policy_url
WHERE source_url IS NULL;

CREATE TABLE IF NOT EXISTS policy_rules (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    country TEXT NOT NULL CHECK (country IN ('GLOBAL', 'TW', 'US')),
    product_category TEXT NOT NULL CHECK (
        product_category IN ('ALL', 'FINANCIAL_SERVICES', 'CRYPTO')
    ),
    rule_type TEXT NOT NULL CHECK (
        rule_type IN ('PROHIBITED', 'RESTRICTED', 'REQUIRED', 'DISCLOSURE', 'ACCOUNT_ELIGIBILITY')
    ),
    requirement TEXT NOT NULL,
    result_if_violated TEXT NOT NULL CHECK (
        result_if_violated IN ('BLOCKED', 'REVIEW_REQUIRED', 'UNKNOWN')
    ),
    evidence_url TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES policy_snapshots(id),
    verified_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (rule_id, snapshot_id)
);

CREATE TABLE IF NOT EXISTS policy_checklist_templates (
    id TEXT PRIMARY KEY,
    checklist_id TEXT NOT NULL,
    checklist_name TEXT NOT NULL,
    country TEXT NOT NULL CHECK (country IN ('TW', 'US')),
    product_category TEXT NOT NULL CHECK (
        product_category IN ('FINANCIAL_SERVICES', 'CRYPTO')
    ),
    fields_json TEXT NOT NULL,
    policy_snapshot_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'SUPERSEDED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (checklist_id, policy_snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_policy_snapshots_source_version
    ON policy_snapshots(source_url, snapshot_version);
CREATE INDEX IF NOT EXISTS idx_policy_snapshots_verification
    ON policy_snapshots(verification_status, fetched_at);
CREATE INDEX IF NOT EXISTS idx_policy_rules_country_category
    ON policy_rules(country, product_category, rule_type);
CREATE INDEX IF NOT EXISTS idx_policy_rules_snapshot ON policy_rules(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_policy_checklists_country_category
    ON policy_checklist_templates(country, product_category, status);
