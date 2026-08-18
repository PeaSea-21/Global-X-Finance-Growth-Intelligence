PRAGMA foreign_keys = ON;

DROP TRIGGER IF EXISTS realtime_sources_active_governance_insert;
DROP TRIGGER IF EXISTS realtime_sources_active_governance_update;

CREATE TRIGGER realtime_sources_active_governance_insert
BEFORE INSERT ON realtime_sources
FOR EACH ROW
WHEN NEW.monitoring_status = 'ACTIVE' AND (
    NEW.identity_verified <> 'VERIFIED' OR
    NEW.endpoint_verified <> 'VERIFIED' OR
    NEW.monitoring_method_verified <> 'VERIFIED' OR
    NEW.terms_status IN ('MANUAL_ONLY','BLOCKED') OR
    NEW.commercial_use_status IN ('MANUAL_ONLY','BLOCKED') OR
    NEW.expected_interval_minutes IS NULL
)
BEGIN
    SELECT RAISE(ABORT, 'ACTIVE requires verified identity, endpoint, method, interval, and no manual-only or blocked rights status');
END;

CREATE TRIGGER realtime_sources_active_governance_update
BEFORE UPDATE OF monitoring_status, identity_verified, endpoint_verified,
                 monitoring_method_verified, terms_status, commercial_use_status,
                 expected_interval_minutes ON realtime_sources
FOR EACH ROW
WHEN NEW.monitoring_status = 'ACTIVE' AND (
    NEW.identity_verified <> 'VERIFIED' OR
    NEW.endpoint_verified <> 'VERIFIED' OR
    NEW.monitoring_method_verified <> 'VERIFIED' OR
    NEW.terms_status IN ('MANUAL_ONLY','BLOCKED') OR
    NEW.commercial_use_status IN ('MANUAL_ONLY','BLOCKED') OR
    NEW.expected_interval_minutes IS NULL
)
BEGIN
    SELECT RAISE(ABORT, 'ACTIVE requires verified identity, endpoint, method, interval, and no manual-only or blocked rights status');
END;

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('009_realtime_active_rights_guard');
