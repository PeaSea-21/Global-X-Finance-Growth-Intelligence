PRAGMA foreign_keys = ON;

ALTER TABLE realtime_sources ADD COLUMN identity_verified TEXT NOT NULL DEFAULT 'UNKNOWN'
    CHECK (identity_verified IN ('VERIFIED','NOT_VERIFIED','UNKNOWN'));
ALTER TABLE realtime_sources ADD COLUMN endpoint_verified TEXT NOT NULL DEFAULT 'UNKNOWN'
    CHECK (endpoint_verified IN ('VERIFIED','NOT_VERIFIED','UNKNOWN'));
ALTER TABLE realtime_sources ADD COLUMN monitoring_method_verified TEXT NOT NULL DEFAULT 'UNKNOWN'
    CHECK (monitoring_method_verified IN ('VERIFIED','NOT_VERIFIED','UNKNOWN'));
ALTER TABLE realtime_sources ADD COLUMN terms_status TEXT NOT NULL DEFAULT 'UNKNOWN'
    CHECK (terms_status IN ('ALLOWED','MANUAL_ONLY','BLOCKED','UNKNOWN'));
ALTER TABLE realtime_sources ADD COLUMN commercial_use_status TEXT NOT NULL DEFAULT 'UNKNOWN'
    CHECK (commercial_use_status IN ('ALLOWED','MANUAL_ONLY','BLOCKED','UNKNOWN'));
ALTER TABLE realtime_sources ADD COLUMN runtime_status TEXT NOT NULL DEFAULT 'NOT_STARTED';

UPDATE realtime_sources
SET runtime_status = monitoring_status,
    monitoring_status = CASE source_status
        WHEN 'VERIFIED_ACTIVE' THEN 'ACTIVE'
        WHEN 'VERIFIED_MANUAL_ONLY' THEN 'MANUAL_ONLY'
        WHEN 'BLOCKED' THEN 'BLOCKED'
        ELSE 'NEEDS_VERIFICATION'
    END;

CREATE TRIGGER IF NOT EXISTS realtime_sources_monitoring_status_insert
BEFORE INSERT ON realtime_sources
FOR EACH ROW
WHEN NEW.monitoring_status NOT IN ('ACTIVE','MANUAL_ONLY','NEEDS_VERIFICATION','BLOCKED')
BEGIN
    SELECT RAISE(ABORT, 'invalid monitoring_status');
END;

CREATE TRIGGER IF NOT EXISTS realtime_sources_monitoring_status_update
BEFORE UPDATE OF monitoring_status ON realtime_sources
FOR EACH ROW
WHEN NEW.monitoring_status NOT IN ('ACTIVE','MANUAL_ONLY','NEEDS_VERIFICATION','BLOCKED')
BEGIN
    SELECT RAISE(ABORT, 'invalid monitoring_status');
END;

CREATE TRIGGER IF NOT EXISTS realtime_sources_active_governance_insert
BEFORE INSERT ON realtime_sources
FOR EACH ROW
WHEN NEW.monitoring_status = 'ACTIVE' AND (
    NEW.identity_verified <> 'VERIFIED' OR
    NEW.endpoint_verified <> 'VERIFIED' OR
    NEW.monitoring_method_verified <> 'VERIFIED' OR
    NEW.terms_status = 'BLOCKED' OR
    NEW.commercial_use_status = 'BLOCKED' OR
    NEW.expected_interval_minutes IS NULL
)
BEGIN
    SELECT RAISE(ABORT, 'ACTIVE requires verified identity, endpoint, method, interval, and no blocked rights status');
END;

CREATE TRIGGER IF NOT EXISTS realtime_sources_active_governance_update
BEFORE UPDATE OF monitoring_status, identity_verified, endpoint_verified,
                 monitoring_method_verified, terms_status, commercial_use_status,
                 expected_interval_minutes ON realtime_sources
FOR EACH ROW
WHEN NEW.monitoring_status = 'ACTIVE' AND (
    NEW.identity_verified <> 'VERIFIED' OR
    NEW.endpoint_verified <> 'VERIFIED' OR
    NEW.monitoring_method_verified <> 'VERIFIED' OR
    NEW.terms_status = 'BLOCKED' OR
    NEW.commercial_use_status = 'BLOCKED' OR
    NEW.expected_interval_minutes IS NULL
)
BEGIN
    SELECT RAISE(ABORT, 'ACTIVE requires verified identity, endpoint, method, interval, and no blocked rights status');
END;

CREATE INDEX IF NOT EXISTS idx_realtime_sources_monitoring_status
    ON realtime_sources(monitoring_status);
CREATE INDEX IF NOT EXISTS idx_realtime_sources_terms_status
    ON realtime_sources(terms_status);
CREATE INDEX IF NOT EXISTS idx_realtime_sources_commercial_use_status
    ON realtime_sources(commercial_use_status);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('008_source_governance_separation');
