from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CHANNELS = (
    "個股顯微鏡",
    "收盤夜話",
    "產業透視鏡",
    "權值旗艦",
    "資金雷達",
    "那指火箭",
    "板塊輪動儀",
    "暗池雷達",
    "期權守門人",
    "財報獵人",
    "宏觀天秤",
    "全球資金地圖",
    "地緣炸藥庫",
    "週期航海家",
    "鏈上顯微鏡",
    "中概風向球",
    "財商拆彈組",
    "半導體駭客",
    "華爾街溫度計",
    "定投實驗室",
)
WAITING_CHANNELS = {
    "個股顯微鏡",
    "產業透視鏡",
    "財報獵人",
    "宏觀天秤",
    "地緣炸藥庫",
    "週期航海家",
    "半導體駭客",
    "華爾街溫度計",
    "定投實驗室",
}
SCRIPT_REQUIREMENTS = {
    "收盤夜話": ("約15分鐘", 3000),
    "權值旗艦": ("約5至8分鐘", 2000),
    "資金雷達": ("約3至5分鐘", 1500),
    "那指火箭": ("約5至8分鐘", 2000),
    "板塊輪動儀": ("約5至8分鐘", 2000),
    "暗池雷達": ("約3至5分鐘", 1500),
    "期權守門人": ("約3分鐘", 1200),
    "全球資金地圖": ("約5至8分鐘", 2000),
    "鏈上顯微鏡": ("約3至5分鐘", 1500),
    "中概風向球": ("約3至5分鐘", 1500),
    "財商拆彈組": ("約3分鐘", 1200),
}
INTERNAL_SCRIPT_TERMS = ("資料包", "稿件", "模板", "來源卡", "必須改寫")
OUTCOME_STATES = {
    "CONFIRMED",
    "PARTIALLY_CONFIRMED",
    "NOT_CONFIRMED",
    "INVALIDATED",
    "PENDING_DATA",
}
RESOLVED_OUTCOME_STATES = OUTCOME_STATES - {"PENDING_DATA"}
SOURCE_TIME_FIELDS = (
    "published_at",
    "fetched_at",
    "trade_date",
    "observed_at",
    "data_as_of",
    "announced_at",
)


