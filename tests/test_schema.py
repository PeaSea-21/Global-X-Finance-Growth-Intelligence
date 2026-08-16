EXPECTED_TABLES = {
    "markets", "market_pack_versions", "sources", "collection_runs", "raw_items",
    "normalized_items", "entities", "item_entities", "topics", "topic_items",
    "trend_snapshots", "claims", "evidence_links", "content_drafts",
    "verification_runs", "policy_snapshots", "compliance_checks", "review_decisions",
}


def test_all_contract_tables_exist(database):
    tables = {
        row[0]
        for row in database.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert EXPECTED_TABLES <= tables


def test_unknown_and_needs_verification_can_be_saved(database):
    database.execute(
        "UPDATE markets SET status = 'UNKNOWN' WHERE country_code = 'US'"
    )
    database.execute(
        "UPDATE sources SET collection_status = 'NEEDS_VERIFICATION' WHERE source_id = 'TW-A01'"
    )
    database.commit()
    assert database.execute(
        "SELECT status FROM markets WHERE country_code = 'US'"
    ).fetchone()[0] == "UNKNOWN"
    assert database.execute(
        "SELECT collection_status FROM sources WHERE source_id = 'TW-A01'"
    ).fetchone()[0] == "NEEDS_VERIFICATION"

