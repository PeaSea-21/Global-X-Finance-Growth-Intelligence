from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "ben_radar_channel_intake"

PROVENANCE = {
    "SUPPLIED",
    "DERIVED_FROM_SUPPLIED",
    "PROPOSED",
    "UNKNOWN",
    "CONFLICT",
}
CAPABILITY_STATES = {
    "AVAILABLE_VERIFIED",
    "AVAILABLE_BUT_PROTOTYPE",
    "PARTIAL",
    "UNKNOWN",
    "BLOCKED_RIGHTS",
    "NOT_IMPLEMENTED",
}
PROFILE_KEYS = {
    "channel_id",
    "channel_name",
    "source_index",
    "source_fields_raw",
    "profile_version",
    "profile_status",
    "channel_summary",
    "target_audience",
    "primary_market",
    "secondary_markets",
    "security_scope",
    "preferred_sectors",
    "preferred_entities",
    "preferred_topic_types",
    "excluded_topics",
    "prohibited_claims",
    "allowed_source_classes",
    "minimum_evidence_policy",
    "opinion_usage_policy",
    "maximum_data_age",
    "market_session_preferences",
    "preferred_formats",
    "content_depth",
    "title_intensity",
    "risk_tolerance",
    "required_disclosures",
    "daily_primary_target",
    "daily_backup_target_range",
    "shortage_policy",
    "recent_duplicate_window_days",
    "positive_examples",
    "negative_examples",
    "missing_fields",
    "conflicts",
    "proposed_fields",
    "field_provenance",
}
TOPIC_KEYS = {
    "topic_title",
    "readiness",
    "what_happened",
    "what_changed",
    "why_now",
    "why_channel",
    "related_market_qualified_security_ids",
    "market_session_date",
    "session_state",
    "data_as_of",
    "verified_facts",
    "derived_findings",
    "opinions",
    "unknowns",
    "source_conflicts",
    "evidence_ids",
    "independent_publisher_groups",
    "suggested_angles",
    "working_titles",
    "risk_flags",
}


def csv_rows(name: str) -> list[dict]:
    with (OUT / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    profile_doc = json.loads((OUT / "channel_profiles_v0.1.json").read_text(encoding="utf-8"))
    profiles = profile_doc["profiles"]
    assert profile_doc["actual_channel_count"] == 20
    assert len(profiles) == 20
    assert len({row["channel_id"] for row in profiles}) == 20
    assert len({row["channel_name"] for row in profiles}) == 20
    assert [row["source_index"] for row in profiles] == list(range(1, 21))

    for profile in profiles:
        assert PROFILE_KEYS <= set(profile)
        assert set(profile) <= set(profile["field_provenance"])
        assert set(profile["field_provenance"].values()) <= PROVENANCE
        assert profile["profile_version"] == "0.1-draft"
        assert profile["daily_primary_target"] == 5
        assert profile["daily_backup_target_range"] == [0, 3]
        assert profile["shortage_policy"] == "HONEST_SHORTAGE"
        assert profile["recent_duplicate_window_days"] == 30
        raw = profile["source_fields_raw"]
        assert raw["raw_channel_block"].startswith(profile["channel_name"] + "\n")
        assert raw["channel_summary_raw"] != "UNKNOWN"
        assert raw["target_audience_raw"] != "UNKNOWN"
        assert raw["update_frequency_raw"] != "UNKNOWN"
        assert raw["tags_raw"] != "UNKNOWN"
        assert raw["seo_keywords_raw"] != "UNKNOWN"
        assert profile["channel_name"] in raw["matrix_row_raw"]
        assert raw["brand_family_raw"]
        assert raw["brand_meaning_raw"]

    assert sum(profile["profile_status"] == "DRAFT_WITH_CONFLICT" for profile in profiles) == 3
    conflict_names = {
        profile["channel_name"]
        for profile in profiles
        if profile["profile_status"] == "DRAFT_WITH_CONFLICT"
    }
    assert conflict_names == {"半導體駭客", "華爾街溫度計", "鏈上顯微鏡"}

    overlap = csv_rows("channel_overlap_matrix.csv")
    coverage = csv_rows("channel_data_coverage_matrix.csv")
    questions = csv_rows("open_questions.csv")
    assert len(overlap) == len(coverage) == 20
    assert len(questions) == 7
    assert {row["channel_id"] for row in overlap} == {row["channel_id"] for row in profiles}
    assert {row["channel_id"] for row in coverage} == {row["channel_id"] for row in profiles}
    for row in coverage:
        for key, value in row.items():
            if key.endswith("_status"):
                assert value in CAPABILITY_STATES, (key, value)
        assert row["industry_mapping_status"] == "PARTIAL"
        assert row["us_eod_status"] == "NOT_IMPLEMENTED"
        assert row["feedback_1h_6h_24h_status"] == "NOT_IMPLEMENTED"

    example_doc = json.loads((OUT / "pilot_topic_card_examples.json").read_text(encoding="utf-8"))
    assert len(example_doc["pilots"]) == 3
    assert {row["pilot_type"] for row in example_doc["pilots"]} == {
        "SIGNAL_HEAVY",
        "EVENT_HEAVY",
        "CROSS_ENTITY",
    }
    examples = [example for pilot in example_doc["pilots"] for example in pilot["examples"]]
    assert len(examples) == 15
    for example in examples:
        assert TOPIC_KEYS <= set(example)
        assert example["data_label"] == "SCHEMA_EXAMPLE_NOT_REAL_TOPIC"
        assert example["market_session_date"] == "<YYYY-MM-DD>"
        assert example["readiness"] in {"READY_TO_PITCH", "NEEDS_RESEARCH", "WATCH_ONLY"}

    print(
        "PASS: 20 profiles, 20 overlap rows, 20 coverage rows, "
        "3 pilots, 15 labeled schema examples, 7 material questions"
    )


if __name__ == "__main__":
    main()
