from __future__ import annotations

import copy
import json

import pytest

from global_x_finance.errors import ValidationError
from global_x_finance.twse_collector import (
    HttpResponse,
    TwseOpenApiCollector,
    load_twse_config,
)


def _config(root):
    return load_twse_config(root / "config" / "twse_openapi.datasets.json")


def _one_dataset(config, index=0):
    selected = copy.deepcopy(config)
    selected["datasets"] = [selected["datasets"][index]]
    return selected


def _synthetic_response(url: str, timeout: float) -> HttpResponse:
    assert url.startswith("https://openapi.twse.com.tw/v1/")
    assert timeout > 0
    if url.endswith("MI_INDEX"):
        payload = [{"日期": "1150814", "指數": "SYNTHETIC_TEST_DATA", "收盤指數": "0"}]
    elif url.endswith("MI_QFIIS_cat"):
        payload = [{"IndustryCat": "SYNTHETIC_TEST_DATA", "Percentage": "0"}]
    else:
        payload = [{"Date": "1150814", "Code": "SYNTHETIC_TEST_DATA", "Name": "測試資料"}]
    return HttpResponse(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def test_non_api_verified_source_is_rejected(database, root):
    config = _config(root)
    source = database.execute(
        "SELECT source_id FROM sources WHERE collection_status <> 'API_VERIFIED' LIMIT 1"
    ).fetchone()

    with pytest.raises(ValidationError, match="Automatic collection denied"):
        TwseOpenApiCollector(
            database, config, transport=_synthetic_response, test_mode=True
        ).collect_all(source["source_id"])

    assert database.execute("SELECT COUNT(*) FROM collection_runs").fetchone()[0] == 0


def test_success_saves_complete_synthetic_evidence(database, root):
    config = _config(root)
    batch = TwseOpenApiCollector(
        database, config, transport=_synthetic_response, test_mode=True
    ).collect_all()

    assert batch.status == "SUCCESS"
    assert batch.new_count == 3
    rows = database.execute(
        "SELECT original_content, original_url, published_at, fetched_at, "
        "content_hash, raw_payload_json, data_label FROM raw_items ORDER BY created_at"
    ).fetchall()
    assert len(rows) == 3
    assert {row["data_label"] for row in rows} == {"SYNTHETIC_TEST_DATA"}
    assert all(row["original_url"].startswith("https://openapi.twse.com.tw/v1/") for row in rows)
    assert all(len(row["content_hash"]) == 64 for row in rows)
    assert json.loads(rows[0]["raw_payload_json"])
    assert rows[1]["published_at"] is None


@pytest.mark.parametrize(
    ("transport", "expected_code"),
    [
        (lambda url, timeout: (_ for _ in ()).throw(TimeoutError("SYNTHETIC_TEST_DATA timeout")), "TIMEOUT"),
        (lambda url, timeout: HttpResponse(503, b"SYNTHETIC_TEST_DATA"), "HTTP_503"),
    ],
)
def test_api_failure_is_recorded_without_fake_items(database, root, transport, expected_code):
    config = _one_dataset(_config(root))
    batch = TwseOpenApiCollector(
        database, config, transport=transport, test_mode=True
    ).collect_all()

    assert batch.status == "FAILED"
    run = database.execute(
        "SELECT status, error_code, finished_at FROM collection_runs"
    ).fetchone()
    assert run["status"] == "FAILED"
    assert run["error_code"] == expected_code
    assert run["finished_at"] is not None
    assert database.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0] == 0


def test_second_sync_is_duplicate_and_does_not_overwrite_evidence(database, root):
    config = _one_dataset(_config(root))
    collector = TwseOpenApiCollector(
        database, config, transport=_synthetic_response, test_mode=True
    )
    first = collector.collect_all()
    before = database.execute(
        "SELECT id, original_content, raw_payload_json, content_hash, fetched_at FROM raw_items"
    ).fetchone()
    second = collector.collect_all()
    after = database.execute(
        "SELECT id, original_content, raw_payload_json, content_hash, fetched_at FROM raw_items"
    ).fetchone()

    assert first.new_count == 1
    assert second.new_count == 0
    assert second.duplicate_count == 1
    assert dict(after) == dict(before)
    assert database.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0] == 1

