from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.content_studio import write_content_studio_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the daily BEN content-studio payload.")
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument(
        "--brief",
        default=str(ROOT / "sites" / "ben-channel-review" / "brief.json"),
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "sites" / "ben-content-studio" / "data.json"),
    )
    parser.add_argument(
        "--close-talk-editorial",
        default="",
        help="Optional same-day close_talk_editorial.json; stale/missing files stay visibly unavailable.",
    )
    args = parser.parse_args()
    brief_payload = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    editorial_path = Path(args.close_talk_editorial) if args.close_talk_editorial else (
        ROOT / "outputs" / "ben_channel_daily" / str(brief_payload["market_session_date"]) / "close_talk_editorial.json"
    )
    payload = write_content_studio_payload(
        database_path=args.database,
        brief_path=args.brief,
        output_path=args.output,
        close_talk_editorial_path=editorial_path,
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "market_session_date": payload["market_session_date"],
                "weight_topic_count": len(payload["weight_topics"]),
                "output": str(Path(args.output).resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
