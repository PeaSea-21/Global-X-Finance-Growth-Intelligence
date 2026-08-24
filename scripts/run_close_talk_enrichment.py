from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.ben_radar import collect_news_once
from global_x_finance.close_talk_sources import collect_close_talk_source_pack
from global_x_finance.db import apply_migrations, connect

TAIPEI = timezone(timedelta(hours=8))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retry late 收盤夜話 official sources and perform the second 48-hour search."
    )
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--migrations", default=str(ROOT / "migrations"))
    parser.add_argument("--output-root", default=str(ROOT / "outputs" / "ben_channel_daily"))
    parser.add_argument("--date", help="Taiwan session date; defaults to today's Taipei date")
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--retry-seconds", type=int, default=15)
    args = parser.parse_args()
    if args.attempts < 1 or args.retry_seconds < 0:
        parser.error("attempts must be >= 1 and retry-seconds must be >= 0")

    now = datetime.now(TAIPEI)
    trade_date = date.fromisoformat(args.date) if args.date else now.date()
    day_output = Path(args.output_root) / trade_date.isoformat()
    day_output.mkdir(parents=True, exist_ok=True)
    connection = connect(args.database)
    try:
        apply_migrations(connection, args.migrations)
        news_attempts = []
        news_results = []
        for attempt in range(1, args.attempts + 1):
            news_results = list(collect_news_once(connection))
            news_attempts.append({"attempt": attempt, "results": news_results})
            if any(row.get("status") == "SUCCESS" for row in news_results):
                break
            if attempt < args.attempts:
                time.sleep(args.retry_seconds)
        source_pack = collect_close_talk_source_pack(
            connection, trade_date.isoformat(), now=datetime.now(TAIPEI)
        )
    finally:
        connection.close()

    source_path = day_output / "close_talk_source_pack.json"
    source_path.write_text(json.dumps(source_pack, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "status": "ENHANCEMENT_READY" if source_pack.get("enhancement_status") == "READY" else "ENHANCEMENT_PENDING",
        "market_session_date": trade_date.isoformat(),
        "checked_at": datetime.now(TAIPEI).isoformat(),
        "news_window_hours": 48,
        "news_attempts": news_attempts,
        "source_pack": {
            "base_status": source_pack.get("base_status"),
            "enhancement_status": source_pack.get("enhancement_status"),
            "coverage_status": source_pack.get("coverage_status"),
            "missing_datasets": source_pack.get("missing_datasets", []),
            "path": str(source_path),
        },
        "next_step": (
            "Regenerate FactPack and editorial as ENRICHED_DRAFT, preserving the earlier BASE_DRAFT."
            if source_pack.get("enhancement_status") == "READY"
            else "Keep the existing BASE_DRAFT and show missing late sources as UNKNOWN."
        ),
    }
    (day_output / "enrichment_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "ENHANCEMENT_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
