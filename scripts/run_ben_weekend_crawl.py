from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.ben_radar import collect_news_once
from global_x_finance.db import apply_migrations, connect
from global_x_finance.weekend_crawl import (
    TAIPEI,
    build_weekend_snapshot,
    load_x_input_status,
    select_recent_news,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect a Sunday 24h/48h BEN source snapshot without pretending it is a post-close brief."
    )
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--migrations", default=str(ROOT / "migrations"))
    parser.add_argument("--output-root", default=str(ROOT / "outputs" / "ben_weekend_crawl"))
    parser.add_argument("--x-output-root", default=str(ROOT / "outputs" / "x_daily"))
    parser.add_argument("--label", choices=("primary", "enrichment"), default="primary")
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--retry-seconds", type=int, default=15)
    parser.add_argument("--allow-non-sunday", action="store_true")
    args = parser.parse_args()
    if args.attempts < 1 or args.retry_seconds < 0:
        parser.error("attempts must be >= 1 and retry-seconds must be >= 0")

    now = datetime.now(TAIPEI)
    if now.weekday() != 6 and not args.allow_non_sunday:
        print(json.dumps({
            "status": "NOT_SUNDAY",
            "checked_at": now.isoformat(),
            "reason": "This source-only job is reserved for Sunday; weekday post-close jobs are separate.",
        }, ensure_ascii=False, indent=2))
        return 3

    connection = connect(args.database)
    try:
        apply_migrations(connection, args.migrations)
        attempts: list[dict[str, object]] = []
        news_results: list[dict[str, object]] = []
        for attempt in range(1, args.attempts + 1):
            news_results = list(collect_news_once(connection))
            attempts.append({"attempt": attempt, "results": news_results})
            if all(row.get("status") == "SUCCESS" for row in news_results):
                break
            if attempt < args.attempts:
                time.sleep(args.retry_seconds)
        generated_at = datetime.now(TAIPEI)
        news_items = select_recent_news(connection, as_of=generated_at)
    finally:
        connection.close()

    run_date = generated_at.date().isoformat()
    x_status = load_x_input_status(args.x_output_root, run_date)
    snapshot = build_weekend_snapshot(
        as_of=generated_at,
        label=args.label,
        news_results=news_results,
        news_items=news_items,
        x_status=x_status,
    )
    snapshot["news_attempts"] = attempts
    day_output = Path(args.output_root) / run_date
    day_output.mkdir(parents=True, exist_ok=True)
    destination = day_output / f"crawl_{args.label}.json"
    destination.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    (day_output / "latest.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = {
        "status": snapshot["status"],
        "snapshot_date": run_date,
        "label": args.label,
        "fresh_24h_count": snapshot["fresh_24h_count"],
        "context_24h_to_48h_count": snapshot["context_24h_to_48h_count"],
        "news_source_success_count": snapshot["news_source_success_count"],
        "news_source_count": snapshot["news_source_count"],
        "x_status": snapshot["x_input"]["status"],
        "output": str(destination),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if snapshot["status"] in {"NEWS_CRAWL_PASS", "NEWS_CRAWL_DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
