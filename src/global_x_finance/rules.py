from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

from .errors import ValidationError


OPINION_SOURCE_TYPES = {"KOL", "FORUM", "SOCIAL", "SOCIAL_MEDIA", "COMMUNITY"}
RELIABLE_LEVELS = {"A", "B"}


def default_claim_type(source_type: str) -> str:
    """KOL/social material is opinion unless a human explicitly verifies otherwise."""
    return "OPINION" if source_type.upper() in OPINION_SOURCE_TYPES else "FACT_CLAIM"


def add_evidence_link(
    connection: sqlite3.Connection,
    *,
    claim_id: str,
    raw_item_id: str,
    relation: str,
    excerpt: str | None = None,
    observed_at: str | None = None,
) -> str:
    if relation not in {"SUPPORTS", "CONTRADICTS", "CONTEXT"}:
        raise ValidationError(f"Unsupported evidence relation: {relation}")
    raw_item = connection.execute(
        "SELECT original_url FROM raw_items WHERE id = ?", (raw_item_id,)
    ).fetchone()
    if raw_item is None:
        raise ValidationError(f"Unknown raw_item_id: {raw_item_id}")
    if not raw_item["original_url"]:
        raise ValidationError("Evidence link requires a source URL")

    link_id = str(uuid.uuid4())
    with connection:
        connection.execute(
            """
            INSERT INTO evidence_links (
                id, claim_id, raw_item_id, relation, excerpt, source_url, observed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link_id, claim_id, raw_item_id, relation, excerpt,
                raw_item["original_url"],
                observed_at or datetime.now(timezone.utc).isoformat(),
            ),
        )
    refresh_claim_status(connection, claim_id)
    return link_id


def refresh_claim_status(connection: sqlite3.Connection, claim_id: str) -> str:
    claim = connection.execute("SELECT id FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if claim is None:
        raise ValidationError(f"Unknown claim_id: {claim_id}")
    relations = {
        row["relation"]
        for row in connection.execute(
            """
            SELECT el.relation
            FROM evidence_links el
            JOIN raw_items ri ON ri.id = el.raw_item_id
            JOIN sources s ON s.id = ri.source_id
            WHERE el.claim_id = ? AND s.reliability_level IN ('A', 'B')
            """,
            (claim_id,),
        )
    }
    supports = "SUPPORTS" in relations
    contradicts = "CONTRADICTS" in relations
    if supports and contradicts:
        status = "SOURCE_CONFLICT"
    elif supports:
        status = "SUPPORTED"
    elif contradicts:
        status = "REFUTED"
    else:
        status = "UNVERIFIED"
    with connection:
        connection.execute(
            "UPDATE claims SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, claim_id),
        )
    return status


def independent_source_count(connection: sqlite3.Connection, claim_id: str) -> int:
    row = connection.execute(
        """
        SELECT COUNT(DISTINCT s.publisher_group) AS count
        FROM evidence_links el
        JOIN raw_items ri ON ri.id = el.raw_item_id
        JOIN sources s ON s.id = ri.source_id
        WHERE el.claim_id = ? AND el.relation IN ('SUPPORTS', 'CONTRADICTS')
        """,
        (claim_id,),
    ).fetchone()
    return int(row["count"])


def compliance_precheck_result(
    *,
    requested_result: str,
    is_promoted: bool,
    product_info_status: str,
    advertiser_license_status: str,
) -> str:
    allowed = {"PASS_PRECHECK", "REVIEW_REQUIRED", "BLOCKED", "UNKNOWN"}
    if requested_result not in allowed:
        raise ValidationError(f"Unsupported compliance result: {requested_result}")
    if (
        is_promoted
        and requested_result == "PASS_PRECHECK"
        and (
            product_info_status != "PROVIDED"
            or advertiser_license_status != "PROVIDED"
        )
    ):
        return "REVIEW_REQUIRED"
    return requested_result

