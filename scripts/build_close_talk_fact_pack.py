from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.close_talk_fact_pack import build_close_talk_fact_pack
from global_x_finance.db import connect


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the bounded 收盤夜話 FactPack.")
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--channel-brief", required=True)
    parser.add_argument("--source-pack", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    channel_brief = json.loads(Path(args.channel_brief).read_text(encoding="utf-8"))
    source_pack = json.loads(Path(args.source_pack).read_text(encoding="utf-8"))
    connection = connect(args.database)
    try:
        payload = build_close_talk_fact_pack(
            connection, channel_brief=channel_brief, source_pack=source_pack
        )
    finally:
        connection.close()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "market_session_date": payload["market_session_date"],
        "data_as_of": payload["data_as_of"],
        "coverage": payload["coverage"],
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
