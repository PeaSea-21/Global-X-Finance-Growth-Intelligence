from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from flask import template_rendered

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from global_x_finance.webapp import create_app


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    items = []
    for item in event.get("items", []):
        items.append(
            {
                "id": str(item.get("id", "")),
                "kind": str(item.get("kind", "UNKNOWN")),
                "publisher": str(item.get("publisher", "UNKNOWN")),
                "publisher_group": str(item.get("publisher_group", "UNKNOWN")),
                "published_at": str(item.get("published_at", "UNKNOWN")),
                "text": str(item.get("text", "")),
                "url": str(item.get("url", "")),
                "market": str(item.get("market", "UNKNOWN")),
                "is_repost": bool(item.get("is_repost", False)),
            }
        )
    return {
        "event_id": str(event.get("event_id", "")),
        "title": str(event.get("display_title_zh", "中文摘要生成中")),
        "summary": str(event.get("summary_zh", "")),
        "score": int(event.get("score", 0)),
        "trend": str(event.get("trend", "SUSTAINED")),
        "acceleration_pct": event.get("acceleration_pct"),
        "independent_count": int(event.get("independent_count", 0)),
        "news_count": int(event.get("news_count", 0)),
        "x_count": int(event.get("x_count", 0)),
        "entities": [str(value) for value in event.get("entities", [])],
        "categories": [str(value) for value in event.get("categories", [])],
        "first_seen_at": str(event.get("first_seen_at", "UNKNOWN")),
        "latest_update_at": str(event.get("latest_update_at", "UNKNOWN")),
        "score_dimensions": dict(event.get("score_dimensions", {})),
        "market_response": list(event.get("market_response", [])),
        "content_formats": [str(value) for value in event.get("content_formats", [])],
        "recommended_angle": str(event.get("recommended_angle", "")),
        "why_watch": str(event.get("why_watch", "")),
        "questions": [str(value) for value in event.get("questions", [])],
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    app = create_app(args.db)
    captured: dict[str, Any] = {}

    def receive(_sender, template, context, **_extra):
        if template.name == "ai_market_radar.html":
            captured.update(context)

    template_rendered.connect(receive, app, weak=False)
    response = app.test_client().get("/stock-radar")
    if response.status_code != 200 or "events" not in captured:
        raise RuntimeError(f"Unable to render stock radar: HTTP {response.status_code}")

    payload = {
        "generated_at": str(captured.get("last_updated", "UNKNOWN")),
        "official_data_date": str(captured.get("official_data_date", "UNKNOWN")),
        "window": str(captured.get("window", "24")),
        "events_total": int(captured.get("events_total", 0)),
        "category_counts": dict(captured.get("category_counts", {})),
        "usable_source_count": int(captured.get("usable_source_count", 0)),
        "pool_count": int(captured.get("pool_count", 0)),
        "history_valid_count": int(captured.get("history_valid_count", 0)),
        "x_account_counts": dict(captured.get("x_account_counts", {})),
        "quality": dict(captured.get("quality", {})),
        "snapshot_metadata": dict(captured.get("snapshot_metadata", {})),
        "source_coverage": dict(captured.get("source_coverage", {})),
        "stock_workbench": dict(captured.get("stock_workbench", {})),
        "events": [_event_payload(event) for event in captured["events"]],
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(payload['events'])} events to {destination}")


if __name__ == "__main__":
    main()
