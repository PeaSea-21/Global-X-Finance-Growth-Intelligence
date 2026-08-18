from __future__ import annotations

import csv
import json
import sqlite3
import sys
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlparse

from .errors import ValidationError
from .evidence import EvidenceStore


SOURCE_STATUSES = {
    "VERIFIED_ACTIVE",
    "VERIFIED_MANUAL_ONLY",
    "NEEDS_VERIFICATION",
    "BLOCKED",
    "UNKNOWN",
}
REQUIRED_REGISTRY_FIELDS = {
    "registry_source_id",
    "platform",
    "source_type",
    "publisher",
    "publisher_group",
    "market",
    "language",
    "category",
    "monitoring_method",
    "source_status",
    "identity_verified",
    "endpoint_verified",
    "monitoring_method_verified",
    "terms_status",
    "commercial_use_status",
    "monitoring_status",
}
VERIFICATION_STATES = {"VERIFIED", "NOT_VERIFIED", "UNKNOWN"}
TERMS_STATES = {"ALLOWED", "MANUAL_ONLY", "BLOCKED", "UNKNOWN"}
COMMERCIAL_USE_STATES = {"ALLOWED", "MANUAL_ONLY", "BLOCKED", "UNKNOWN"}
MONITORING_STATES = {"ACTIVE", "MANUAL_ONLY", "NEEDS_VERIFICATION", "BLOCKED"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    for fmt in (
        "%a %b %d %H:%M:%S %z %Y",
        "%Y-%m-%d %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            return datetime.strptime(raw.replace("Z", "+0000"), fmt).astimezone(timezone.utc)
        except ValueError:
            pass
    try:
        result = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def detection_latency_minutes(published_at: str | None, discovered_at: str) -> float | None:
    published = parse_datetime(published_at)
    discovered = parse_datetime(discovered_at)
    if published is None or discovered is None:
        return None
    return max(0.0, round((discovered - published).total_seconds() / 60.0, 3))


def _valid_http_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_realtime_registry(path: str | Path) -> list[dict[str, str]]:
    registry_path = Path(path)
    if not registry_path.exists():
        raise ValidationError(f"Realtime source registry not found: {registry_path}")
    with registry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_columns = REQUIRED_REGISTRY_FIELDS - set(reader.fieldnames or [])
        if missing_columns:
            raise ValidationError(
                "Realtime registry missing columns: " + ", ".join(sorted(missing_columns))
            )
        rows = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValidationError(f"Row {line_number}: too many CSV fields")
            rows.append({key: (value or "").strip() for key, value in row.items()})

    seen: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        source_id = row["registry_source_id"]
        if not source_id:
            raise ValidationError(f"Row {line_number}: registry_source_id is required")
        if source_id in seen:
            raise ValidationError(f"Row {line_number}: duplicate registry_source_id {source_id}")
        seen.add(source_id)
        if row["source_status"] not in SOURCE_STATUSES:
            raise ValidationError(f"Row {line_number}: unsupported source_status")
        for field in (
            "identity_verified", "endpoint_verified", "monitoring_method_verified"
        ):
            if row[field] not in VERIFICATION_STATES:
                raise ValidationError(f"Row {line_number}: unsupported {field}")
        if row["terms_status"] not in TERMS_STATES:
            raise ValidationError(f"Row {line_number}: unsupported terms_status")
        if row["commercial_use_status"] not in COMMERCIAL_USE_STATES:
            raise ValidationError(f"Row {line_number}: unsupported commercial_use_status")
        if row["monitoring_status"] not in MONITORING_STATES:
            raise ValidationError(f"Row {line_number}: unsupported monitoring_status")
        if row["market"] != "TW":
            raise ValidationError(f"Row {line_number}: P02 registry market must be TW")
        if row["monitoring_status"] == "ACTIVE":
            required = ["verified_at", "verification_evidence_url", "expected_interval_minutes"]
            missing = [field for field in required if not row.get(field)]
            if missing:
                raise ValidationError(
                    f"Row {line_number}: ACTIVE missing {', '.join(missing)}"
                )
            if not _valid_http_url(row["verification_evidence_url"]):
                raise ValidationError(f"Row {line_number}: invalid verification_evidence_url")
            try:
                if int(row["expected_interval_minutes"]) <= 0:
                    raise ValueError
            except ValueError as error:
                raise ValidationError(
                    f"Row {line_number}: expected_interval_minutes must be positive"
                ) from error
            unverified = [
                field for field in (
                    "identity_verified", "endpoint_verified", "monitoring_method_verified"
                ) if row[field] != "VERIFIED"
            ]
            if unverified:
                raise ValidationError(
                    f"Row {line_number}: ACTIVE requires VERIFIED {', '.join(unverified)}"
                )
            if row["terms_status"] in {"MANUAL_ONLY", "BLOCKED"} or row[
                "commercial_use_status"
            ] in {"MANUAL_ONLY", "BLOCKED"}:
                raise ValidationError(
                    f"Row {line_number}: ACTIVE cannot have manual-only or blocked rights status"
                )
        for url_field in ("profile_url", "channel_url", "verification_evidence_url"):
            if row.get(url_field) and not _valid_http_url(row[url_field]):
                raise ValidationError(f"Row {line_number}: invalid {url_field}")
    return rows


def _ensure_core_source(connection: sqlite3.Connection, row: dict[str, str]) -> str | None:
    if row["monitoring_status"] != "ACTIVE":
        existing = connection.execute(
            "SELECT id FROM sources WHERE source_id = ?", (row["registry_source_id"],)
        ).fetchone()
        return existing["id"] if existing else None

    market = connection.execute("SELECT id FROM markets WHERE country_code = 'TW'").fetchone()
    if market is None:
        raise ValidationError("TW market must be initialized before radar registry import")
    source_url = row.get("profile_url") or row.get("channel_url") or row["verification_evidence_url"]
    core_id = str(uuid.uuid4())
    existing = connection.execute(
        "SELECT id FROM sources WHERE source_id = ?", (row["registry_source_id"],)
    ).fetchone()
    if existing:
        core_id = existing["id"]
    reliability = "A" if row["publisher_group"] == "twse" else "D"
    connection.execute(
        """
        INSERT INTO sources (
            id, source_id, source_url, publisher, publisher_group, market_id,
            source_type, signal_role, reliability_level, verified_at, evidence_url,
            registry_status, collection_status, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', 'RADAR_VERIFIED', ?)
        ON CONFLICT(source_id) DO UPDATE SET
            source_url = excluded.source_url,
            publisher = excluded.publisher,
            publisher_group = excluded.publisher_group,
            source_type = excluded.source_type,
            verified_at = excluded.verified_at,
            evidence_url = excluded.evidence_url,
            collection_status = excluded.collection_status,
            metadata_json = excluded.metadata_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            core_id,
            row["registry_source_id"],
            source_url,
            row["publisher"],
            row["publisher_group"],
            market["id"],
            row["source_type"],
            "OPINION" if row["platform"] in {"X", "YOUTUBE", "FORUM"} else "FACT",
            reliability,
            row["verified_at"],
            row["verification_evidence_url"],
            json.dumps(
                {
                    "adapter_role": "READ_ONLY_DISCOVERY",
                    "monitoring_method": row["monitoring_method"],
                    "automatic_publishing": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    return core_id


def import_realtime_registry(
    connection: sqlite3.Connection, rows: Iterable[dict[str, str]], *, now: datetime | None = None
) -> int:
    imported = 0
    current = now or utc_now()
    with connection:
        for row in rows:
            core_id = _ensure_core_source(connection, row)
            existing = connection.execute(
                "SELECT id FROM realtime_sources WHERE registry_source_id = ?",
                (row["registry_source_id"],),
            ).fetchone()
            realtime_id = existing["id"] if existing else str(uuid.uuid4())
            interval = int(row["expected_interval_minutes"]) if row.get("expected_interval_minutes") else None
            metadata = {
                "notes": row.get("notes") or "",
                "candidate_origin": row.get("candidate_origin") or "",
                "single_connectivity_verified": row.get("single_connectivity_verified") or "false",
                "continuous_sla_verified": row.get("continuous_sla_verified") or "false",
            }
            connection.execute(
                """
                INSERT INTO realtime_sources (
                    id, registry_source_id, core_source_id, platform, source_type,
                    account_handle, profile_url, channel_name, channel_id, channel_url,
                    publisher, publisher_group, market, language, category, verified_at,
                    verification_evidence_url, monitoring_method, source_status,
                    monitoring_status, expected_interval_minutes, metadata_json,
                    identity_verified, endpoint_verified, monitoring_method_verified,
                    terms_status, commercial_use_status, runtime_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(registry_source_id) DO UPDATE SET
                    core_source_id = excluded.core_source_id,
                    platform = excluded.platform,
                    source_type = excluded.source_type,
                    account_handle = excluded.account_handle,
                    profile_url = excluded.profile_url,
                    channel_name = excluded.channel_name,
                    channel_id = excluded.channel_id,
                    channel_url = excluded.channel_url,
                    publisher = excluded.publisher,
                    publisher_group = excluded.publisher_group,
                    market = excluded.market,
                    language = excluded.language,
                    category = excluded.category,
                    verified_at = excluded.verified_at,
                    verification_evidence_url = excluded.verification_evidence_url,
                    monitoring_method = excluded.monitoring_method,
                    source_status = excluded.source_status,
                    monitoring_status = excluded.monitoring_status,
                    expected_interval_minutes = excluded.expected_interval_minutes,
                    metadata_json = excluded.metadata_json,
                    identity_verified = excluded.identity_verified,
                    endpoint_verified = excluded.endpoint_verified,
                    monitoring_method_verified = excluded.monitoring_method_verified,
                    terms_status = excluded.terms_status,
                    commercial_use_status = excluded.commercial_use_status,
                    runtime_status = CASE
                        WHEN realtime_sources.last_success_at IS NOT NULL
                        THEN realtime_sources.runtime_status
                        ELSE excluded.runtime_status
                    END,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    realtime_id,
                    row["registry_source_id"],
                    core_id,
                    row["platform"],
                    row["source_type"],
                    row.get("account_handle") or None,
                    row.get("profile_url") or None,
                    row.get("channel_name") or None,
                    row.get("channel_id") or None,
                    row.get("channel_url") or None,
                    row["publisher"],
                    row["publisher_group"],
                    row["market"],
                    row["language"],
                    row["category"],
                    row.get("verified_at") or None,
                    row.get("verification_evidence_url") or None,
                    row["monitoring_method"],
                    row["source_status"],
                    row["monitoring_status"],
                    interval,
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                    row["identity_verified"],
                    row["endpoint_verified"],
                    row["monitoring_method_verified"],
                    row["terms_status"],
                    row["commercial_use_status"],
                    row.get("runtime_status") or "NOT_STARTED",
                ),
            )
            if row["monitoring_status"] == "ACTIVE":
                connection.execute(
                    """
                    INSERT OR IGNORE INTO radar_scheduler_state (
                        realtime_source_id, next_due_at
                    ) VALUES (?, ?)
                    """,
                    (realtime_id, iso(current)),
                )
            imported += 1
    return imported


def make_xhot_fetcher(xhot_root: str | Path) -> Callable[[str], list[dict[str, Any]]]:
    root = Path(xhot_root).resolve()
    source_dir = root / "src"
    if not (source_dir / "x_hottopic" / "timeline.py").exists():
        raise ValidationError(f"xHotTopic source tree not found: {root}")
    source_text = str(source_dir)
    if source_text not in sys.path:
        sys.path.insert(0, source_text)
    from x_hottopic.timeline import FxTwitterTimelineSource, TimelineRequest

    adapter = FxTwitterTimelineSource(timeout=30.0, requests_per_second=2.0)

    def fetch(handle: str) -> list[dict[str, Any]]:
        page = adapter.fetch_page(TimelineRequest(handle=handle, count=30, with_replies=False))
        if page.status_code != 200 or not page.parse_ok:
            raise RuntimeError(
                f"FxTwitter read-only adapter HTTP {page.status_code}; parse_ok={page.parse_ok}"
            )
        return list(page.results)

    return fetch


def fetch_youtube_atom(channel_id: str) -> list[dict[str, Any]]:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "global-x-finance-radar/0.1", "Accept": "application/atom+xml"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"YouTube Atom HTTP {response.status}")
        body = response.read()
    root = ET.fromstring(body)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }
    items: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        link = entry.find("atom:link", ns)
        items.append(
            {
                "id": entry.findtext("yt:videoId", default="", namespaces=ns),
                "title": entry.findtext("atom:title", default="", namespaces=ns),
                "url": link.get("href") if link is not None else "",
                "published_at": entry.findtext("atom:published", default="", namespaces=ns),
                "channel_id": entry.findtext("yt:channelId", default=channel_id, namespaces=ns),
            }
        )
    return items


