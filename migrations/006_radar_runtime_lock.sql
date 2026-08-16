PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS radar_runtime_lock (
    lock_name TEXT PRIMARY KEY,
    owner_id TEXT,
    locked_until TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO radar_runtime_lock(lock_name, owner_id, locked_until)
VALUES ('taiwan_realtime_radar', NULL, '1970-01-01T00:00:00+00:00');

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('006_radar_runtime_lock');
