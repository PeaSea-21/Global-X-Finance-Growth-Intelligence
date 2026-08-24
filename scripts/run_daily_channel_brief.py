from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from audit_channel_briefs import audit_payload
from global_x_finance.ben_radar import collect_news_once
from global_x_finance.close_talk_sources import collect_close_talk_source_pack
from global_x_finance.channel_briefs import (
    TAIPEI,
    build_channel_briefs,
    channel_brief_markdown,
    load_channel_pilot_config,
    persist_channel_briefs,
)
from global_x_finance.db import apply_migrations, connect
from global_x_finance.market_history_backfill import MarketHistoryBackfillService
from global_x_finance.official_data import OfficialDataService, load_official_data_config


def _market_coverage(connection: Any, trade_date: str) -> dict[str, dict[str, Any]]:
    totals = {
        row["exchange_code"]: int(row["count"])
        for row in connection.execute(
            """SELECT exchange_code, COUNT(*) AS count FROM official_securities
               WHERE exchange_code IN ('TWSE','TPEX') GROUP BY exchange_code"""
        )
    }
    counts = {
        row["exchange_code"]: int(row["count"])
        for row in connection.execute(
            """SELECT exchange_code, COUNT(*) AS count FROM official_market_data_daily
               WHERE trade_date=? AND data_status='EOD' GROUP BY exchange_code""",
            (trade_date,),
        )
    }
    return {
        market: {
            "records": counts.get(market, 0),
            "securities": totals.get(market, 0),
            "ratio": counts.get(market, 0) / totals[market] if totals.get(market) else 0.0,
        }
        for market in ("TWSE", "TPEX")
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Taiwan post-close BEN channel job.")
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--config", default=str(ROOT / "config" / "channel_pilots.v0.1.json"))
    parser.add_argument("--anomaly-config", default=str(ROOT / "config" / "anomaly_rules.v0.1.json"))
    parser.add_argument("--official-config", default=str(ROOT / "config" / "official_data.sources.json"))
    parser.add_argument("--migrations", default=str(ROOT / "migrations"))
    parser.add_argument("--status", default=str(ROOT / "research" / "ben_radar_market_history" / "backfill_status.json"))
    parser.add_argument("--output-root", default=str(ROOT / "outputs" / "ben_channel_daily"))
    parser.add_argument("--review-json", help="Optional local review-site brief.json to refresh after a passing audit")
    parser.add_argument("--date", help="Taiwan market session date; defaults to today's Taipei date")
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--retry-seconds", type=int, default=300)
    parser.add_argument("--optional-attempts", type=int, default=2)
    parser.add_argument("--optional-retry-seconds", type=int, default=10)
    parser.add_argument("--skip-news", action="store_true")
    parser.add_argument("--allow-before-build-time", action="store_true")
    args = parser.parse_args()

    if (
        args.max_attempts < 1
        or args.retry_seconds < 0
        or args.optional_attempts < 1
        or args.optional_retry_seconds < 0
    ):
        parser.error("attempt counts must be >= 1 and retry seconds must be >= 0")

    now = datetime.now(TAIPEI)
    trade_date = date.fromisoformat(args.date) if args.date else now.date()
    if trade_date > now.date():
        parser.error("date cannot be in the future")

    channel_config, _ = load_channel_pilot_config(args.config)
    build_hour, build_minute = (
        int(part) for part in channel_config["primary_build_time"].split(":", 1)
    )
    scheduled = datetime(
        trade_date.year,
        trade_date.month,
        trade_date.day,
        build_hour,
        build_minute,
        tzinfo=TAIPEI,
    )
    if (
        trade_date == now.date()
        and now < scheduled
        and not args.allow_before_build_time
    ):
        print(json.dumps({
            "status": "WAITING_FOR_BUILD_TIME",
            "market_session_date": trade_date.isoformat(),
            "scheduled_for": scheduled.isoformat(),
            "checked_at": now.isoformat(),
        }, ensure_ascii=False, indent=2))
        return 3

    connection = connect(args.database)
    try:
        apply_migrations(connection, args.migrations)
        official_config = load_official_data_config(args.official_config)
        official_service = OfficialDataService(connection, official_config, now=now)
        official_sync_attempts = []
        for attempt in range(1, args.optional_attempts + 1):
            official_sync = official_service.sync_disclosures().as_dict()
            official_sync_attempts.append({"attempt": attempt, **official_sync})
            if official_sync["status"] == "PASS":
                break
            if attempt < args.optional_attempts:
                time.sleep(args.optional_retry_seconds)
        minimum_coverage = float(channel_config["minimum_market_coverage"])
        attempts: list[dict[str, Any]] = []
        service = MarketHistoryBackfillService(
            connection,
            official_config,
            status_path=args.status,
            target_days=20,
            minimum_days=20,
            now=now,
        )
        for attempt in range(1, args.max_attempts + 1):
            coverage = _market_coverage(connection, trade_date.isoformat())
            pending = [
                market for market, row in coverage.items()
                if row["ratio"] < minimum_coverage
            ]
            results = []
            for market in pending:
                result = service.collect_market_date(market, trade_date)
                results.append({
                    "market": market,
                    "status": result.status,
                    "fetched_count": result.fetched_count,
                    "stored_count": result.stored_count,
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                })
            coverage = _market_coverage(connection, trade_date.isoformat())
            attempts.append({"attempt": attempt, "coverage": coverage, "results": results})
            if all(row["ratio"] >= minimum_coverage for row in coverage.values()):
                service.refresh_history_status()
                break
            if attempt < args.max_attempts:
                time.sleep(args.retry_seconds)

        coverage = _market_coverage(connection, trade_date.isoformat())
        if any(row["ratio"] < minimum_coverage for row in coverage.values()):
            summary = {
                "status": "SOURCE_PENDING_OR_NO_SESSION",
                "market_session_date": trade_date.isoformat(),
                "checked_at": datetime.now(TAIPEI).isoformat(),
                "attempts": attempts,
            }
            _write_json(Path(args.output_root) / trade_date.isoformat() / "run_summary.json", summary)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 2

        news_attempts = []
        news_results = []
        if not args.skip_news:
            for attempt in range(1, args.optional_attempts + 1):
                news_results = list(collect_news_once(connection))
                news_attempts.append({"attempt": attempt, "results": news_results})
                if all(row["status"] == "SUCCESS" for row in news_results):
                    break
                if attempt < args.optional_attempts:
                    time.sleep(args.optional_retry_seconds)
        generated_at = datetime.now(TAIPEI)
        close_talk_source_pack = collect_close_talk_source_pack(
            connection, trade_date.isoformat(), now=generated_at
        )
        payload = build_channel_briefs(
            connection,
            config_path=args.config,
            anomaly_config_path=args.anomaly_config,
            replay_date=trade_date.isoformat(),
            generated_at=generated_at,
        )
        payload, persisted_new = persist_channel_briefs(
            connection, payload, config_path=args.config
        )
        audit, violations = audit_payload(payload)
        day_output = Path(args.output_root) / trade_date.isoformat()
        _write_json(day_output / "channel_brief.json", payload)
        (day_output / "channel_brief.md").write_text(
            channel_brief_markdown(payload), encoding="utf-8"
        )
        _write_json(day_output / "audit.json", {"audit": audit, "violations": violations})
        _write_json(day_output / "close_talk_source_pack.json", close_talk_source_pack)
        summary = {
            "status": "PASS" if not violations else "AUDIT_FAILED",
            "market_session_date": trade_date.isoformat(),
            "generated_at": payload["generated_at"],
            "data_as_of": payload["data_as_of"],
            "replay_mode": payload["replay_mode"],
            "persisted_new": persisted_new,
            "official_sync": official_sync,
            "official_sync_attempts": official_sync_attempts,
            "market_coverage": coverage,
            "news_results": news_results,
            "news_attempts": news_attempts,
            "close_talk_source_pack": {
                "status": close_talk_source_pack["status"],
                "base_status": close_talk_source_pack.get("base_status"),
                "enhancement_status": close_talk_source_pack.get("enhancement_status"),
                "generation_stage": close_talk_source_pack.get("generation_stage"),
                "coverage_status": close_talk_source_pack["coverage_status"],
                "missing_datasets": close_talk_source_pack["missing_datasets"],
                "path": str(day_output / "close_talk_source_pack.json"),
            },
            "ranking_method": payload["ranking_method"],
            "channels": [
                {
                    "channel": brief["channel_name"],
                    "status": brief["status"],
                    "top_count": min(brief["target_count"], len(brief["assignments"])),
                }
                for brief in payload["briefs"]
            ],
            "violation_count": len(violations),
        }
        _write_json(day_output / "run_summary.json", summary)
        if args.review_json and not violations:
            _write_json(Path(args.review_json), payload)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if not violations else 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
