from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from global_x_finance.db import apply_migrations, connect
from global_x_finance.industry_mapping_sync import IndustryMappingSyncService


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync official TWSE/TPEx industry codes for BEN candidate recall."
    )
    parser.add_argument("--database", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--migrations", default=str(ROOT / "migrations"))
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()

    connection = connect(args.database)
    try:
        applied = apply_migrations(connection, args.migrations)
        result = IndustryMappingSyncService(connection, timeout=args.timeout).sync()
    finally:
        connection.close()
    print(json.dumps({"applied_migrations": applied, **result.to_dict()}, ensure_ascii=False, indent=2))
    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
