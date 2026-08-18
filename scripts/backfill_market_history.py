from __future__ import annotations

import argparse
import json

from global_x_finance.db import apply_migrations, connect
from global_x_finance.market_history_backfill import run_market_history_backfill
from global_x_finance.official_data import load_official_data_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill official TWSE/TPEx daily OHLCV")
    parser.add_argument("--db", default="data/taiwan-demo.db")
    parser.add_argument("--config", default="config/official_data.sources.json")
    parser.add_argument("--migrations", default="migrations")
    parser.add_argument(
        "--status",
        default="research/ben_radar_market_history/backfill_status.json",
    )
    parser.add_argument("--target-days", type=int, default=40)
    parser.add_argument("--minimum-days", type=int, default=20)
    args = parser.parse_args()

    connection = connect(args.db)
    try:
        apply_migrations(connection, args.migrations)
        result = run_market_history_backfill(
            connection,
            load_official_data_config(args.config),
            status_path=args.status,
            target_days=args.target_days,
            minimum_days=args.minimum_days,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        connection.close()
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