def _normalize_x_item(item: dict[str, Any], handle: str) -> dict[str, Any]:
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    item_id = str(item.get("id") or item.get("tweet_id") or "").strip()
    text = str(item.get("text") or item.get("raw_text") or "").strip()
    url = str(item.get("url") or "").strip()
    if not url and item_id:
        url = f"https://x.com/{handle}/status/{item_id}"
    published = item.get("created_at") or item.get("createdAt") or item.get("published_at")
    parsed = parse_datetime(published)
    return {
        "external_id": item_id,
        "text": text,
        "title": text,
        "url": url,
        "published_at": iso(parsed) if parsed else None,
        "source_account": str(author.get("screen_name") or author.get("username") or handle),
        "payload": item,
    }


def _normalize_youtube_item(item: dict[str, Any], channel_name: str) -> dict[str, Any]:
    published = parse_datetime(item.get("published_at") or item.get("published"))
    title = str(item.get("title") or "").strip()
    return {
        "external_id": str(item.get("id") or item.get("video_id") or "").strip(),
        "text": title,
        "title": title,
        "url": str(item.get("url") or "").strip(),
        "published_at": iso(published) if published else None,
        "source_account": channel_name,
        "payload": item,
    }


@dataclass(frozen=True)
class SourceCycleResult:
    source_id: str
    status: str
    fetched_count: int
    new_count: int
    duplicate_count: int
    latency_seconds: float | None
    error: str | None


