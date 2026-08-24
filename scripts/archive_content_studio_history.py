from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.content_studio import archive_workbench_channels


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive current visible BEN channel versions before a daily refresh."
    )
    parser.add_argument(
        "--site-data",
        default=str(ROOT / "sites" / "ben-content-studio" / "data.json"),
    )
    args = parser.parse_args()
    site_path = Path(args.site_data)
    payload = json.loads(site_path.read_text(encoding="utf-8"))
    workbench = payload.get("channel_workbench")
    if not isinstance(workbench, dict):
        raise ValueError("channel_workbench is missing")
    before = len(workbench.get("channel_history_index") or [])
    payload["channel_workbench"] = archive_workbench_channels(
        workbench,
        site_path.parent,
    )
    after = len(payload["channel_workbench"].get("channel_history_index") or [])
    site_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "history_entry_count": after,
                "new_history_entries": after - before,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
