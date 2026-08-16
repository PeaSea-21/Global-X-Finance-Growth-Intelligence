from __future__ import annotations

import hashlib
import json
from datetime import date

import pytest

from global_x_finance.compliance import run_financial_ads_precheck
from global_x_finance.errors import ValidationError
from global_x_finance.policy import (
    PolicyHttpResponse,
    XAdsPolicySnapshotService,
    load_policy_registry,
    load_policy_rules,
)
from global_x_finance.webapp import create_app


def _registries(root):
    pages = load_policy_registry(root / "config" / "x_ads_policy.pages.json")
    rules = load_policy_rules(
        root / "config" / "x_ads_policy.rules.json",
        {page["policy_key"] for page in pages["pages"]},
    )
    return pages, rules


def _transport_factory(pages, revisions=None):
    revisions = revisions or {}
    names = {page["source_url"]: page["policy_name"] for page in pages["pages"]}

    def transport(url: str, timeout: float) -> PolicyHttpResponse:
        del timeout
        marker = names[url]
        revision = revisions.get(url, "v1")
        body = (
            f"<html><body>{marker} SYNTHETIC_TEST_DATA {revision}</body></html>"
        ).encode("utf-8")
        return PolicyHttpResponse(200, body, "text/html; charset=utf-8", url)

    return transport


def _snapshot_all(database, root, revisions=None):
    pages, rules = _registries(root)
    service = XAdsPolicySnapshotService(
        database,
        pages,
        rules,
        transport=_transport_factory(pages, revisions),
    )
    return service.snapshot_all(), pages, rules


def _complete_facts(**updates):
    facts = {
        "advertiser_legal_name": "SYNTHETIC_TEST_DATA LTD.",
        "advertiser_country": "TW",
        "target_country": "TW",
        "product_name": "SYNTHETIC_TEST_DATA PRODUCT",
        "product_category": "FINANCIAL_SERVICES",
        "landing_page": "https://example.invalid/synthetic-test-data",
        "fees_disclosed": True,
        "risk_disclosure": True,
        "financial_license_status": "PROVIDED",
        "license_authority": "SYNTHETIC_TEST_DATA AUTHORITY",
        "license_number": "SYNTHETIC_TEST_DATA LICENSE",
        "X_pre_authorization_status": "APPROVED",
        "X_ads_account_eligible": True,
        "X_account_verified": True,
        "bio_url_valid": True,
        "landing_page_accessible": True,
        "landing_page_matches_ad": True,
        "prohibited_claims_detected": False,
        "review_evasion_detected": False,
        "ad_text": "SYNTHETIC_TEST_DATA neutral copy",
    }
    facts.update(updates)
    return facts


def test_policy_registry_allows_only_configured_official_hosts(root, tmp_path):
    pages, rules = _registries(root)
    assert len(pages["pages"]) == 6
    assert len(rules["rules"]) >= 20
    assert all(
        page["source_url"].startswith("https://business.x.com/")
        for page in pages["pages"]
    )

    invalid = json.loads(json.dumps(pages))
    invalid["pages"][0]["source_url"] = "https://example.invalid/not-x-policy"
    path = tmp_path / "invalid-policy-pages.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValidationError, match="Non-official X policy URL"):
        load_policy_registry(path)


def test_snapshots_rules_and_checklists_are_traceable_and_idempotent(database, root):
    first, pages, rules = _snapshot_all(database, root)
    assert first.snapshot_new_count == 6
    assert first.total_snapshot_count == 6
    assert first.rule_new_count == len(rules["rules"])
    assert first.checklist_new_count == 4

    snapshots = database.execute(
        "SELECT * FROM policy_snapshots ORDER BY policy_name"
    ).fetchall()
    assert len(snapshots) == 6
    for snapshot in snapshots:
        assert snapshot["content_text"].startswith("<html>")
        assert "SYNTHETIC_TEST_DATA" in snapshot["content_text"]
        assert snapshot["content_hash"] == hashlib.sha256(
            snapshot["content_text"].encode("utf-8")
        ).hexdigest()
        assert snapshot["page_updated_at"] == "UNKNOWN"
        assert snapshot["snapshot_version"] == "v1"
        assert snapshot["supersedes_snapshot_id"] is None
        assert snapshot["verification_status"] == "VERIFIED_OFFICIAL_HTTP_200"
        assert snapshot["source_url"].startswith("https://business.x.com/")

    rule_rows = database.execute(
        """
        SELECT pr.*, ps.source_url
        FROM policy_rules pr JOIN policy_snapshots ps ON ps.id = pr.snapshot_id
        """
    ).fetchall()
    assert len(rule_rows) == len(rules["rules"])
    assert all(row["evidence_url"] == row["source_url"] for row in rule_rows)
    assert all(row["snapshot_id"] for row in rule_rows)

    checklists = database.execute(
        "SELECT * FROM policy_checklist_templates WHERE status = 'ACTIVE'"
    ).fetchall()
    assert {(row["country"], row["product_category"]) for row in checklists} == {
        ("TW", "FINANCIAL_SERVICES"),
        ("TW", "CRYPTO"),
        ("US", "FINANCIAL_SERVICES"),
        ("US", "CRYPTO"),
    }
    for row in checklists:
        fields = json.loads(row["fields_json"])
        assert fields["advertiser_legal_name"] == "UNKNOWN"
        assert fields["financial_license_status"] == "UNKNOWN"
        assert fields["X_pre_authorization_status"] == "UNKNOWN"

    second, _, _ = _snapshot_all(database, root)
    assert second.snapshot_new_count == 0
    assert second.snapshot_existing_count == 6
    assert second.rule_new_count == 0
    assert second.total_snapshot_count == 6
    assert database.execute(
        "SELECT COUNT(*) FROM policy_checklist_templates"
    ).fetchone()[0] == 4
    assert {page["policy_key"] for page in pages["pages"]}


