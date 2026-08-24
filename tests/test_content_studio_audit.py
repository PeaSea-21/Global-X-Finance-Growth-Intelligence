from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from scripts.audit_all20_content_studio import audit


ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict:
    return json.loads(
        (ROOT / "sites" / "ben-content-studio" / "data.json").read_text(
            encoding="utf-8"
        )
    )["channel_workbench"]


def test_current_workbench_topic_contracts_pass() -> None:
    report = audit(_payload())

    assert report["status"] == "PASS"
    assert report["violation_count"] == 0
    assert report["history_entry_count"] >= 11


def test_audit_recomputes_topic_to_manuscript_alignment() -> None:
    payload = deepcopy(_payload())
    topic = next(channel for channel in payload["channels"] if channel["topics"])["topics"][0]
    topic["script_text"] = topic["script_text"].replace(topic["title"], "完全無關的替代標題")
    topic["script_character_count"] = len("".join(topic["script_text"].split()))

    report = audit(payload)

    assert report["status"] == "FAIL"
    assert any("audit recompute found title absent" in row for row in report["violations"])


def test_resolved_review_requires_dated_evidence() -> None:
    payload = deepcopy(_payload())
    topic = next(channel for channel in payload["channels"] if channel["topics"])["topics"][0]
    topic["outcome_review"] = {
        "status": "CONFIRMED",
        "summary": "說中了",
        "observation_date": None,
        "evidence": [],
    }

    report = audit(payload)

    assert report["status"] == "FAIL"
    assert any("resolved outcome review lacks dated Evidence" in row for row in report["violations"])


def test_public_source_requires_a_publication_or_fetch_time() -> None:
    payload = deepcopy(_payload())
    topic = next(channel for channel in payload["channels"] if channel["topics"])["topics"][0]
    source = topic["evidence"][0]
    for field in (
        "published_at",
        "fetched_at",
        "trade_date",
        "observed_at",
        "data_as_of",
        "announced_at",
    ):
        source.pop(field, None)

    report = audit(payload)

    assert report["status"] == "FAIL"
    assert any(
        "source publication or fetch time is missing" in row
        for row in report["violations"]
    )
