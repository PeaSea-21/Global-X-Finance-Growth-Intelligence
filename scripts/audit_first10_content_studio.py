from __future__ import annotations

import argparse
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
)
WAITING_CHANNELS = {"個股顯微鏡", "產業透視鏡", "財報獵人"}


def _character_count(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def _is_http_url(value: Any) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    channels = list(payload.get("channels") or [])
    names = [row.get("channel_name") for row in channels]
    if tuple(names) != EXPECTED_CHANNELS:
        violations.append(f"channel order mismatch: {names}")
    if payload.get("channel_count") != 10:
        violations.append("channel_count must be 10")
    if payload.get("draft_ready_channel_count") != 7:
        violations.append("draft_ready_channel_count must be 7")
    if payload.get("waiting_sample_channel_count") != 3:
        violations.append("waiting_sample_channel_count must be 3")

    topic_count = 0
    full_script_count = 0
    source_count = 0
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
        for index, topic in enumerate(topics, start=1):
            topic_count += 1
            label = f"{name} topic {index}"
            title_options = list(topic.get("title_options") or [])
            if len(title_options) < 2:
                violations.append(f"{label}: fewer than two title options")
            if not topic.get("why_now"):
                violations.append(f"{label}: why_now is empty")
            if not topic.get("why_channel"):
                violations.append(f"{label}: why_channel is empty")
            if not topic.get("unknowns"):
                violations.append(f"{label}: unknowns are empty")
            script = str(topic.get("script_text") or "")
            if script:
                full_script_count += 1
                expected_count = _character_count(script)
                if topic.get("script_character_count") != expected_count:
                    violations.append(
                        f"{label}: character count mismatch "
                        f"{topic.get('script_character_count')} != {expected_count}"
                    )
            elif name != "收盤夜話":
                violations.append(f"{label}: full script is missing")
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

    by_name = {row.get("channel_name"): row for row in channels}
    dark_unknowns = " ".join(
        str(value)
        for topic in by_name.get("暗池雷達", {}).get("topics", [])
        for value in topic.get("unknowns", [])
    )
    if "暗池" not in dark_unknowns or "期權鏈" not in dark_unknowns:
        violations.append("暗池雷達 must disclose missing dark-pool and options-chain evidence")
    option_unknowns = " ".join(
        str(value)
        for topic in by_name.get("期權守門人", {}).get("topics", [])
        for value in topic.get("unknowns", [])
    )
    if "IV" not in option_unknowns or "OI" not in option_unknowns:
        violations.append("期權守門人 must disclose missing IV and OI")

    return {
        "status": "PASS" if not violations else "FAIL",
        "channel_count": len(channels),
        "topic_count": topic_count,
        "full_script_count": full_script_count,
        "source_count": source_count,
        "violation_count": len(violations),
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the first-ten BEN workbench.")
    parser.add_argument(
        "--input",
        default=str(
            ROOT
            / "outputs"
            / "ben_first10_editorial"
            / "2026-08-23"
            / "first10_editorial.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=str(
            ROOT
            / "outputs"
            / "ben_first10_editorial"
            / "2026-08-23"
            / "first10_editorial_audit.json"
        ),
    )
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = audit(payload)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
