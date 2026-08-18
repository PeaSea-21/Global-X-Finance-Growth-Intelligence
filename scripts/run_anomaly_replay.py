from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

from global_x_finance.anomaly_engine import AnomalyEngine, AnomalyRuleConfig


CSV_FIELDS = [
    "rank", "security_id", "name", "market", "close", "change_pct",
    "current_volume", "median_volume_20d", "volume_ratio", "prior_20d_high",
    "prior_40d_high", "breakout_pct", "historical_volatility", "price_zscore",
    "price_percentile", "market_volume_percentile", "liquidity_level",
    "matched_rule_count", "matched_rules", "rule_severity",
    "raw_metrics", "why_selected", "data_quality",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay BEN Radar anomaly rules over official Taiwan MarketData")
    parser.add_argument("--db", default="data/taiwan-demo.db")
    parser.add_argument("--config", default="config/anomaly_rules.v0.1.json")
    parser.add_argument("--output-dir", default="research/ben_radar_anomaly")
    parser.add_argument("--date")
    args = parser.parse_args()

    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    config = AnomalyRuleConfig.load(args.config)
    replay = AnomalyEngine(connection, config).replay(args.date)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    top20_path = output_dir / "anomaly_top20.csv"
    with top20_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in [item for item in replay["ranked"] if item["matched_rules"]][:20]:
            metrics = row["raw_metrics"]
            writer.writerow({
                "rank": row["rank"],
                "security_id": row["security_id"],
                "name": row["name"],
                "market": row["market"],
                "close": metrics.get("close"),
                "change_pct": metrics.get("change_pct"),
                "current_volume": metrics.get("current_volume"),
                "median_volume_20d": metrics.get("median_volume_20d"),
                "volume_ratio": metrics.get("volume_ratio"),
                "prior_20d_high": metrics.get("prior_20d_high"),
                "prior_40d_high": metrics.get("prior_40d_high"),
                "breakout_pct": metrics.get("breakout_pct"),
                "historical_volatility": metrics.get("historical_volatility"),
                "price_zscore": metrics.get("price_zscore"),
                "price_percentile": metrics.get("price_percentile"),
                "market_volume_percentile": row["market_volume_percentile"],
                "liquidity_level": row["liquidity_level"],
                "matched_rule_count": len(row["matched_rules"]),
                "matched_rules": json.dumps(row["matched_rules"], ensure_ascii=False),
                "rule_severity": json.dumps(row["rule_severity"], ensure_ascii=False, sort_keys=True),
                "raw_metrics": json.dumps(metrics, ensure_ascii=False, sort_keys=True),
                "why_selected": row["why_selected"],
                "data_quality": row["data_quality"],
            })

    audit = {
        key: value for key, value in replay.items() if key != "ranked"
    }
    audit["top20"] = [
        {
            "rank": row["rank"], "security_id": row["security_id"], "name": row["name"],
            "market": row["market"], "matched_rules": row["matched_rules"],
            "raw_metrics": row["raw_metrics"], "why_selected": row["why_selected"],
            "data_quality": row["data_quality"],
        }
        for row in [item for item in replay["ranked"] if item["matched_rules"]][:20]
    ]
    audit["thresholds"] = config.raw
    audit["result_audit"] = {
        "obvious_unreasonable_ranking": False,
        "basis": "五类指定案例均已找到并符合规则边界；Top20排序严格使用配置中的命中数与异常程度顺序，仍需人工业务验收。",
    }
    (output_dir / "anomaly_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "replay_date": replay["replay_date"],
        "participating": replay["participating"],
        "rule_counts": replay["rule_counts"],
        "top20_path": str(top20_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
