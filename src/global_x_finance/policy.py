from __future__ import annotations

import hashlib
import json
import sqlite3
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from .errors import ValidationError


@dataclass(frozen=True)
class PolicyHttpResponse:
    status: int
    body: bytes
    content_type: str
    final_url: str


@dataclass(frozen=True)
class PolicyImportResult:
    snapshot_new_count: int
    snapshot_existing_count: int
    rule_new_count: int
    rule_existing_count: int
    checklist_new_count: int
    total_snapshot_count: int
    total_rule_count: int


PolicyTransport = Callable[[str, float], PolicyHttpResponse]


CHECKLIST_FIELDS = {
    "advertiser_legal_name": "UNKNOWN",
    "advertiser_country": "UNKNOWN",
    "target_country": "UNKNOWN",
    "product_name": "UNKNOWN",
    "product_category": "UNKNOWN",
    "landing_page": "UNKNOWN",
    "fees_disclosed": "UNKNOWN",
    "risk_disclosure": "UNKNOWN",
    "financial_license_status": "UNKNOWN",
    "license_authority": "UNKNOWN",
    "license_number": "UNKNOWN",
    "X_pre_authorization_status": "UNKNOWN",
    "X_ads_account_eligible": "UNKNOWN",
    "X_account_verified": "UNKNOWN",
    "bio_url_valid": "UNKNOWN",
    "landing_page_accessible": "UNKNOWN",
    "landing_page_matches_ad": "UNKNOWN",
    "prohibited_claims_detected": "UNKNOWN",
    "policy_snapshot_date": "UNKNOWN",
}