def test_changed_policy_appends_version_without_overwriting_history(database, root):
    _, pages, _ = _snapshot_all(database, root)
    changed_url = pages["pages"][0]["source_url"]
    original = database.execute(
        "SELECT id, content_text FROM policy_snapshots WHERE source_url = ?",
        (changed_url,),
    ).fetchone()

    result, _, _ = _snapshot_all(database, root, {changed_url: "v2 changed"})
    versions = database.execute(
        """
        SELECT id, content_text, snapshot_version, supersedes_snapshot_id
        FROM policy_snapshots WHERE source_url = ? ORDER BY snapshot_version
        """,
        (changed_url,),
    ).fetchall()
    assert result.snapshot_new_count == 1
    assert len(versions) == 2
    assert versions[0]["id"] == original["id"]
    assert versions[0]["content_text"] == original["content_text"]
    assert versions[1]["snapshot_version"] == "v2"
    assert versions[1]["supersedes_snapshot_id"] == original["id"]
    assert "v2 changed" in versions[1]["content_text"]


def test_precheck_without_snapshots_is_unknown(database):
    outcome = run_financial_ads_precheck(database, _complete_facts())
    assert outcome.result == "UNKNOWN"
    assert outcome.policy_snapshot_date == "UNKNOWN"


@pytest.mark.parametrize(
    ("updates", "expected"),
    [
        ({"financial_license_status": "UNKNOWN"}, "UNKNOWN"),
        ({"financial_license_status": "NOT_LICENSED"}, "BLOCKED"),
        ({"ad_text": "保证翻倍"}, "BLOCKED"),
        ({"fees_disclosed": False}, "REVIEW_REQUIRED"),
        ({"advertiser_legal_name": "UNKNOWN", "financial_license_status": "UNKNOWN"}, "UNKNOWN"),
        ({"X_account_verified": False}, "REVIEW_REQUIRED"),
        ({"bio_url_valid": False}, "REVIEW_REQUIRED"),
        ({"landing_page_matches_ad": False}, "BLOCKED"),
    ],
)
def test_fail_closed_precheck_cases(database, root, updates, expected):
    _snapshot_all(database, root)
    outcome = run_financial_ads_precheck(database, _complete_facts(**updates))
    assert outcome.result == expected
    assert outcome.result != "PASS_PRECHECK" or expected == "PASS_PRECHECK"


def test_complete_data_can_only_reach_internal_pass_precheck(database, root):
    _snapshot_all(database, root)
    outcome = run_financial_ads_precheck(database, _complete_facts())
    assert outcome.result == "PASS_PRECHECK"
    assert "不代表X批准" in outcome.disclaimer
    assert "Guaranteed Approval" not in outcome.disclaimer


def test_stale_policy_requires_review(database, root):
    _snapshot_all(database, root)
    database.execute("UPDATE policy_snapshots SET fetched_at = '2025-01-01T00:00:00+00:00'")
    database.commit()
    outcome = run_financial_ads_precheck(
        database,
        _complete_facts(),
        today=date(2026, 8, 14),
        max_policy_age_days=30,
    )
    assert outcome.result == "REVIEW_REQUIRED"


def test_compliance_page_shows_evidence_versions_and_four_checklists(database_path, root):
    from global_x_finance.db import connect

    connection = connect(database_path)
    try:
        _snapshot_all(connection, root)
    finally:
        connection.close()

    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.testing = True
    page = app.test_client().get("/compliance").get_data(as_text=True)
    assert "政策與合規" in page
    assert "6" in page
    assert "26" in page
    assert "Taiwan Financial Ads Checklist" in page
    assert "Taiwan Crypto Ads Checklist" in page
    assert "US Financial Ads Checklist" in page
    assert "US Crypto Ads Checklist" in page
    assert "UNKNOWN" in page
    assert "https://business.x.com/en/help/ads-policies" in page
    assert "v1" in page
