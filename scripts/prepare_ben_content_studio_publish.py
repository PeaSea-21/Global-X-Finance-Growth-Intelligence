from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from audit_all20_content_studio import audit as audit_all20
from global_x_finance.content_studio import write_content_studio_payload


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"required file is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare and audit the dated BEN content studio before publication."
    )
    parser.add_argument(
        "--trade-date",
        default=datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat(),
    )
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument(
        "--brief",
        default=str(ROOT / "sites" / "ben-channel-review" / "brief.json"),
    )
    parser.add_argument(
        "--site-data",
        default=str(ROOT / "sites" / "ben-content-studio" / "data.json"),
    )
    args = parser.parse_args()

    trade_date = args.trade_date
    day_root = ROOT / "outputs" / "ben_channel_daily" / trade_date
    editorial_path = day_root / "close_talk_editorial.json"
    editorial_audit_path = day_root / "close_talk_editorial_audit.json"
    editorial = _read_json(editorial_path)
    editorial_audit = _read_json(editorial_audit_path)
    if editorial.get("market_session_date") != trade_date:
        raise ValueError("close-talk editorial date mismatch")
    if editorial_audit.get("status") != "PASS":
        raise ValueError("close-talk editorial audit did not pass")
    if int(editorial_audit.get("violation_count", -1)) != 0:
        raise ValueError("close-talk editorial audit has violations")

    site_payload = write_content_studio_payload(
        database_path=args.database,
        brief_path=args.brief,
        output_path=args.site_data,
        close_talk_editorial_path=editorial_path,
    )
    workbench = site_payload.get("channel_workbench")
    if not isinstance(workbench, dict):
        raise ValueError("all-20 channel workbench is missing")
    if workbench.get("last_market_session_date") != trade_date:
        raise ValueError("workbench did not accept the current close-talk session")

    source_snapshot_date = str(workbench.get("source_snapshot_date") or "")
    if not source_snapshot_date:
        raise ValueError("workbench source snapshot date is missing")
    output_root = ROOT / "outputs" / "ben_all20_editorial" / source_snapshot_date
    workbench_path = output_root / "all20_editorial.json"
    audit_path = output_root / "all20_editorial_audit.json"
    output_root.mkdir(parents=True, exist_ok=True)
    workbench_path.write_text(
        json.dumps(workbench, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = audit_all20(workbench)
    report["input_sha256"] = _fingerprint(workbench)
    audit_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    result = {
        "status": report["status"],
        "trade_date": trade_date,
        "source_snapshot_date": source_snapshot_date,
        "topic_count": report["topic_count"],
        "full_script_count": report["full_script_count"],
        "violation_count": report["violation_count"],
        "site_data": str(Path(args.site_data).resolve()),
        "workbench": str(workbench_path.resolve()),
        "audit": str(audit_path.resolve()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
