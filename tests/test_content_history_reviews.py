from __future__ import annotations

import json

import pytest

from scripts.apply_content_history_reviews import apply_updates
from global_x_finance.content_studio import archive_workbench_channels


def _site(tmp_path):
    topic = {
        "candidate_id": "topic-1",
        "title": "原始標題",
        "why_now": ["原始理由"],
        "why_channel": ["原始頻道理由"],
        "facts": ["原始事實"],
        "unknowns": ["後續未知"],
        "evidence": [],
        "script_text": "這是永遠不能被結果回顧改寫的原始完整文稿。",
    }
    workbench = archive_workbench_channels(
        {
            "channels": [
                {
                    "channel_id": "ch-test",
                    "channel_name": "測試頻道",
                    "content_date": "2026-08-21",
                    "topics": [topic],
                }
            ]
        },
        tmp_path,
    )
    site_path = tmp_path / "data.json"
    site_path.write_text(
        json.dumps({"channel_workbench": workbench}, ensure_ascii=False),
        encoding="utf-8",
    )
    entry = workbench["channel_history_index"][0]
    return site_path, entry


def test_evidence_backed_review_is_append_only_and_idempotent(tmp_path) -> None:
    site_path, entry = _site(tmp_path)
    artifact_path = tmp_path / entry["path"]
    original_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    updates_path = tmp_path / "updates.json"
    updates_path.write_text(
        json.dumps(
            {
                "updates": [
                    {
                        "snapshot_fingerprint": entry["snapshot_fingerprint"],
                        "candidate_id": "topic-1",
                        "status": "CONFIRMED",
                        "summary": "後續正式資料已經滿足原稿列出的核驗條件。",
                        "observation_date": "2026-08-24",
                        "measured_result": "觀察值符合條件",
                        "evidence": [
                            {
                                "source_id": "OFFICIAL",
                                "title": "官方結果",
                                "human_verification_url": "https://example.com/result",
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    first = apply_updates(site_path, updates_path)
    second = apply_updates(site_path, updates_path)
    updated_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    updated_site = json.loads(site_path.read_text(encoding="utf-8"))

    assert first["applied_count"] == 1
    assert second["duplicate_count"] == 1
    assert updated_artifact["channel"] == original_artifact["channel"]
    assert len(updated_artifact["review_events"]) == 1
    assert updated_site["channel_workbench"]["channel_history_index"][0]["status_counts"] == {
        "CONFIRMED": 1
    }


def test_resolved_review_without_evidence_is_rejected(tmp_path) -> None:
    site_path, entry = _site(tmp_path)
    updates_path = tmp_path / "updates.json"
    updates_path.write_text(
        json.dumps(
            {
                "updates": [
                    {
                        "snapshot_fingerprint": entry["snapshot_fingerprint"],
                        "candidate_id": "topic-1",
                        "status": "CONFIRMED",
                        "summary": "聲稱說中但沒有結果來源，必須拒絕。",
                        "observation_date": "2026-08-24",
                        "evidence": [],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires Evidence"):
        apply_updates(site_path, updates_path)
