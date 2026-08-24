import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "research" / "ben_radar_close_talk" / "style_pack_v0.1.json"


def test_close_talk_style_pack_is_provisional_and_evidence_bounded():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))

    assert pack["channel_name"] == "收盤夜話"
    assert pack["status"] == "PROVISIONAL_TWO_FULL_TRANSCRIPTS"
    assert len(pack["sample_evidence"]) == 2
    assert all(
        sample["text_status"] == "FULL_NOISY_ASR_SUPPLIED_IN_CHAT"
        for sample in pack["sample_evidence"]
    )
    assert all(
        sample["finance_fact_status"] == "NOT_A_CURRENT_FACT_SOURCE"
        for sample in pack["sample_evidence"]
    )
    assert len(pack["old_corpus_references"]) == 3
    assert all(len(row["attachment_sha256"]) == 64 for row in pack["old_corpus_references"])
    assert len(pack["repeated_mechanisms"]) >= 5
    assert any("共同催化" in row for row in pack["repeated_mechanisms"])
    assert any("Line" in row for row in pack["observed_gaps"])


def test_close_talk_daily_contract_requires_market_structure_and_sources():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    contract = pack["daily_output_contract"]

    assert contract["ranked_episode_angles"] == 5
    assert contract["full_drafts_for_top_ranked"] == 5
    assert contract["target_script_characters"]["minimum"] == 3000
    assert "source_cards" in contract["required_angle_fields"]
    assert "cash_and_derivatives_flow" in contract["required_script_sections"]
    assert "tomorrow_checkpoints" in contract["required_script_sections"]
    assert pack["topic_eligibility"]["composite_score_status"].startswith("NOT_ADOPTED")
    assert "TAIFEX futures close, basis, open interest and institutional positions" in pack["source_requirements"]["leverage_and_positioning"]


def test_close_talk_pack_rejects_promotional_and_unsupported_generation():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    prohibited = " ".join(pack["language_controls"]["must_not_do"])

    assert "Line groups" in prohibited
    assert "guaranteed returns" in prohibited
    assert "Invent index contribution" in prohibited


def test_first_ten_style_pack_keeps_missing_transcripts_unknown():
    first_ten = json.loads(
        (ROOT / "research" / "ben_radar_first10_style_packs" / "style_packs_v0.1.json")
        .read_text(encoding="utf-8")
    )
    channels = first_ten["channels"]

    assert len(channels) == 10
    assert sum(channel["sample_count"] for channel in channels) == 12
    assert first_ten["global_contract"]["crawl_days"] == ["MO", "TU", "WE", "TH", "FR", "SU"]
    missing = [channel for channel in channels if channel["sample_count"] == 0]
    assert {channel["channel_name"] for channel in missing} == {"個股顯微鏡", "產業透視鏡", "財報獵人"}
    assert all(channel["language_style"] == "UNKNOWN_NO_TRANSCRIPT" for channel in missing)
    assert all(channel["status"] == "NO_TRANSCRIPT_NEEDS_SAMPLES" for channel in missing)


def test_first_ten_style_pack_flags_profile_sample_mismatches():
    first_ten = json.loads(
        (ROOT / "research" / "ben_radar_first10_style_packs" / "style_packs_v0.1.json")
        .read_text(encoding="utf-8")
    )
    by_name = {channel["channel_name"]: channel for channel in first_ten["channels"]}

    assert "PROFILE_SAMPLE_MISMATCH" in by_name["資金雷達"]["profile_sample_alignment"]
    assert "PROFILE_SAMPLE_MISMATCH" in by_name["板塊輪動儀"]["profile_sample_alignment"]
    assert "TRUE_DARK_POOL" in by_name["暗池雷達"]["profile_sample_alignment"]