def _character_count(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def _is_http_url(value: Any) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_iso_time(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _unknown_text(channel: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for topic in channel.get("topics") or []
        for value in topic.get("unknowns") or []
    )


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    channels = list(payload.get("channels") or [])
    names = [row.get("channel_name") for row in channels]
    if tuple(names) != EXPECTED_CHANNELS:
        violations.append(f"channel order mismatch: {names}")
    if payload.get("channel_count") != 20:
        violations.append("channel_count must be 20")
    if payload.get("draft_ready_channel_count") != 11:
        violations.append("draft_ready_channel_count must be 11")
    if payload.get("waiting_sample_channel_count") != 9:
        violations.append("waiting_sample_channel_count must be 9")
    if payload.get("transcript_sample_count") != 19:
        violations.append("transcript_sample_count must be 19")
    if payload.get("public_visible_channel_count") != 11:
        violations.append("public_visible_channel_count must be 11")
    if payload.get("hidden_waiting_channel_count") != 9:
        violations.append("hidden_waiting_channel_count must be 9")

    topic_count = 0
    full_script_count = 0
    source_count = 0
    source_time_count = 0
    seen_titles: dict[str, str] = {}
    seen_scripts: dict[str, str] = {}
    seen_selection_reasons: dict[str, str] = {}
    shared_hotspots: Counter[str] = Counter()
    channel_length_stats: dict[str, dict[str, Any]] = {}
    for channel in channels:
        name = str(channel.get("channel_name") or "")
        topics = list(channel.get("topics") or [])
        if name in WAITING_CHANNELS:
            if channel.get("content_status") != "WAITING_FOR_TRANSCRIPT_SAMPLES":
                violations.append(f"{name}: missing-sample status is incorrect")
            if topics:
                violations.append(f"{name}: must not contain generated topics")
            if "NO_TRANSCRIPT" not in str(channel.get("style_status") or ""):
                violations.append(f"{name}: style status must preserve missing transcript")
            continue
        if not topics:
            violations.append(f"{name}: expected at least one review topic")
            continue
        if len(topics) != 5:
            violations.append(f"{name}: expected five review topics, got {len(topics)}")
        if not str(channel.get("style_status") or "").startswith("PROVISIONAL"):
            violations.append(f"{name}: ready channel must remain provisional")
        required_duration, required_minimum = SCRIPT_REQUIREMENTS[name]
        if channel.get("target_duration") != required_duration:
            violations.append(f"{name}: target duration must be {required_duration}")
        if channel.get("minimum_script_character_count") != required_minimum:
            violations.append(f"{name}: minimum character count must be {required_minimum}")
        channel_script_count = 0
        channel_lengths: list[int] = []
        for index, topic in enumerate(topics, start=1):
            topic_count += 1
            label = f"{name} topic {index}"
            title_options = list(topic.get("title_options") or [])
            if len(title_options) < 2:
                violations.append(f"{label}: fewer than two title options")
            for title in title_options:
                normalized = re.sub(r"\s+", "", str(title)).casefold()
                previous = seen_titles.get(normalized)
                if previous:
                    violations.append(f"{label}: duplicate public title also used by {previous}")
                elif normalized:
                    seen_titles[normalized] = label
            hotspot_id = str(topic.get("shared_hotspot_id") or "")
            if hotspot_id:
                shared_hotspots[hotspot_id] += 1
            if not topic.get("why_now"):
                violations.append(f"{label}: why_now is empty")
            if not topic.get("why_channel"):
                violations.append(f"{label}: why_channel is empty")
            if not topic.get("unknowns"):
                violations.append(f"{label}: unknowns are empty")
            core_question = str(topic.get("core_question") or "").strip()
            selection_reason = topic.get("selection_reason") or {}
            selection_summary = str(selection_reason.get("summary") or "").strip()
            if len(core_question) < 20:
                violations.append(f"{label}: core_question is missing or too generic")
            if str(topic.get("title") or "") not in core_question:
                violations.append(f"{label}: core_question does not preserve the displayed title")
            required_reason_fields = (
                "summary",
                "what_changed",
                "audience_relevance",
                "channel_fit",
                "editorial_tension",
                "next_verification",
            )
            for field in required_reason_fields:
                if len(str(selection_reason.get(field) or "").strip()) < 12:
                    violations.append(f"{label}: selection_reason.{field} is missing or generic")
            dimensions = list(selection_reason.get("dimensions") or [])
            if len(dimensions) < 5:
                violations.append(f"{label}: selection reason has fewer than five dimensions")
            normalized_reason = re.sub(r"\s+", "", selection_summary).casefold()
            previous_reason = seen_selection_reasons.get(normalized_reason)
            if previous_reason:
                violations.append(
                    f"{label}: duplicate selection reason also used by {previous_reason}"
                )
            elif normalized_reason:
                seen_selection_reasons[normalized_reason] = label
            script = str(topic.get("script_text") or "")
            if script:
                full_script_count += 1
                channel_script_count += 1
                expected_count = _character_count(script)
                if topic.get("script_character_count") != expected_count:
                    violations.append(
                        f"{label}: character count mismatch "
                        f"{topic.get('script_character_count')} != {expected_count}"
                    )
                if expected_count < required_minimum:
                    violations.append(
                        f"{label}: complete manuscript is too short "
                        f"({expected_count} < {required_minimum})"
                    )
                if topic.get("script_target_duration") != required_duration:
                    violations.append(f"{label}: script target duration is incorrect")
                if topic.get("script_minimum_character_count") != required_minimum:
                    violations.append(f"{label}: script minimum is incorrect")
                if topic.get("script_meets_target") is not True:
                    violations.append(f"{label}: script target flag is not true")
                normalized_script = re.sub(r"\s+", "", script)
                previous_script = seen_scripts.get(normalized_script)
                if previous_script:
                    violations.append(f"{label}: duplicate body also used by {previous_script}")
                else:
                    seen_scripts[normalized_script] = label
                for term in INTERNAL_SCRIPT_TERMS:
                    if term in script:
                        violations.append(f"{label}: internal production wording remains: {term}")
                alignment = topic.get("manuscript_alignment") or {}
                normalized_current_script = re.sub(r"\s+", "", script).casefold()
                if re.sub(r"\s+", "", str(topic.get("title") or "")).casefold() not in normalized_current_script:
                    violations.append(f"{label}: audit recompute found title absent from manuscript")
                if re.sub(r"\s+", "", selection_summary).casefold() not in normalized_current_script:
                    violations.append(f"{label}: audit recompute found selection reason absent from manuscript")
                for claim_index, claim in enumerate(topic.get("script_claims") or [], start=1):
                    normalized_claim = re.sub(r"\s+", "", str(claim)).casefold()
                    if normalized_claim and normalized_claim not in normalized_current_script:
                        violations.append(
                            f"{label}: audit recompute found claim {claim_index} absent from manuscript"
                        )
                if alignment.get("contract_version") != "2.0":
                    violations.append(f"{label}: manuscript contract version is not 2.0")
                if alignment.get("status") != "PASS":
                    violations.append(f"{label}: manuscript does not align with its topic contract")
                if alignment.get("title_present") is not True:
                    violations.append(f"{label}: displayed title is absent from manuscript")
                if alignment.get("selection_reason_present") is not True:
                    violations.append(f"{label}: selection reason is absent from manuscript")
                if list(alignment.get("uncovered_claim_indexes") or []):
                    violations.append(f"{label}: displayed facts are not fully covered by manuscript")
                evidence_ids = [
                    str(row.get("source_id") or "").strip()
                    for row in list(topic.get("evidence") or [])
                    if str(row.get("source_id") or "").strip()
                ]
                if list(dict.fromkeys(evidence_ids)) != list(topic.get("script_evidence_ids") or []):
                    violations.append(f"{label}: manuscript evidence IDs do not match topic Evidence")
                checkpoints = list(topic.get("review_checkpoints") or [])
                if len(checkpoints) < 3:
                    violations.append(f"{label}: fewer than three future review checkpoints")
                for checkpoint_index, checkpoint in enumerate(checkpoints, start=1):
                    status = checkpoint.get("status")
                    if status not in OUTCOME_STATES:
                        violations.append(
                            f"{label}: checkpoint {checkpoint_index} has invalid outcome status"
                        )
                    if status in RESOLVED_OUTCOME_STATES and (
                        not checkpoint.get("observation_date")
                        or not list(checkpoint.get("evidence") or [])
                    ):
                        violations.append(
                            f"{label}: resolved checkpoint {checkpoint_index} lacks dated Evidence"
                        )
                outcome = topic.get("outcome_review") or {}
                outcome_status = outcome.get("status")
                if outcome_status not in OUTCOME_STATES:
                    violations.append(f"{label}: invalid outcome review status")
                if outcome_status in RESOLVED_OUTCOME_STATES and (
                    not outcome.get("observation_date")
                    or not list(outcome.get("evidence") or [])
                ):
                    violations.append(f"{label}: resolved outcome review lacks dated Evidence")
                channel_lengths.append(expected_count)
            else:
                violations.append(f"{label}: complete manuscript is missing")
            if topic.get("candidate_type") == "CHANNEL_TOPIC_OUTLINE":
                violations.append(f"{label}: outline candidate remains in public payload")
            evidence = list(topic.get("evidence") or [])
            if not evidence:
                violations.append(f"{label}: evidence is empty")
            for source_index, source in enumerate(evidence, start=1):
                source_count += 1
                human_url = source.get("human_verification_url")
                raw_url = source.get("raw_api_url")
                if not _is_http_url(human_url):
                    violations.append(
                        f"{label} source {source_index}: human verification URL is invalid"
                    )
                if raw_url and raw_url == human_url:
                    violations.append(
                        f"{label} source {source_index}: raw URL duplicates primary URL"
                    )
                if human_url and (
                    "openapi.twse.com.tw" in human_url
                    or "response=json" in human_url
                    or human_url.endswith(".json")
                ):
                    violations.append(
                        f"{label} source {source_index}: raw API used as primary URL"
                    )
                time_values = [source.get(field) for field in SOURCE_TIME_FIELDS]
                if not any(str(value or "").strip() for value in time_values):
                    violations.append(
                        f"{label} source {source_index}: source publication or fetch time is missing"
                    )
                else:
                    source_time_count += 1
                for field in ("published_at", "fetched_at"):
                    value = source.get(field)
                    if value and not _is_iso_time(value):
                        violations.append(
                            f"{label} source {source_index}: {field} is not ISO date/time"
                        )
        if channel_script_count != 5:
            violations.append(
                f"{name}: expected five complete manuscripts, got {channel_script_count}"
            )
        if channel_lengths:
            channel_length_stats[name] = {
                "minimum_required": required_minimum,
                "minimum_actual": min(channel_lengths),
                "maximum_actual": max(channel_lengths),
                "average_actual": round(sum(channel_lengths) / len(channel_lengths), 1),
            }

    if topic_count != 55:
        violations.append(f"topic_count must be 55, got {topic_count}")
    if full_script_count != 55:
        violations.append(f"full_script_count must be 55, got {full_script_count}")
    if not any(count >= 2 for count in shared_hotspots.values()):
        violations.append("shared hotspot coverage across channels is missing")

    history_index = list(payload.get("channel_history_index") or [])
    history_channels = {
        str(row.get("channel_name") or "") for row in history_index
    }
    ready_names = set(SCRIPT_REQUIREMENTS)
    if not ready_names.issubset(history_channels):
        violations.append("history index does not cover every visible channel")
    if payload.get("history_entry_count") != len(history_index):
        violations.append("history_entry_count does not match history index")
    seen_history_fingerprints: set[str] = set()
    for index, row in enumerate(history_index, start=1):
        fingerprint = str(row.get("snapshot_fingerprint") or "")
        path = str(row.get("path") or "")
        if len(fingerprint) != 64 or fingerprint in seen_history_fingerprints:
            violations.append(f"history entry {index}: invalid or duplicate fingerprint")
        seen_history_fingerprints.add(fingerprint)
        if not re.fullmatch(r"history/[A-Za-z0-9_-]+/\d{4}-\d{2}-\d{2}--[a-f0-9]{12}\.json", path):
            violations.append(f"history entry {index}: invalid history path")

    gaps = payload.get("structured_data_gaps") or {}
    for field in ("ETF_NET_FLOWS", "ONCHAIN_ADDRESS_METRICS", "OPTIONS_CHAIN_IV_OI", "DARK_POOL_PRINTS"):
        if gaps.get(field) != "UNAVAILABLE":
            violations.append(f"structured data gap must remain UNAVAILABLE: {field}")

    by_name = {row.get("channel_name"): row for row in channels}
    required_unknown_fragments = {
        "暗池雷達": ("暗池", "期權鏈"),
        "期權守門人": ("IV", "OI"),
        "全球資金地圖": ("ETF", "DXY"),
        "鏈上顯微鏡": ("鏈上地址", "OI"),
        "中概風向球": ("港交所", "CNH"),
        "財商拆彈組": ("個人完整資產", "官方費率"),
    }
    for name, fragments in required_unknown_fragments.items():
        unknowns = _unknown_text(by_name.get(name, {}))
        for fragment in fragments:
            if fragment not in unknowns:
                violations.append(f"{name}: unknowns must disclose {fragment}")

    return {
        "status": "PASS" if not violations else "FAIL",
        "channel_count": len(channels),
        "topic_count": topic_count,
        "full_script_count": full_script_count,
        "source_count": source_count,
        "source_time_count": source_time_count,
        "unique_script_count": len(seen_scripts),
        "history_entry_count": len(history_index),
        "channel_length_stats": channel_length_stats,
        "violation_count": len(violations),
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the all-20 BEN workbench.")
    parser.add_argument(
        "--input",
        default=str(
            ROOT
            / "outputs"
            / "ben_all20_editorial"
            / "2026-08-23"
            / "all20_editorial.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=str(
            ROOT
            / "outputs"
            / "ben_all20_editorial"
            / "2026-08-23"
            / "all20_editorial_audit.json"
        ),
    )
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = audit(payload)
    report["input_sha256"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
