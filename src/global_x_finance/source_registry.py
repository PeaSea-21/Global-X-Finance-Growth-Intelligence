from __future__ import annotations

import csv
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .errors import ValidationError


REQUIRED_COLUMNS = {
    "source_id", "source_url", "publisher", "publisher_group", "market",
    "market_code", "source_type", "signal_role", "reliability_level",
    "verified_at", "evidence_url", "registry_status", "collection_status",
    "collection_method", "notes",
}
ACTIVE_REQUIRED_FIELDS = {
    "source_url", "publisher", "publisher_group", "market", "market_code",
    "verified_at", "evidence_url",
}
ALLOWED_RELIABILITY = {"A", "B", "C", "D", "UNKNOWN"}


@dataclass(frozen=True)
class RegistryReport:
    rows: list[dict[str, str]]
    active_count: int
    api_verified_count: int
    blocked_source_ids: tuple[str, ...]


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_registry(path: str | Path) -> RegistryReport:
    registry_path = Path(path)
    with registry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - headers)
        if missing_columns:
            raise ValidationError(f"Missing registry columns: {', '.join(missing_columns)}")
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]

    errors: list[str] = []
    seen_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        prefix = f"line {line_number} ({row.get('source_id') or 'missing source_id'})"
        if not row.get("source_id"):
            errors.append(f"{prefix}: source_id is required")
        elif row["source_id"] in seen_ids:
            errors.append(f"{prefix}: duplicate source_id")
        seen_ids.add(row.get("source_id", ""))

        if row.get("registry_status") == "ACTIVE":
            missing = sorted(field for field in ACTIVE_REQUIRED_FIELDS if not row.get(field))
            if missing:
                errors.append(f"{prefix}: ACTIVE source missing {', '.join(missing)}")

        for field in ("source_url", "evidence_url"):
            value = row.get(field, "")
            if value and not _is_http_url(value):
                errors.append(f"{prefix}: {field} must be an http(s) URL")
        if row.get("verified_at"):
            try:
                date.fromisoformat(row["verified_at"])
            except ValueError:
                errors.append(f"{prefix}: verified_at must use YYYY-MM-DD")
        if row.get("reliability_level") not in ALLOWED_RELIABILITY:
            errors.append(f"{prefix}: invalid reliability_level")

    if errors:
        raise ValidationError("Invalid source registry:\n" + "\n".join(errors))

    return RegistryReport(
        rows=rows,
        active_count=sum(row["registry_status"] == "ACTIVE" for row in rows),
        api_verified_count=sum(row["collection_status"] == "API_VERIFIED" for row in rows),
        blocked_source_ids=tuple(
            row["source_id"]
            for row in rows
            if row["collection_status"] in {
                "BLOCKED_ROBOTS_OR_NEEDS_PERMISSION",
                "NEEDS_TERMS_REVIEW",
                "NEEDS_LICENSE_OR_TERMS_REVIEW",
            }
        ),
    )


def import_registry(connection: sqlite3.Connection, report: RegistryReport) -> int:
    markets = {
        row["country_code"]: {"id": row["id"], "country": row["country"]}
        for row in connection.execute("SELECT id, country_code, country FROM markets")
    }
    missing_markets = sorted({row["market_code"] for row in report.rows} - set(markets))
    if missing_markets:
        raise ValidationError(
            "Registry references markets not initialized from a Market Pack: "
            + ", ".join(missing_markets)
        )
    mismatched_names = [
        row["source_id"]
        for row in report.rows
        if row["market"] != markets[row["market_code"]]["country"]
    ]
    if mismatched_names:
        raise ValidationError(
            "Registry market name does not match its Market Pack: "
            + ", ".join(mismatched_names)
        )

    with connection:
        for row in report.rows:
            existing = connection.execute(
                "SELECT id FROM sources WHERE source_id = ?", (row["source_id"],)
            ).fetchone()
            internal_id = existing["id"] if existing else str(uuid.uuid4())
            metadata = json.dumps(
                {
                    "market_name": row["market"],
                    "market_code": row["market_code"],
                    "collection_method": row["collection_method"],
                    "notes": row["notes"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            connection.execute(
                """
                INSERT INTO sources (
                    id, source_id, source_url, publisher, publisher_group,
                    market_id, source_type, signal_role, reliability_level,
                    verified_at, evidence_url, registry_status,
                    collection_status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    source_url = excluded.source_url,
                    publisher = excluded.publisher,
                    publisher_group = excluded.publisher_group,
                    market_id = excluded.market_id,
                    source_type = excluded.source_type,
                    signal_role = excluded.signal_role,
                    reliability_level = excluded.reliability_level,
                    verified_at = excluded.verified_at,
                    evidence_url = excluded.evidence_url,
                    registry_status = excluded.registry_status,
                    collection_status = excluded.collection_status,
                    metadata_json = excluded.metadata_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    internal_id, row["source_id"], row["source_url"], row["publisher"],
                    row["publisher_group"], markets[row["market_code"]]["id"], row["source_type"],
                    row["signal_role"], row["reliability_level"], row["verified_at"],
                    row["evidence_url"], row["registry_status"], row["collection_status"],
                    metadata,
                ),
            )
    return len(report.rows)
