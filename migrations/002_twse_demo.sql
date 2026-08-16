PRAGMA foreign_keys = ON;

ALTER TABLE collection_runs ADD COLUMN batch_id TEXT;
ALTER TABLE collection_runs ADD COLUMN endpoint TEXT;
ALTER TABLE collection_runs ADD COLUMN dataset_name TEXT;
ALTER TABLE collection_runs ADD COLUMN new_item_count INTEGER NOT NULL DEFAULT 0 CHECK (new_item_count >= 0);
ALTER TABLE collection_runs ADD COLUMN duplicate_item_count INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_item_count >= 0);

CREATE INDEX IF NOT EXISTS idx_collection_runs_batch ON collection_runs(batch_id);
CREATE INDEX IF NOT EXISTS idx_collection_runs_endpoint ON collection_runs(endpoint);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('002_twse_demo');