def load_policy_registry(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed_hosts = set(config.get("allowed_hosts", []))
    pages = config.get("pages", [])
    if not allowed_hosts or not pages:
        raise ValidationError("X policy page registry is empty")
    seen_keys: set[str] = set()
    seen_urls: set[str] = set()
    for page in pages:
        missing = {
            "policy_key",
            "policy_name",
            "jurisdiction",
            "product_category",
            "source_url",
            "page_updated_at",
            "normalized_summary",
        } - set(page)
        if missing:
            raise ValidationError(f"Policy page is missing fields: {sorted(missing)}")
        parsed = urlparse(page["source_url"])
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            raise ValidationError(f"Non-official X policy URL is not allowed: {page['source_url']}")
        if page["policy_key"] in seen_keys or page["source_url"] in seen_urls:
            raise ValidationError("Duplicate X policy key or URL")
        seen_keys.add(page["policy_key"])
        seen_urls.add(page["source_url"])
    return config


def load_policy_rules(path: str | Path, page_keys: set[str]) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    rules = config.get("rules", [])
    if not rules:
        raise ValidationError("X structured policy rules are empty")
    rule_ids: set[str] = set()
    required = {
        "rule_id",
        "policy_key",
        "country",
        "product_category",
        "rule_type",
        "requirement",
        "result_if_violated",
    }
    for rule in rules:
        missing = required - set(rule)
        if missing:
            raise ValidationError(f"Policy rule is missing fields: {sorted(missing)}")
        if rule["rule_id"] in rule_ids:
            raise ValidationError(f"Duplicate policy rule_id: {rule['rule_id']}")
        if rule["policy_key"] not in page_keys:
            raise ValidationError(f"Unknown policy_key in rule: {rule['policy_key']}")
        rule_ids.add(rule["rule_id"])
    return config


def _default_transport(url: str, timeout: float) -> PolicyHttpResponse:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
            "User-Agent": "Global-X-Finance-Policy-Snapshot/0.1",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return PolicyHttpResponse(
            status=response.status,
            body=response.read(2_000_001),
            content_type=response.headers.get("Content-Type", ""),
            final_url=response.geturl(),
        )


class XAdsPolicySnapshotService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        page_registry: dict,
        rule_registry: dict,
        *,
        transport: PolicyTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.connection = connection
        self.page_registry = page_registry
        self.rule_registry = rule_registry
        self.transport = transport or _default_transport
        self.timeout = timeout
        self.allowed_hosts = set(page_registry["allowed_hosts"])

    def snapshot_all(self) -> PolicyImportResult:
        snapshot_new = 0
        snapshot_existing = 0
        page_snapshots: dict[str, sqlite3.Row] = {}
        for page in self.page_registry["pages"]:
            snapshot, created = self._snapshot_page(page)
            page_snapshots[page["policy_key"]] = snapshot
            if created:
                snapshot_new += 1
            else:
                snapshot_existing += 1

        rule_new, rule_existing = self._store_rules(page_snapshots)
        checklist_new = self._store_checklists(page_snapshots)
        total_snapshots = self.connection.execute(
            "SELECT COUNT(*) FROM policy_snapshots"
        ).fetchone()[0]
        total_rules = self.connection.execute("SELECT COUNT(*) FROM policy_rules").fetchone()[0]
        return PolicyImportResult(
            snapshot_new_count=snapshot_new,
            snapshot_existing_count=snapshot_existing,
            rule_new_count=rule_new,
            rule_existing_count=rule_existing,
            checklist_new_count=checklist_new,
            total_snapshot_count=total_snapshots,
            total_rule_count=total_rules,
        )

    def _snapshot_page(self, page: dict) -> tuple[sqlite3.Row, bool]:
        response = self.transport(page["source_url"], self.timeout)
        final_host = urlparse(response.final_url).hostname
        if response.status != 200:
            raise ValidationError(
                f"X policy fetch failed ({response.status}): {page['source_url']}"
            )
        if final_host not in self.allowed_hosts:
            raise ValidationError(f"X policy redirected outside official hosts: {response.final_url}")
        if len(response.body) > 2_000_000:
            raise ValidationError(f"X policy response exceeds 2 MB: {page['source_url']}")
        if "text/html" not in response.content_type.lower():
            raise ValidationError(f"Unexpected X policy content type: {response.content_type}")
        raw_text = response.body.decode("utf-8", errors="replace")
        if page["policy_name"].split()[0].lower() not in raw_text.lower():
            raise ValidationError(f"X policy response lacks expected page marker: {page['policy_name']}")
        content_hash = hashlib.sha256(response.body).hexdigest()
        existing = self.connection.execute(
            "SELECT * FROM policy_snapshots WHERE policy_url = ? AND content_hash = ?",
            (page["source_url"], content_hash),
        ).fetchone()
        if existing is not None:
            return existing, False

        previous = self.connection.execute(
            """
            SELECT * FROM policy_snapshots
            WHERE COALESCE(source_url, policy_url) = ?
            ORDER BY fetched_at DESC, created_at DESC LIMIT 1
            """,
            (page["source_url"],),
        ).fetchone()
        previous_version = 0
        if previous is not None:
            try:
                previous_version = int(str(previous["snapshot_version"]).removeprefix("v"))
            except (TypeError, ValueError):
                previous_version = 0
        snapshot_id = str(uuid.uuid4())
        fetched_at = datetime.now(timezone.utc).isoformat()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO policy_snapshots (
                    id, market_id, policy_name, policy_url, fetched_at,
                    content_hash, content_text, status, jurisdiction,
                    product_category, source_url, page_updated_at,
                    normalized_summary, snapshot_version,
                    supersedes_snapshot_id, verification_status
                ) VALUES (?, NULL, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    page["policy_name"],
                    page["source_url"],
                    fetched_at,
                    content_hash,
                    raw_text,
                    page["jurisdiction"],
                    page["product_category"],
                    page["source_url"],
                    page["page_updated_at"],
                    page["normalized_summary"],
                    f"v{previous_version + 1}",
                    previous["id"] if previous is not None else None,
                    "VERIFIED_OFFICIAL_HTTP_200",
                ),
            )
        return self.connection.execute(
            "SELECT * FROM policy_snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone(), True

    def _store_rules(self, page_snapshots: dict[str, sqlite3.Row]) -> tuple[int, int]:
        created = 0
        existing = 0
        for rule in self.rule_registry["rules"]:
            snapshot = page_snapshots[rule["policy_key"]]
            found = self.connection.execute(
                "SELECT id FROM policy_rules WHERE rule_id = ? AND snapshot_id = ?",
                (rule["rule_id"], snapshot["id"]),
            ).fetchone()
            if found is not None:
                existing += 1
                continue
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO policy_rules (
                        id, rule_id, policy_name, country, product_category,
                        rule_type, requirement, result_if_violated,
                        evidence_url, snapshot_id, verified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        rule["rule_id"],
                        snapshot["policy_name"],
                        rule["country"],
                        rule["product_category"],
                        rule["rule_type"],
                        rule["requirement"],
                        rule["result_if_violated"],
                        snapshot["source_url"],
                        snapshot["id"],
                        snapshot["fetched_at"],
                    ),
                )
            created += 1
        return created, existing

    def _store_checklists(self, page_snapshots: dict[str, sqlite3.Row]) -> int:
        snapshot_date = max(row["fetched_at"] for row in page_snapshots.values())[:10]
        created = 0
        names = {
            ("TW", "FINANCIAL_SERVICES"): "Taiwan Financial Ads Checklist",
            ("TW", "CRYPTO"): "Taiwan Crypto Ads Checklist",
            ("US", "FINANCIAL_SERVICES"): "US Financial Ads Checklist",
            ("US", "CRYPTO"): "US Crypto Ads Checklist",
        }
        for (country, category), name in names.items():
            checklist_id = f"XADS-{country}-{category}-V0.1"
            found = self.connection.execute(
                """
                SELECT id FROM policy_checklist_templates
                WHERE checklist_id = ? AND policy_snapshot_date = ?
                """,
                (checklist_id, snapshot_date),
            ).fetchone()
            if found is not None:
                continue
            fields = dict(CHECKLIST_FIELDS)
            fields["target_country"] = country
            fields["product_category"] = category
            fields["policy_snapshot_date"] = snapshot_date
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE policy_checklist_templates SET status = 'SUPERSEDED'
                    WHERE country = ? AND product_category = ? AND status = 'ACTIVE'
                    """,
                    (country, category),
                )
                self.connection.execute(
                    """
                    INSERT INTO policy_checklist_templates (
                        id, checklist_id, checklist_name, country,
                        product_category, fields_json, policy_snapshot_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                    """,
                    (
                        str(uuid.uuid4()),
                        checklist_id,
                        name,
                        country,
                        category,
                        json.dumps(fields, ensure_ascii=False, sort_keys=True),
                        snapshot_date,
                    ),
                )
            created += 1
        return created
