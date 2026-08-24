from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_CHANNELS = (
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
    "宏觀天秤",
    "地緣炸藥庫",
    "週期航海家",
    "半導體駭客",
    "華爾街溫度計",
    "定投實驗室",
}


def validate() -> dict[str, object]:
    payload = json.loads((ROOT / "style_packs_v0.1.json").read_text(encoding="utf-8"))
    with (ROOT / "sample_inventory.csv").open(encoding="utf-8", newline="") as handle:
        inventory = list(csv.DictReader(handle))

    violations: list[str] = []
    channels = list(payload.get("channels") or [])
    names = [row.get("channel_name") for row in channels]
    if tuple(names) != EXPECTED_CHANNELS:
        violations.append(f"channel order mismatch: {names}")
    if [row.get("channel_order") for row in channels] != list(range(11, 21)):
        violations.append("channel order values must be 11 through 20")
    transcript_rows = [row for row in inventory if row["text_status"] == "COMPLETE_TRANSCRIPT"]
    if len(transcript_rows) != 7:
        violations.append(f"expected 7 transcript rows, got {len(transcript_rows)}")
    by_name = {row["channel_name"]: row for row in channels}
    for name in EXPECTED_CHANNELS:
        row = by_name.get(name) or {}
        if name in WAITING_CHANNELS:
            if row.get("status") != "NO_TRANSCRIPT_NEEDS_SAMPLES":
                violations.append(f"{name}: missing-sample status is incorrect")
            if row.get("sample_count") != 0:
                violations.append(f"{name}: sample count must be zero")
        else:
            if not str(row.get("status") or "").startswith("PROVISIONAL"):
                violations.append(f"{name}: transcript-backed status must be provisional")
            if int(row.get("sample_count") or 0) < 1:
                violations.append(f"{name}: transcript-backed channel has no samples")
        for field in ("profile_promise", "audience", "profile_sample_alignment", "upgrade_requirement"):
            if not row.get(field):
                violations.append(f"{name}: missing {field}")

    summary = payload.get("corpus_summary") or {}
    if summary.get("channel_count") != 10:
        violations.append("corpus channel_count must be 10")
    if summary.get("channels_with_transcripts") != 4:
        violations.append("channels_with_transcripts must be 4")
    if summary.get("channels_without_transcripts") != 6:
        violations.append("channels_without_transcripts must be 6")
    if summary.get("transcript_sample_count") != 7:
        violations.append("transcript_sample_count must be 7")

    return {
        "status": "PASS" if not violations else "FAIL",
        "channel_count": len(channels),
        "channels_with_transcripts": sum(name not in WAITING_CHANNELS for name in names),
        "channels_without_transcripts": sum(name in WAITING_CHANNELS for name in names),
        "transcript_sample_count": len(transcript_rows),
        "violation_count": len(violations),
        "violations": violations,
    }


if __name__ == "__main__":
    report = validate()
    (ROOT / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
