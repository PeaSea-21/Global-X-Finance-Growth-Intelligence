from __future__ import annotations

import sqlite3

import pytest

from global_x_finance.evidence import EvidenceStore


def test_duplicate_url_or_content_hash_is_exactly_deduplicated(database):
    store = EvidenceStore(database)
    first = store.save_raw_item(
        source_id="TW-A01",
        original_url="https://synthetic.invalid/item/one",
        original_content="SYNTHETIC_TEST_DATA first evidence",
        published_at="2026-01-01T00:00:00+00:00",
        fetched_at="2026-01-01T00:01:00+00:00",
        raw_payload={"label": "SYNTHETIC_TEST_DATA"},
        data_label="SYNTHETIC_TEST_DATA",
    )
    same_url = store.save_raw_item(
        source_id="TW-A02",
        original_url="https://synthetic.invalid/item/one",
        original_content="SYNTHETIC_TEST_DATA changed body",
        published_at="2026-01-01T00:00:00+00:00",
        data_label="SYNTHETIC_TEST_DATA",
    )
    same_hash = store.save_raw_item(
        source_id="TW-A06",
        original_url="https://synthetic.invalid/item/two",
        original_content="SYNTHETIC_TEST_DATA first evidence",
        published_at=None,
        data_label="SYNTHETIC_TEST_DATA",
    )

    assert first.created is True
    assert same_url == type(same_url)(first.id, False, "original_url")
    assert same_hash == type(same_hash)(first.id, False, "content_hash")
    assert database.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0] == 1


def test_raw_evidence_fields_are_immutable(database):
    item = EvidenceStore(database).save_raw_item(
        source_id="TW-A01",
        original_url="https://synthetic.invalid/immutable",
        original_content="SYNTHETIC_TEST_DATA immutable evidence",
        published_at=None,
        raw_payload={"label": "SYNTHETIC_TEST_DATA"},
        data_label="SYNTHETIC_TEST_DATA",
    )

    with pytest.raises(sqlite3.IntegrityError, match="raw evidence fields are immutable"):
        database.execute(
            "UPDATE raw_items SET original_content = ? WHERE id = ?",
            ("SYNTHETIC_TEST_DATA ai overwrite", item.id),
        )


def test_raw_item_keeps_required_traceability_fields(database):
    item = EvidenceStore(database).save_raw_item(
        source_id="TW-A01",
        original_url="https://synthetic.invalid/traceable",
        original_content="SYNTHETIC_TEST_DATA traceable content",
        published_at="2026-01-01T00:00:00Z",
        fetched_at="2026-01-01T00:02:00Z",
        data_label="SYNTHETIC_TEST_DATA",
    )
    row = database.execute("SELECT * FROM raw_items WHERE id = ?", (item.id,)).fetchone()
    assert row["original_content"] == "SYNTHETIC_TEST_DATA traceable content"
    assert row["original_url"] == "https://synthetic.invalid/traceable"
    assert row["published_at"] == "2026-01-01T00:00:00Z"
    assert row["fetched_at"] == "2026-01-01T00:02:00Z"
    assert len(row["content_hash"]) == 64

