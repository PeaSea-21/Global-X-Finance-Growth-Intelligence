from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACK_PATH = ROOT / "style_packs_v0.1.json"
INVENTORY_PATH = ROOT / "sample_inventory.csv"
REPORT_PATH = ROOT / "validation_report.json"


def validate() -> dict[str, object]:
    payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    with INVENTORY_PATH.open(encoding="utf-8", newline="") as handle:
        inventory = list(csv.DictReader(handle))

    violations: list[str] = []
    channels = payload.get("channels", [])
    if len(channels) != 10:
        violations.append(f"expected 10 channels, found {len(channels)}")

    orders = [row.get("channel_order") for row in channels]
    if orders != list(range(1, 11)):
        violations.append(f"channel_order is not 1..10: {orders}")

    ids = [str(row.get("channel_id") or "") for row in channels]
    if len(ids) != len(set(ids)):
        violations.append("channel_id values are not unique")

    transcript_rows = [row for row in inventory if row["sample_id"] != "NO_SAMPLE"]
    inventory_counts = Counter(row["channel_id"] for row in transcript_rows)
    for channel in channels:
        channel_id = channel["channel_id"]
        expected = inventory_counts.get(channel_id, 0)
        if channel.get("sample_count") != expected:
            violations.append(
                f"{channel_id} sample_count={channel.get('sample_count')} inventory={expected}"
            )
        if expected == 0:
            if channel.get("status") != "NO_TRANSCRIPT_NEEDS_SAMPLES":
                violations.append(f"{channel_id} missing NO_TRANSCRIPT status")
            for field in ("language_style", "opening_hook", "ending_pattern"):
                if channel.get(field) != "UNKNOWN_NO_TRANSCRIPT":
                    violations.append(f"{channel_id} inferred {field} without transcript")
        else:
            required = (
                "language_style",
                "title_formulas",
                "opening_hook",
                "narrative_logic",
                "script_structure",
                "fact_opinion_balance",
                "required_fact_fields",
                "ending_pattern",
                "profile_sample_alignment",
                "promotion_exclusions",
            )
            for field in required:
                if not channel.get(field):
                    violations.append(f"{channel_id} missing {field}")

    global_contract = payload.get("global_contract", {})
    if global_contract.get("fresh_event_window_hours") != 24:
        violations.append("fresh_event_window_hours must be 24")
    if global_contract.get("context_window_hours") != 48:
        violations.append("context_window_hours must be 48")
    if global_contract.get("crawl_days") != ["MO", "TU", "WE", "TH", "FR", "SU"]:
        violations.append("crawl_days must be Monday-Friday plus Sunday")
    if global_contract.get("source_card_contract", {}).get("raw_api_only_is_acceptable") is not False:
        violations.append("raw API-only Ben-facing sources must be rejected")

    report = {
        "artifact": "BEN_FIRST10_STYLE_PACK_VALIDATION",
        "status": "PASS" if not violations else "FAIL",
        "channel_count": len(channels),
        "channels_with_transcripts": sum(1 for row in channels if row.get("sample_count", 0) > 0),
        "channels_without_transcripts": sum(1 for row in channels if row.get("sample_count", 0) == 0),
        "transcript_sample_count": len(transcript_rows),
        "inventory_row_count": len(inventory),
        "violations": violations,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
