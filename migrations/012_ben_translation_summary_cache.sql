PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ben_translation_summary_cache (
    id TEXT PRIMARY KEY,
    cache_key TEXT NOT NULL UNIQUE,
    source_hash TEXT NOT NULL,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL CHECK (target_language IN ('zh-tw','zh-cn')),
    source_text TEXT NOT NULL,
    title_zh TEXT NOT NULL,
    summary_zh TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('ORIGINAL_CHINESE','MODEL_TRANSLATED','RULE_FALLBACK','TRANSLATION_UNAVAILABLE','ERROR')
    ),
    method TEXT NOT NULL,
    model_name TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    error_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ben_translation_summary_hash
    ON ben_translation_summary_cache(source_hash, target_language);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('012_ben_translation_summary_cache');