@dataclass(frozen=True)
class RadarCycleResult:
    cycle_id: str
    started_at: str
    finished_at: str
    sources: tuple[SourceCycleResult, ...]


class RealtimeRadar:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        x_fetcher: Callable[[str], list[dict[str, Any]]] | None = None,
        youtube_fetcher: Callable[[str], list[dict[str, Any]]] | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.connection = connection
        self.x_fetcher = x_fetcher
        self.youtube_fetcher = youtube_fetcher or fetch_youtube_atom
        self.clock = clock

    def _due_sources(self, force: bool) -> list[sqlite3.Row]:
        now_text = iso(self.clock())
        if force:
            return self.connection.execute(
                """
                SELECT * FROM realtime_sources
                WHERE monitoring_status = 'ACTIVE' AND platform IN ('X','YOUTUBE')
                ORDER BY platform, registry_source_id
                """
            ).fetchall()
        return self.connection.execute(
            """
            SELECT rs.* FROM realtime_sources rs
            JOIN radar_scheduler_state state ON state.realtime_source_id = rs.id
            WHERE rs.monitoring_status = 'ACTIVE'
              AND rs.platform IN ('X','YOUTUBE')
              AND state.next_due_at <= ?
            ORDER BY rs.platform, rs.registry_source_id
            """,
            (now_text,),
        ).fetchall()

    def run_cycle(self, *, force: bool = False) -> RadarCycleResult:
        started = self.clock()
        cycle_id = str(uuid.uuid4())
        if not self._acquire_runtime_lock(cycle_id, started):
            finished = self.clock()
            return RadarCycleResult(cycle_id, iso(started), iso(finished), ())
        try:
            results = [
                self._collect_source(row, cycle_id, schedule_anchor=started)
                for row in self._due_sources(force)
            ]
            finished = self.clock()
            return RadarCycleResult(cycle_id, iso(started), iso(finished), tuple(results))
        finally:
            self._release_runtime_lock(cycle_id)

    def _acquire_runtime_lock(self, owner_id: str, started: datetime) -> bool:
        locked_until = started + timedelta(minutes=8)
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            updated = self.connection.execute(
                """
                UPDATE radar_runtime_lock
                SET owner_id = ?, locked_until = ?, updated_at = CURRENT_TIMESTAMP
                WHERE lock_name = 'taiwan_realtime_radar' AND locked_until <= ?
                """,
                (owner_id, iso(locked_until), iso(started)),
            ).rowcount
            self.connection.commit()
            return updated == 1
        except Exception:
            self.connection.rollback()
            raise

    def _release_runtime_lock(self, owner_id: str) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE radar_runtime_lock
                SET owner_id = NULL, locked_until = '1970-01-01T00:00:00+00:00',
                    updated_at = CURRENT_TIMESTAMP
                WHERE lock_name = 'taiwan_realtime_radar' AND owner_id = ?
                """,
                (owner_id,),
            )

    def _collect_source(
        self,
        row: sqlite3.Row,
        cycle_id: str,
        *,
        schedule_anchor: datetime,
    ) -> SourceCycleResult:
        started = self.clock()
        started_mono = time.monotonic()
        run_id = str(uuid.uuid4())
        collection_run_id = str(uuid.uuid4())
        market = self.connection.execute("SELECT id FROM markets WHERE country_code = 'TW'").fetchone()
        if market is None or not row["core_source_id"]:
            raise ValidationError(f"Active radar source lacks core source: {row['registry_source_id']}")
        self.connection.execute(
            """
            INSERT INTO collection_runs (
                id, market_id, source_id, started_at, status, collector_version
            ) VALUES (?, ?, ?, ?, 'RUNNING', 'realtime-radar/0.1')
            """,
            (collection_run_id, market["id"], row["core_source_id"], iso(started)),
        )
        self.connection.commit()
        fetched_count = new_count = duplicate_count = 0
        latest_published: str | None = None
        is_initial_backfill = 1 if row["last_success_at"] is None else 0
        try:
            if row["platform"] == "X":
                if self.x_fetcher is None:
                    raise RuntimeError("xHotTopic adapter is not configured")
                raw_items = self.x_fetcher(row["account_handle"])
                items = [_normalize_x_item(item, row["account_handle"]) for item in raw_items]
            elif row["platform"] == "YOUTUBE":
                raw_items = self.youtube_fetcher(row["channel_id"])
                items = [_normalize_youtube_item(item, row["channel_name"]) for item in raw_items]
            else:
                raise RuntimeError(f"Unsupported active platform {row['platform']}")
            discovered = iso(self.clock())
            store = EvidenceStore(self.connection)
            for item in items:
                if not item["text"] or not _valid_http_url(item["url"]):
                    continue
                fetched_count += 1
                evidence = store.save_raw_item(
                    source_id=row["registry_source_id"],
                    original_url=item["url"],
                    original_content=item["text"],
                    published_at=item["published_at"],
                    fetched_at=discovered,
                    mime_type="application/json",
                    raw_payload=item["payload"],
                    data_label="RAW_EVIDENCE",
                    collection_run_id=collection_run_id,
                    commit=False,
                )
                if evidence.created:
                    new_count += 1
                    self.connection.execute(
                        """
                        INSERT INTO radar_items (
                            id, raw_item_id, realtime_source_id, external_item_id,
                            source_type, title_or_text, source_account, published_at,
                            discovered_at, detection_latency_minutes, fact_or_opinion,
                            evidence_url, duplicate_status, publisher_group, is_initial_backfill
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPINION', ?, 'EXACT_NEW', ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            evidence.id,
                            row["id"],
                            item["external_id"] or None,
                            row["source_type"],
                            item["title"],
                            item["source_account"],
                            item["published_at"],
                            discovered,
                            detection_latency_minutes(item["published_at"], discovered),
                            item["url"],
                            row["publisher_group"],
                            is_initial_backfill,
                        ),
                    )
                else:
                    duplicate_count += 1
                if item["published_at"] and (
                    latest_published is None or item["published_at"] > latest_published
                ):
                    latest_published = item["published_at"]
            finished = self.clock()
            latency = round(time.monotonic() - started_mono, 3)
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE collection_runs SET finished_at = ?, status = 'SUCCESS', item_count = ?
                    WHERE id = ?
                    """,
                    (iso(finished), fetched_count, collection_run_id),
                )
                self.connection.execute(
                    """
                    UPDATE realtime_sources SET
                        runtime_status = 'CONTINUOUS_CYCLE_SUCCESS',
                        last_success_at = ?, last_failure_reason = NULL,
                        consecutive_failures = 0,
                        latest_content_published_at = COALESCE(?, latest_content_published_at),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (iso(finished), latest_published, row["id"]),
                )
                self._advance_schedule(row, cycle_id, schedule_anchor)
                self.connection.execute(
                    """
                    INSERT INTO radar_runs (
                        id, cycle_id, realtime_source_id, collection_run_id, started_at,
                        finished_at, status, fetched_count, new_count, duplicate_count,
                        request_latency_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, 'SUCCESS', ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        cycle_id,
                        row["id"],
                        collection_run_id,
                        iso(started),
                        iso(finished),
                        fetched_count,
                        new_count,
                        duplicate_count,
                        latency,
                    ),
                )
            return SourceCycleResult(
                row["registry_source_id"], "SUCCESS", fetched_count, new_count,
                duplicate_count, latency, None
            )
        except Exception as error:
            finished = self.clock()
            latency = round(time.monotonic() - started_mono, 3)
            message = f"{type(error).__name__}: {error}"[:1000]
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE collection_runs SET finished_at = ?, status = 'FAILED',
                        error_code = ?, error_message = ? WHERE id = ?
                    """,
                    (iso(finished), type(error).__name__, message, collection_run_id),
                )
                self.connection.execute(
                    """
                    UPDATE realtime_sources SET runtime_status = 'CONTINUOUS_CYCLE_FAILED',
                        last_failure_at = ?, last_failure_reason = ?,
                        consecutive_failures = consecutive_failures + 1,
                        updated_at = CURRENT_TIMESTAMP WHERE id = ?
                    """,
                    (iso(finished), message, row["id"]),
                )
                self._advance_schedule(row, cycle_id, schedule_anchor)
                self.connection.execute(
                    """
                    INSERT INTO radar_runs (
                        id, cycle_id, realtime_source_id, collection_run_id, started_at,
                        finished_at, status, fetched_count, new_count, duplicate_count,
                        request_latency_seconds, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, 'FAILED', 0, 0, 0, ?, ?)
                    """,
                    (
                        run_id, cycle_id, row["id"], collection_run_id,
                        iso(started), iso(finished), latency, message,
                    ),
                )
            return SourceCycleResult(
                row["registry_source_id"], "FAILED", 0, 0, 0, latency, message
            )

    def _advance_schedule(
        self, row: sqlite3.Row, cycle_id: str, schedule_anchor: datetime
    ) -> None:
        # Anchor every source in one dispatcher cycle to the same whole minute.
        # Otherwise sequential HTTP calls that cross a minute boundary split one
        # source group across later Windows triggers.
        next_due = schedule_anchor.replace(second=0, microsecond=0) + timedelta(
            minutes=int(row["expected_interval_minutes"])
        )
        self.connection.execute(
            """
            INSERT INTO radar_scheduler_state (realtime_source_id, next_due_at, last_cycle_id)
            VALUES (?, ?, ?)
            ON CONFLICT(realtime_source_id) DO UPDATE SET
                next_due_at = excluded.next_due_at,
                last_cycle_id = excluded.last_cycle_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (row["id"], iso(next_due), cycle_id),
        )


def radar_summary(connection: sqlite3.Connection) -> dict[str, Any]:
    totals = connection.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN monitoring_status = 'ACTIVE' THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN monitoring_status = 'NEEDS_VERIFICATION' THEN 1 ELSE 0 END) AS needs,
               COUNT(DISTINCT CASE WHEN monitoring_status = 'ACTIVE' THEN publisher_group END)
                   AS independent_active_groups
        FROM realtime_sources
        """
    ).fetchone()
    average_latency = connection.execute(
        """
        SELECT AVG(detection_latency_minutes) FROM radar_items
        WHERE detection_latency_minutes IS NOT NULL AND is_initial_backfill = 0
        """
    ).fetchone()[0]
    return {
        **dict(totals),
        "average_detection_latency_minutes": (
            round(float(average_latency), 2) if average_latency is not None else None
        ),
    }
