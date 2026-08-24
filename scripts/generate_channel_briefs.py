from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.channel_briefs import (
    build_channel_briefs,
    channel_brief_markdown,
    persist_channel_briefs,
)
from global_x_finance.db import apply_migrations, connect


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate BEN P06B channel briefs.")
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--config", default=str(ROOT / "config" / "channel_pilots.v0.1.json"))
    parser.add_argument("--anomaly-config", default=str(ROOT / "config" / "anomaly_rules.v0.1.json"))
    parser.add_argument("--migrations", default=str(ROOT / "migrations"))
    parser.add_argument("--replay-date")
    parser.add_argument("--generated-at", help="ISO-8601 timestamp; defaults to now")
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    generated_at = datetime.fromisoformat(args.generated_at) if args.generated_at else None
    connection = connect(args.database)
    try:
        apply_migrations(connection, args.migrations)
        payload = build_channel_briefs(
            connection,
            config_path=args.config,
            anomaly_config_path=args.anomaly_config,
            replay_date=args.replay_date,
            generated_at=generated_at,
        )
        created = False
        if args.persist:
            payload, created = persist_channel_briefs(
                connection, payload, config_path=args.config
            )
    finally:
        connection.close()

    if args.output_dir:
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        stem = f"channel_brief_{payload['market_session_date']}"
        (output / f"{stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output / f"{stem}.md").write_text(
            channel_brief_markdown(payload), encoding="utf-8"
        )
    summary = {
        "market_session_date": payload["market_session_date"],
        "session_state": payload["session_state"],
        "ranking_method": payload["ranking_method"],
        "persisted_new": created,
        "channels": [
            {
                "channel": row["channel_name"],
                "status": row["status"],
                "qualified_count": row["qualified_count"],
                "displayed_count": row["displayed_count"],
            }
            for row in payload["briefs"]
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if payload["session_state"] in {"READY", "DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
