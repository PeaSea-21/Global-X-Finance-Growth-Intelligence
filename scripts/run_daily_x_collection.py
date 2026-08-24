from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.db import apply_migrations, connect
from global_x_finance.x_intelligence import collect_x_accounts_once, load_x_accounts


TAIPEI = timezone(timedelta(hours=8))
COMPLETE_STATUSES = {"SUCCESS", "NO_NEW"}
RETRYABLE_STATUSES = {"FAILED", "RATE_LIMITED"}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect the configured X account pool once per day.")
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--accounts", default=str(ROOT / "config" / "x_accounts.csv"))
    parser.add_argument("--migrations", default=str(ROOT / "migrations"))
    parser.add_argument("--output-root", default=str(ROOT / "outputs" / "x_daily"))
    parser.add_argument("--max-rounds", type=int, default=2)
    parser.add_argument("--retry-seconds", type=int, default=45)
    args = parser.parse_args()
    if args.max_rounds < 1 or args.retry_seconds < 0:
        parser.error("max-rounds must be >= 1 and retry-seconds must be >= 0")

    started_at = datetime.now(TAIPEI)
    accounts = load_x_accounts(args.accounts)
    final_by_handle: dict[str, dict[str, Any]] = {}
    rounds: list[dict[str, Any]] = []
    pending = list(accounts)
    connection = connect(args.database)
    try:
        apply_migrations(connection, args.migrations)
        for round_number in range(1, args.max_rounds + 1):
            results = collect_x_accounts_once(
                connection,
                pending,
                force=True,
                include_low_confidence=True,
                reconcile_accounts=round_number == 1,
            )
            rows = [result.__dict__ for result in results]
            for row in rows:
                final_by_handle[row["handle"].lower()] = row
            rounds.append({
                "round": round_number,
                "account_count": len(pending),
                "results": rows,
            })
            failed_handles = {
                row["handle"].lower()
                for row in rows
                if row["status"] in RETRYABLE_STATUSES
            }
            pending = [account for account in accounts if account.handle.lower() in failed_handles]
            if not pending or round_number == args.max_rounds:
                break
            time.sleep(args.retry_seconds)
    finally:
        connection.close()

    final_rows = [
        final_by_handle.get(account.handle.lower(), {
            "handle": account.handle,
            "status": "FAILED",
            "error_reason": "collector returned no account result",
            "new_count": 0,
            "kept_count": 0,
            "fetched_count": 0,
        })
        for account in accounts
    ]
    complete_count = sum(row["status"] in COMPLETE_STATUSES for row in final_rows)
    finished_at = datetime.now(TAIPEI)
    unresolved = [row for row in final_rows if row["status"] not in COMPLETE_STATUSES]
    summary = {
        "run_id": started_at.strftime("%Y%m%dT%H%M%S%z"),
        "status": "PASS" if not unresolved else "DEGRADED",
        "adapter": "FXTWITTER_V2_READ_ONLY_THIRD_PARTY",
        "terms_status": "UNKNOWN",
        "commercial_use_status": "UNKNOWN",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "configured_accounts": len(accounts),
        "complete_accounts": complete_count,
        "completion_ratio": round(complete_count / len(accounts), 4) if accounts else 0.0,
        "new_posts": sum(int(row.get("new_count") or 0) for batch in rounds for row in batch["results"]),
        "kept_posts": sum(int(row.get("kept_count") or 0) for batch in rounds for row in batch["results"]),
        "unresolved": unresolved,
        "rounds": rounds,
    }
    day_root = Path(args.output_root) / started_at.date().isoformat()
    _write_json(day_root / f"run_{summary['run_id']}.json", summary)
    _write_json(day_root / "run_summary.json", summary)
    _write_json(Path(args.output_root) / "latest.json", summary)
    print(json.dumps({key: summary[key] for key in (
        "status", "started_at", "finished_at", "configured_accounts",
        "complete_accounts", "completion_ratio", "new_posts", "kept_posts",
    )}, ensure_ascii=False, indent=2))
    return 0 if not unresolved else 2


if __name__ == "__main__":
    raise SystemExit(main())
