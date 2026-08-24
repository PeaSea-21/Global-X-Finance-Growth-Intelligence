from __future__ import annotations

import json
import sqlite3
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable

from .errors import ValidationError
from .evidence import EvidenceStore, content_sha256
from .industry_mapping import (
    MAPPED_COMMON_STOCK,
    OFFICIAL_INDUSTRY_CLASSIFICATIONS,
    TPEX_COMPANY_ENDPOINT,
    TWSE_COMPANY_ENDPOINT,
    UNKNOWN,
    classify_security_industry,
)


COLLECTOR_VERSION = "industry-mapping-sync-v0.1"


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    content_type: str


@dataclass(frozen=True)
class IndustryEndpointResult:
    exchange_code: str
    source_id: str
    endpoint: str
    status: str
    fetched_count: int
    mapped_count: int
    skipped_count: int
    new_evidence_count: int
    duplicate_evidence_count: int
    error_reason: str | None = None


@dataclass(frozen=True)
class IndustrySyncResult:
    status: str
    endpoints: tuple[IndustryEndpointResult, ...]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "endpoints": [asdict(row) for row in self.endpoints],
        }


def _default_transport(url: str, timeout: float) -> HttpResponse:
    request = urllib.request.Request(url, headers={"User-Agent": "GlobalXFinance/0.5"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return HttpResponse(
            int(response.status),
            response.read(),
            response.headers.get("Content-Type", "application/json"),
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _published_at(record: dict) -> str | None:
    raw = str(record.get("出表日期") or record.get("Date") or "").strip()
    if len(raw) != 7 or not raw.isdigit():
        return None
    year = int(raw[:3]) + 1911
    try:
        return datetime(year, int(raw[3:5]), int(raw[5:7]), tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


class IndustryMappingSyncService:
    """Persist official industry codes as Evidence-backed candidate-recall metadata."""

    ENDPOINTS = (
        ("TWSE", "TW-A02", TWSE_COMPANY_ENDPOINT),
        ("TPEX", "TW-A04", TPEX_COMPANY_ENDPOINT),
    )

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        transport: Callable[[str, float], HttpResponse] | None = None,
        timeout: float = 60,
        test_mode: bool = False,
    ):
        self.connection = connection
        self.transport = transport or _default_transport
        self.timeout = timeout
        self.data_label = "SYNTHETIC_TEST_DATA" if test_mode else "REAL_OFFICIAL_SOURCE"

    def sync(self) -> IndustrySyncResult:
        self._require_tables()
        results = tuple(
            self._sync_endpoint(exchange, source_id, endpoint)
            for exchange, source_id, endpoint in self.ENDPOINTS
        )
        status = "SUCCESS" if all(row.status == "SUCCESS" for row in results) else "PARTIAL_FAILED"
        return IndustrySyncResult(status, results)

    def _require_tables(self) -> None:
        tables = {
            row[0]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required = {"industry_classifications", "security_industry_mappings"}
        missing = sorted(required - tables)
        if missing:
            raise ValidationError(f"Industry Mapping migration is not applied: {', '.join(missing)}")

    def _source(self, source_id: str) -> sqlite3.Row:
        row = self.connection.execute(
            "SELECT * FROM sources WHERE source_id=?", (source_id,)
        ).fetchone()
        if row is None:
            raise ValidationError(f"Unknown source_id: {source_id}")
        if row["collection_status"] != "API_VERIFIED":
            raise ValidationError(
                f"Automatic collection denied for {source_id}: "
                f"collection_status={row['collection_status']}"
            )
        return row

    def _sync_endpoint(
        self, exchange: str, registry_source_id: str, endpoint: str
    ) -> IndustryEndpointResult:
        source = self._source(registry_source_id)
        run_id = str(uuid.uuid4())
        started_at = _utc_now()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO collection_runs (
                    id, market_id, source_id, started_at, status, collector_version,
                    endpoint, dataset_name
                ) VALUES (?, ?, ?, ?, 'RUNNING', ?, ?, ?)
                """,
                (
                    run_id,
                    source["market_id"],
                    source["id"],
                    started_at,
                    COLLECTOR_VERSION,
                    endpoint,
                    f"official_industry_mapping_{exchange.lower()}",
                ),
            )
        try:
            response = self.transport(endpoint, self.timeout)
            if response.status != 200:
                raise ValidationError(f"{exchange} industry endpoint returned HTTP {response.status}")
            document = json.loads(response.body.decode("utf-8-sig"))
            if not isinstance(document, list):
                raise ValidationError(f"{exchange} industry endpoint must return a list")
            fetched_at = _utc_now()
            evidence = EvidenceStore(self.connection)
            mapped = skipped = raw_new = duplicates = 0
            self.connection.execute("BEGIN")
            self._upsert_classifications(source, exchange)
            for record in document:
                if not isinstance(record, dict):
                    skipped += 1
                    continue
                mapping = classify_security_industry(exchange, record)
                if mapping.ticker == UNKNOWN:
                    skipped += 1
                    continue
                content = json.dumps(
                    record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                digest = content_sha256(content)
                raw = evidence.save_raw_item(
                    source_id=registry_source_id,
                    original_url=f"{endpoint}#record-sha256={digest}",
                    canonical_url=endpoint,
                    original_content=content,
                    published_at=_published_at(record),
                    fetched_at=fetched_at,
                    mime_type=response.content_type.split(";", 1)[0],
                    raw_payload=record,
                    data_label=self.data_label,
                    collection_run_id=run_id,
                    commit=False,
                )
                raw_new += int(raw.created)
                duplicates += int(not raw.created)
                security_id = f"{exchange}:{mapping.ticker}"
                security = self.connection.execute(
                    "SELECT id FROM official_securities WHERE id=?", (security_id,)
                ).fetchone()
                if security is None:
                    skipped += 1
                    continue
                classification_id = None
                if mapping.mapping_status == MAPPED_COMMON_STOCK:
                    classification_id = f"industry:{exchange}:{mapping.official_industry_code}"
                self.connection.execute(
                    """
                    INSERT INTO security_industry_mappings (
                        id, security_id, industry_classification_id, exchange_code,
                        ticker, company_name, official_industry_code,
                        official_industry_name, normalized_sector, mapping_status,
                        source_id, raw_item_id, source_endpoint, source_field_code,
                        source_field_name, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(security_id) DO UPDATE SET
                        industry_classification_id=excluded.industry_classification_id,
                        company_name=excluded.company_name,
                        official_industry_code=excluded.official_industry_code,
                        official_industry_name=excluded.official_industry_name,
                        normalized_sector=excluded.normalized_sector,
                        mapping_status=excluded.mapping_status,
                        source_id=excluded.source_id,
                        raw_item_id=excluded.raw_item_id,
                        source_endpoint=excluded.source_endpoint,
                        source_field_code=excluded.source_field_code,
                        source_field_name=excluded.source_field_name,
                        collected_at=excluded.collected_at,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        f"security-industry:{security_id}",
                        security_id,
                        classification_id,
                        exchange,
                        mapping.ticker,
                        mapping.company_name,
                        mapping.official_industry_code,
                        mapping.official_industry_name,
                        mapping.normalized_sector,
                        mapping.mapping_status,
                        source["id"],
                        raw.id,
                        mapping.source_endpoint,
                        mapping.source_field_code,
                        mapping.source_field_name,
                        fetched_at,
                    ),
                )
                mapped += 1
            finished_at = _utc_now()
            self.connection.execute(
                """
                UPDATE collection_runs SET finished_at=?, status='SUCCESS',
                    item_count=?, new_item_count=?, duplicate_item_count=?
                WHERE id=?
                """,
                (finished_at, len(document), raw_new, duplicates, run_id),
            )
            self.connection.commit()
            return IndustryEndpointResult(
                exchange, registry_source_id, endpoint, "SUCCESS", len(document),
                mapped, skipped, raw_new, duplicates,
            )
        except Exception as error:
            self.connection.rollback()
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE collection_runs SET finished_at=?, status='FAILED',
                        error_code=?, error_message=? WHERE id=?
                    """,
                    (_utc_now(), type(error).__name__, str(error), run_id),
                )
            return IndustryEndpointResult(
                exchange, registry_source_id, endpoint, "FAILED", 0, 0, 0, 0, 0,
                f"{type(error).__name__}: {error}",
            )

    def _upsert_classifications(self, source: sqlite3.Row, exchange: str) -> None:
        for row in OFFICIAL_INDUSTRY_CLASSIFICATIONS:
            if row.exchange_code != exchange:
                continue
            self.connection.execute(
                """
                INSERT INTO industry_classifications (
                    id, market_id, exchange_code, scheme, official_industry_code,
                    official_industry_name, normalized_sector, mapping_status,
                    source_authority, source_endpoint, source_field_code,
                    source_field_name, notes
                ) VALUES (?, ?, ?, 'OFFICIAL_INDUSTRY_CODE', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(exchange_code, scheme, official_industry_code) DO UPDATE SET
                    official_industry_name=excluded.official_industry_name,
                    normalized_sector=excluded.normalized_sector,
                    mapping_status=excluded.mapping_status,
                    source_authority=excluded.source_authority,
                    source_endpoint=excluded.source_endpoint,
                    source_field_code=excluded.source_field_code,
                    source_field_name=excluded.source_field_name,
                    notes=excluded.notes,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    f"industry:{exchange}:{row.official_industry_code}",
                    source["market_id"],
                    exchange,
                    row.official_industry_code,
                    row.official_industry_name,
                    row.normalized_sector,
                    row.mapping_status,
                    row.source_authority,
                    row.source_endpoint,
                    row.source_field_code,
                    row.source_field_name,
                    row.notes,
                ),
            )
