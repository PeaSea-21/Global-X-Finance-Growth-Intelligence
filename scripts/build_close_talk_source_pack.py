from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.close_talk_sources import collect_close_talk_source_pack
from global_x_finance.db import connect


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect the 收盤夜話 cash-market source pack.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    connection = connect(args.database)
    try:
        payload = collect_close_talk_source_pack(connection, args.date)
    finally:
        connection.close()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "coverage_status": payload["coverage_status"],
        "market_session_date": payload["market_session_date"],
        "missing_datasets": payload["missing_datasets"],
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
