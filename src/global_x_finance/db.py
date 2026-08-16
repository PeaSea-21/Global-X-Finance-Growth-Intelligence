from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Iterable


def connect(database: str | Path) -> sqlite3.Connection:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def apply_migrations(connection: sqlite3.Connection, migrations_dir: str | Path) -> list[str]:
    applied: list[str] = []
    for migration in sorted(Path(migrations_dir).glob("*.sql")):
        version = migration.stem
        migration_table_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if migration_table_exists:
            already_applied = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()
            if already_applied:
                continue
        connection.executescript(migration.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)", (version,)
        )
        connection.commit()
        applied.append(migration.name)
    return applied


def register_market_packs(connection: sqlite3.Connection, packs: Iterable[dict]) -> None:
    with connection:
        for pack in packs:
            row = connection.execute(
                "SELECT id FROM markets WHERE country_code = ?", (pack["country_code"],)
            ).fetchone()
            market_id = row["id"] if row else str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO markets (
                    id, country_code, country, primary_language, timezone,
                    currency, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(country_code) DO UPDATE SET
                    country = excluded.country,
                    primary_language = excluded.primary_language,
                    timezone = excluded.timezone,
                    currency = excluded.currency,
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    market_id,
                    pack["country_code"],
                    pack["country"],
                    pack["primary_language"],
                    pack["timezone"],
                    pack["currency"],
                    pack["status"],
                ),
            )
            version = pack["pack_id"]
            config_json = json.dumps(pack, ensure_ascii=False, sort_keys=True)
            existing = connection.execute(
                "SELECT id FROM market_pack_versions WHERE market_id = ? AND version = ?",
                (market_id, version),
            ).fetchone()
            version_id = existing["id"] if existing else str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO market_pack_versions (
                    id, market_id, version, schema_version, config_json, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(market_id, version) DO UPDATE SET
                    schema_version = excluded.schema_version,
                    config_json = excluded.config_json,
                    status = excluded.status
                """,
                (
                    version_id,
                    market_id,
                    version,
                    pack["schema_version"],
                    config_json,
                    pack["status"],
                ),
            )
