PRAGMA foreign_keys = ON;

ALTER TABLE radar_items ADD COLUMN is_initial_backfill INTEGER NOT NULL DEFAULT 1
    CHECK (is_initial_backfill IN (0, 1));

CREATE INDEX IF NOT EXISTS idx_radar_items_backfill ON radar_items(is_initial_backfill);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('007_radar_backfill_marker');
