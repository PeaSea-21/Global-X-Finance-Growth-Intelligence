from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from global_x_finance.ben_radar import NEWS_SOURCES


TAIPEI = timezone(timedelta(hours=8))
NEWS_SOURCE_BY_KEY = {str(source["key"]): source for source in NEWS_SOURCES}


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def select_recent_news(
    connection: sqlite3.Connection,
    *,
    as_of: datetime,
    context_hours: int = 48,
    fresh_hours: int = 24,
    limit: int = 400,
) -> list[dict[str, Any]]:
    """Return human-verifiable news rows for a Sunday candidate snapshot."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    if not 0 < fresh_hours <= context_hours:
        raise ValueError("fresh_hours must be positive and no greater than context_hours")

    cutoff = as_of.astimezone(timezone.utc) - timedelta(hours=context_hours)
    columns = {
        str(row["name"] if isinstance(row, sqlite3.Row) else row[1])
        for row in connection.execute("PRAGMA table_info(ben_news_items)")
    }
    fetched_at_sql = "fetched_at" if "fetched_at" in columns else "NULL AS fetched_at"
    rows = connection.execute(
        f"""
        SELECT source_key, source_name, original_title, published_at, {fetched_at_sql},
               original_url, public_summary, market, language
          FROM ben_news_items
         ORDER BY published_at DESC, id DESC
        """
    ).fetchall()
    output: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for row in rows:
        published = _parse_datetime(str(row["published_at"] or ""))
        url = str(row["original_url"] or "")
        if published is None or published < cutoff or published > as_of.astimezone(timezone.utc):
            continue
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        age_hours = (as_of.astimezone(timezone.utc) - published).total_seconds() / 3600
        source = NEWS_SOURCE_BY_KEY.get(str(row["source_key"]), {})
        output.append(
            {
                "source_key": row["source_key"],
                "source_name": row["source_name"],
                "title": row["original_title"],
                "published_at": published.isoformat(),
                "fetched_at": row["fetched_at"],
                "age_hours": round(age_hours, 2),
                "freshness_bucket": "FRESH_24H" if age_hours <= fresh_hours else "CONTEXT_48H",
                "human_verification_url": url,
                "summary": row["public_summary"],
                "market": row["market"],
                "language": row["language"],
                "epistemic_status": "REPORTED",
                "source_class": source.get("source_class", "REPORTED_MEDIA"),
                "coverage_tags": list(source.get("coverage_tags", ("GENERAL_FINANCE",))),
                "publisher_group": source.get("publisher_group", row["source_key"]),
            }
        )
        if len(output) >= limit:
            break
    return output


def load_x_input_status(output_root: str | Path, run_date: str) -> dict[str, Any]:
    root = Path(output_root)
    dated = root / run_date / "run_summary.json"
    if not dated.is_file():
        return {
            "status": "X_DEGRADED",
            "reason": "Same-day X summary is missing; stale X was not substituted.",
            "path": str(dated),
        }
    try:
        payload = json.loads(dated.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {
            "status": "X_DEGRADED",
            "reason": f"Same-day X summary could not be read: {type(error).__name__}",
            "path": str(dated),
        }
    return {
        "status": payload.get("status", "UNKNOWN"),
        "configured_accounts": payload.get("configured_accounts"),
        "complete_accounts": payload.get("complete_accounts"),
        "new_posts": payload.get("new_posts"),
        "kept_posts": payload.get("kept_posts"),
        "path": str(dated),
        "epistemic_status": "OPINION_INPUT_ONLY",
    }


def build_weekend_snapshot(
    *,
    as_of: datetime,
    label: str,
    news_results: list[dict[str, Any]],
    news_items: list[dict[str, Any]],
    x_status: dict[str, Any],
) -> dict[str, Any]:
    success_count = sum(row.get("status") == "SUCCESS" for row in news_results)
    required_results = [row for row in news_results if row.get("required", True)]
    required_success_count = sum(row.get("status") == "SUCCESS" for row in required_results)
    required_success = bool(required_results) and required_success_count == len(required_results)
    optional_failures = [
        row for row in news_results if not row.get("required", True) and row.get("status") != "SUCCESS"
    ]
    if required_success and news_items:
        status = "NEWS_CRAWL_PASS"
    elif success_count and news_items:
        status = "NEWS_CRAWL_DEGRADED"
    else:
        status = "NEWS_CRAWL_FAILED"

    source_counts = Counter(str(row["source_key"]) for row in news_items)
    source_class_counts = Counter(str(row.get("source_class") or "UNKNOWN") for row in news_items)
    coverage_counts = Counter(
        str(tag)
        for row in news_items
        for tag in row.get("coverage_tags") or ["GENERAL_FINANCE"]
    )
    source_coverage = []
    for result in news_results:
        source_coverage.append(
            {
                "source_key": result.get("source_key"),
                "source_name": result.get("source_name"),
                "status": result.get("status"),
                "required": result.get("required", True),
                "source_class": result.get("source_class", "REPORTED_MEDIA"),
                "coverage_tags": result.get("coverage_tags") or ["GENERAL_FINANCE"],
                "fetched_item_count": result.get("valid_item_count", 0),
                "recent_48h_item_count": source_counts.get(str(result.get("source_key")), 0),
                "endpoint_url": result.get("endpoint_url"),
            }
        )
    return {
        "artifact": "BEN_WEEKEND_24H_48H_SOURCE_SNAPSHOT",
        "schema_version": "1.0",
        "status": status,
        "label": label,
        "snapshot_date": as_of.astimezone(TAIPEI).date().isoformat(),
        "generated_at": as_of.astimezone(TAIPEI).isoformat(),
        "fresh_event_window_hours": 24,
        "context_window_hours": 48,
        "is_post_close_manuscript": False,
        "market_session_status": "NO_SAME_DAY_TW_SESSION_EXPECTED_ON_SUNDAY",
        "purpose": "Collect weekend event evidence for Monday topic selection; do not present it as a Taiwan post-close manuscript.",
        "news_source_success_count": success_count,
        "news_source_count": len(news_results),
        "required_source_success_count": required_success_count,
        "required_source_count": len(required_results),
        "optional_source_failure_count": len(optional_failures),
        "news_results": news_results,
        "fresh_24h_count": sum(row["freshness_bucket"] == "FRESH_24H" for row in news_items),
        "context_24h_to_48h_count": sum(row["freshness_bucket"] == "CONTEXT_48H" for row in news_items),
        "source_concentration": dict(sorted(source_counts.items())),
        "source_class_counts": dict(sorted(source_class_counts.items())),
        "coverage_tag_counts": dict(sorted(coverage_counts.items())),
        "source_coverage": source_coverage,
        "structured_data_gaps": {
            "ETF_NET_FLOWS": "UNAVAILABLE",
            "ONCHAIN_ADDRESS_METRICS": "UNAVAILABLE",
            "OPTIONS_CHAIN_IV_OI": "UNAVAILABLE",
            "DARK_POOL_PRINTS": "UNAVAILABLE",
            "DXY_FX_TICKS": "UNAVAILABLE",
            "COMMODITY_INVENTORIES": "PARTIAL_NEWS_ONLY",
        },
        "x_input": x_status,
        "items": news_items,
        "boundaries": [
            "News is a reported-event lead, not an automatic finance fact.",
            "X remains OPINION and is not upgraded to fact.",
            "No Saturday crawl, no social posting, and no Sunday post-close manuscript.",
            "Optional specialist or official feeds may degrade without blocking the nine-source base crawl.",
        ],
    }
