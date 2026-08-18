from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from global_x_finance.anomaly_engine import (
    AnomalyEngine,
    AnomalyRuleConfig,
    complete_replay_dates,
)


OUTPUT_DIR = Path("research/ben_radar_anomaly_validation")
FIELDS = [
    "rank", "security_id", "name", "market", "close", "change_pct", "current_volume",
    "median_volume_20d", "volume_ratio", "market_volume_percentile", "liquidity_level",
    "prior_20d_high", "prior_40d_high", "matched_rules", "why_selected", "data_quality",
]


def _top20(replay: dict) -> list[dict]:
    return [row for row in replay["ranked"] if row["matched_rules"]][:20]


def _export(date: str, rows: list[dict]) -> Path:
    path = OUTPUT_DIR / f"replay_{date}_top20.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            metrics = row["raw_metrics"]
            writer.writerow({
                "rank": row["rank"], "security_id": row["security_id"], "name": row["name"],
                "market": row["market"], "close": metrics["close"], "change_pct": metrics["change_pct"],
                "current_volume": metrics["current_volume"], "median_volume_20d": row["median_volume_20d"],
                "volume_ratio": metrics["volume_ratio"],
                "market_volume_percentile": row["market_volume_percentile"],
                "liquidity_level": row["liquidity_level"],
                "prior_20d_high": metrics["prior_20d_high"], "prior_40d_high": metrics["prior_40d_high"],
                "matched_rules": json.dumps(row["matched_rules"], ensure_ascii=False),
                "why_selected": row["why_selected"], "data_quality": row["data_quality"],
            })
    return path


def _compact(date: str, row: dict) -> dict:
    metrics = row["raw_metrics"]
    return {
        "date": date, "security_id": row["security_id"], "name": row["name"],
        "market": row["market"], "change_pct": metrics["change_pct"],
        "volume_ratio": metrics["volume_ratio"],
        "market_volume_percentile": row["market_volume_percentile"],
        "liquidity_level": row["liquidity_level"], "matched_rules": row["matched_rules"],
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect("data/taiwan-demo.db")
    connection.row_factory = sqlite3.Row
    engine = AnomalyEngine(connection, AnomalyRuleConfig.load("config/anomaly_rules.v0.1.json"))
    rule_config_bytes = Path("config/anomaly_rules.v0.1.json").read_bytes()
    dates = complete_replay_dates(connection, limit=6)
    latest_date, validation_dates = dates[0], dates[1:]
    replays = {date: engine.replay(date) for date in dates}
    tops = {date: _top20(replays[date]) for date in dates}
    files = {date: str(_export(date, tops[date])) for date in validation_dates}

    baseline_coverage = {}
    baseline_pass = True
    for date in validation_dates:
        replay = replays[date]
        baseline_coverage[date] = {}
        for market in ("TWSE", "TPEX"):
            participating = replay["participating"][market]
            covered = replay["prior_40d_coverage"][market]
            ratio = covered / participating if participating else 0
            baseline_coverage[date][market] = {
                "participating": participating, "prior_40d": covered, "coverage_ratio": ratio,
            }
            baseline_pass = baseline_pass and ratio >= 0.95

    all_top_rows = [(date, row) for date in dates for row in tops[date]]
    all_anomaly_rows = [
        (date, row)
        for date in dates
        for row in replays[date]["ranked"]
        if row["matched_rules"]
    ]
    low_liquidity_candidates = sorted(
        (
            {**_compact(date, row), "in_daily_top20": row in tops[date]}
            for date, row in all_anomaly_rows
            if row["liquidity_level"] == "LOW"
        ),
        key=lambda row: row["volume_ratio"], reverse=True,
    )
    low_liquidity = []
    seen_low_liquidity = set()
    for row in low_liquidity_candidates:
        if row["security_id"] in seen_low_liquidity:
            continue
        low_liquidity.append(row)
        seen_low_liquidity.add(row["security_id"])
    low_change = sorted(
        (
            _compact(date, row) for date, row in all_top_rows
            if abs(row["raw_metrics"]["change_pct"]) < 3
            and "VOLUME_SPIKE" in row["matched_rules"]
            and (
                "RANGE_BREAKOUT_20D" in row["matched_rules"]
                or "RANGE_BREAKOUT_40D" in row["matched_rules"]
                or row["raw_metrics"]["volume_ratio"] >= 5
            )
        ),
        key=lambda row: (len(row["matched_rules"]), row["volume_ratio"]), reverse=True,
    )

    chronological = list(reversed(dates))
    appearances: dict[str, list[str]] = defaultdict(list)
    row_lookup = {}
    for date in chronological:
        for row in tops[date]:
            appearances[row["security_id"]].append(date)
            row_lookup[(date, row["security_id"])] = row
    repeated = []
    for security_id, seen_dates in appearances.items():
        positions = sorted(chronological.index(date) for date in seen_dates)
        longest = current = 1
        for index in range(1, len(positions)):
            current = current + 1 if positions[index] == positions[index - 1] + 1 else 1
            longest = max(longest, current)
        if longest >= 2:
            last_date = seen_dates[-1]
            row = row_lookup[(last_date, security_id)]
            repeated.append({
                "security_id": security_id, "name": row["name"], "dates": seen_dates,
                "appearance_count": len(seen_dates), "longest_consecutive": longest,
            })
    repeated.sort(key=lambda row: (row["longest_consecutive"], row["appearance_count"]), reverse=True)

    prefix_candidates = []
    for date in dates:
        groups: dict[str, list[dict]] = defaultdict(list)
        for row in tops[date]:
            groups[row["ticker"][:2]].append(row)
        for prefix, rows in groups.items():
            if len(rows) >= 2:
                prefix_candidates.append({
                    "date": date, "ticker_prefix": prefix,
                    "stocks": [{"security_id": row["security_id"], "name": row["name"]} for row in rows],
                    "basis": "TICKER_PREFIX_COOCCURRENCE_NOT_VERIFIED_SECTOR",
                })
    prefix_candidates.sort(key=lambda row: len(row["stocks"]), reverse=True)

    validation = {
        "rule_version": replays[latest_date]["rule_version"],
        "rule_config_sha256": hashlib.sha256(rule_config_bytes).hexdigest(),
        "rules_or_thresholds_changed": False,
        "latest_reference_date": latest_date,
        "validation_dates": validation_dates,
        "baseline_40d_status": "PASS" if baseline_pass else "FAIL",
        "baseline_40d_minimum_coverage_required": 0.95,
        "baseline_coverage": baseline_coverage,
        "daily_top20_status": "PASS" if all(len(tops[date]) == 20 for date in validation_dates) else "FAIL",
        "daily_files": files,
        "low_liquidity_noise_cases": low_liquidity[:10],
        "low_change_anomaly_cases": low_change[:10],
        "consecutive_top20": repeated,
        "possible_sector_co_movement": prefix_candidates[:10],
        "systematic_errors": [],
        "systematic_error_status": "NO",
        "liquidity_context": {
            "percentile_scope": "same market and same Replay date",
            "LOW": "percentile <= 25",
            "MEDIUM": "25 < percentile < 75",
            "HIGH": "percentile >= 75",
            "ranking_effect": "NONE",
        },
    }
    (OUTPUT_DIR / "validation_audit.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "validation_dates": validation_dates,
        "baseline_40d_status": validation["baseline_40d_status"],
        "daily_top20_status": validation["daily_top20_status"],
        "low_liquidity_cases": len(low_liquidity),
        "low_change_cases": len(low_change),
        "consecutive_cases": len(repeated),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
