from __future__ import annotations

import sqlite3
import uuid

import pytest

from global_x_finance.evidence import EvidenceStore
from global_x_finance.rules import (
    add_evidence_link,
    compliance_precheck_result,
    default_claim_type,
    independent_source_count,
)


def _claim(database, text: str = "SYNTHETIC_TEST_DATA claim") -> str:
    claim_id = str(uuid.uuid4())
    database.execute(
        """
        INSERT INTO claims (id, claim_text, claim_type, status, extractor_version)
        VALUES (?, ?, 'FACT_CLAIM', 'UNVERIFIED', 'SYNTHETIC_TEST_DATA')
        """,
        (claim_id, text),
    )
    database.commit()
    return claim_id


def _raw(database, source_id: str, slug: str):
    return EvidenceStore(database).save_raw_item(
        source_id=source_id,
        original_url=f"https://synthetic.invalid/{slug}",
        original_content=f"SYNTHETIC_TEST_DATA evidence {slug}",
        published_at=None,
        data_label="SYNTHETIC_TEST_DATA",
    )


def test_same_publisher_group_counts_as_one_independent_source(database):
    claim_id = _claim(database)
    twse_site = _raw(database, "TW-A01", "publisher-one")
    twse_api = _raw(database, "TW-A02", "publisher-two")
    add_evidence_link(database, claim_id=claim_id, raw_item_id=twse_site.id, relation="SUPPORTS")
    add_evidence_link(database, claim_id=claim_id, raw_item_id=twse_api.id, relation="SUPPORTS")

    assert independent_source_count(database, claim_id) == 1


def test_kol_defaults_to_opinion():
    assert default_claim_type("KOL") == "OPINION"
    assert default_claim_type("SOCIAL_MEDIA") == "OPINION"
    assert default_claim_type("OFFICIAL_API") == "FACT_CLAIM"


def test_support_and_contradiction_set_source_conflict(database):
    claim_id = _claim(database, "SYNTHETIC_TEST_DATA conflicting claim")
    support = _raw(database, "TW-A01", "conflict-support")
    contradict = _raw(database, "TW-A06", "conflict-contradict")
    add_evidence_link(database, claim_id=claim_id, raw_item_id=support.id, relation="SUPPORTS")
    add_evidence_link(database, claim_id=claim_id, raw_item_id=contradict.id, relation="CONTRADICTS")

    status = database.execute("SELECT status FROM claims WHERE id = ?", (claim_id,)).fetchone()[0]
    assert status == "SOURCE_CONFLICT"


def test_commercial_fit_can_only_be_predicted(database):
    market_id = database.execute("SELECT id FROM markets WHERE country_code = 'TW'").fetchone()[0]
    topic_id = str(uuid.uuid4())
    database.execute(
        """
        INSERT INTO topics (
            id, market_id, topic_key, title, status, first_seen_at, last_seen_at, clustering_version
        ) VALUES (?, ?, 'SYNTHETIC_TEST_DATA-topic', 'SYNTHETIC_TEST_DATA', 'UNKNOWN',
                  '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', 'SYNTHETIC_TEST_DATA')
        """,
        (topic_id, market_id),
    )
    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO trend_snapshots (
                id, topic_id, measured_at, commercial_fit_type, scoring_version
            ) VALUES (?, ?, '2026-01-01T00:00:00Z', 'ACTUAL_CONVERSION', 'SYNTHETIC_TEST_DATA')
            """,
            (str(uuid.uuid4()), topic_id),
        )


def test_promoted_without_license_cannot_pass_precheck(database):
    assert compliance_precheck_result(
        requested_result="PASS_PRECHECK",
        is_promoted=True,
        product_info_status="PROVIDED",
        advertiser_license_status="UNKNOWN",
    ) == "REVIEW_REQUIRED"

    market_id = database.execute("SELECT id FROM markets WHERE country_code = 'TW'").fetchone()[0]
    topic_id = str(uuid.uuid4())
    draft_id = str(uuid.uuid4())
    database.execute(
        """
        INSERT INTO topics (
            id, market_id, topic_key, title, status, first_seen_at, last_seen_at, clustering_version
        ) VALUES (?, ?, 'SYNTHETIC_TEST_DATA-compliance', 'SYNTHETIC_TEST_DATA', 'UNKNOWN',
                  '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', 'SYNTHETIC_TEST_DATA')
        """,
        (topic_id, market_id),
    )
    database.execute(
        """
        INSERT INTO content_drafts (
            id, market_id, topic_id, draft_type, body, commercial_fit_type,
            status, generation_version
        ) VALUES (?, ?, ?, 'PROMOTED', 'SYNTHETIC_TEST_DATA', 'PREDICTED',
                  'SYNTHETIC_TEST_DATA', 'SYNTHETIC_TEST_DATA')
        """,
        (draft_id, market_id, topic_id),
    )
    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO compliance_checks (
                id, content_draft_id, result, risk_level, findings_json,
                product_info_status, advertiser_license_status, checked_at
            ) VALUES (?, ?, 'PASS_PRECHECK', 'UNKNOWN', '{}', 'PROVIDED', 'UNKNOWN',
                      '2026-01-01T00:00:00Z')
            """,
            (str(uuid.uuid4()), draft_id),
        )

